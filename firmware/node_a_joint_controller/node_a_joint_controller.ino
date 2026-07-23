/*
 * Node A - Joint controller
 *
 * Receives 0x100 position commands over CAN, runs a closed-loop PID
 * position controller against the quadrature encoder, drives the motor
 * through a TB6612 H-bridge, and publishes 0x110 status at 10 Hz.
 *
 * Bus: ESP32 TWAI, 250 kbit/s, CTX=GPIO21, CRX=GPIO22 (via RX divider).
 */

#include "driver/twai.h"

// ---- CAN ----
#define CAN_TX_PIN GPIO_NUM_21
#define CAN_RX_PIN GPIO_NUM_22
#define ID_CMD_POS   0x100
#define ID_STATUS    0x110

// ---- Motor / encoder (validated pins - DO NOT CHANGE) ----
#define AIN1 26
#define AIN2 27
#define PWMA 25
#define STBY 14
#define ENC_A 32
#define ENC_B 33

// Hand-calibrated, replacing the nominal datasheet figure.
const float COUNTS_PER_REV = 1146.0;
const float DEG_PER_COUNT  = 360.0 / COUNTS_PER_REV;

// ---- PID (empirically tuned) ----
const float Kp = 10.0, Ki = 0.1, Kd = 0.1;
const int   STICTION_PWM = 35;      // min duty that breaks static friction
const float DEADBAND_DEG = 0.6;     // prevents limit-cycling at setpoint
const float I_CLAMP      = 50.0;    // anti-windup against static friction
const float ANGLE_MIN = -45.0, ANGLE_MAX = 180.0;

volatile long encoderCount = 0;
float targetDeg = 0.0;
float integral = 0.0, lastErr = 0.0;
unsigned long lastPid = 0, lastStatus = 0;
int lastPwm = 0;

void IRAM_ATTR encoderISR() {
  if (digitalRead(ENC_B)) encoderCount--; else encoderCount++;
}

/*
 * Motor drive direction is inverted relative to the naive convention.
 * With the un-swapped logic, drive direction and encoder counting
 * direction disagree: every correction grows the error, PWM saturates
 * at 255 and the joint runs away. AIN1/AIN2 are swapped here to match
 * the encoder's counting sense.
 */
void setMotor(int pwm) {
  pwm = constrain(pwm, -255, 255);
  lastPwm = pwm;
  if (pwm > 0)      { digitalWrite(AIN1, HIGH); digitalWrite(AIN2, LOW);  }
  else if (pwm < 0) { digitalWrite(AIN1, LOW);  digitalWrite(AIN2, HIGH); }
  else              { digitalWrite(AIN1, LOW);  digitalWrite(AIN2, LOW);  }
  ledcWrite(PWMA, abs(pwm));
}

float currentDeg() { return encoderCount * DEG_PER_COUNT; }

void sendStatus() {
  twai_message_t m = {};
  m.identifier = ID_STATUS;
  m.data_length_code = 8;
  int16_t pos = (int16_t)(currentDeg() * 10);
  int16_t tgt = (int16_t)(targetDeg * 10);
  int16_t err = (int16_t)((targetDeg - currentDeg()) * 10);
  m.data[0] = pos & 0xFF; m.data[1] = pos >> 8;
  m.data[2] = tgt & 0xFF; m.data[3] = tgt >> 8;
  m.data[4] = err & 0xFF; m.data[5] = err >> 8;
  m.data[6] = (uint8_t)min(abs(lastPwm), 255);
  m.data[7] = (fabs(targetDeg - currentDeg()) <= DEADBAND_DEG) ? 1 : 0;
  twai_transmit(&m, 0);
}

void setup() {
  Serial.begin(115200);
  pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT); pinMode(STBY, OUTPUT);
  pinMode(ENC_A, INPUT_PULLUP); pinMode(ENC_B, INPUT_PULLUP);
  digitalWrite(STBY, HIGH);
  ledcAttach(PWMA, 20000, 8);   // ESP32 core 3.x API
  attachInterrupt(digitalPinToInterrupt(ENC_A), encoderISR, RISING);

  twai_general_config_t g =
      TWAI_GENERAL_CONFIG_DEFAULT(CAN_TX_PIN, CAN_RX_PIN, TWAI_MODE_NORMAL);
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  twai_driver_install(&g, &t, &f);
  twai_start();

  targetDeg = currentDeg();   // hold position on boot, no jump
  Serial.println("Node A: joint controller ready");
}

void loop() {
  twai_message_t rx;
  while (twai_receive(&rx, 0) == ESP_OK) {
    if (rx.identifier == ID_CMD_POS && rx.data_length_code >= 2) {
      int16_t raw = (int16_t)(rx.data[0] | (rx.data[1] << 8));
      targetDeg = constrain(raw / 10.0, ANGLE_MIN, ANGLE_MAX);
      Serial.printf("CMD: %.1f deg\n", targetDeg);
    }
  }

  unsigned long now = millis();

  // --- PID @ 100 Hz ---
  if (now - lastPid >= 10) {
    float dt = (now - lastPid) / 1000.0;
    lastPid = now;

    float err = targetDeg - currentDeg();
    int pwm = 0;

    if (fabs(err) > DEADBAND_DEG) {
      integral = constrain(integral + err * dt, -I_CLAMP, I_CLAMP);
      float deriv = (err - lastErr) / dt;
      pwm = (int)(Kp * err + Ki * integral + Kd * deriv);
      // friction compensation: below breakaway duty the motor does not
      // move at all, so the integral would wind up fighting stiction
      if (pwm > 0 && pwm <  STICTION_PWM) pwm =  STICTION_PWM;
      if (pwm < 0 && pwm > -STICTION_PWM) pwm = -STICTION_PWM;
    } else {
      integral = 0;
    }
    lastErr = err;
    setMotor(pwm);
  }

  // --- status @ 10 Hz ---
  if (now - lastStatus >= 100) { lastStatus = now; sendStatus(); }
}
