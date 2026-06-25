// ============================================================
//  Node A — Day 1 starter: spin test + encoder ISR + Kp-only PID
//  Hardware:
//    TB6612  AIN1  → GPIO 25
//            AIN2  → GPIO 26
//            PWMA  → GPIO 27  (must be PWM-capable)
//            STBY  → GPIO 14  (pulled HIGH in setup)
//            VM    → 7.4V motor rail
//            VCC   → 3.3V logic rail
//            GND   → common GND
//
//    Encoder ChA   → GPIO 18  (interrupt-capable)
//            ChB   → GPIO 19  (interrupt-capable)
//            Vcc   → 3.3V  (or via level shifter if 5V encoder)
//            GND   → common GND
//
//  Change CPR to match your encoder's counts-per-rev (before gearbox × gear ratio).
//  Common N20 values after gearbox: 7×ratio, 11×ratio, 16×ratio.
//  Check your datasheet — print the count at a known rotation to verify.
// ============================================================

// ── Pin definitions ─────────────────────────────────────────
#define PIN_AIN1  25
#define PIN_AIN2  26
#define PIN_PWMA  27
#define PIN_STBY  14
#define PIN_ENC_A 18
#define PIN_ENC_B 19

// ── Encoder config ──────────────────────────────────────────
// Set this to your encoder's total CPR *after* the gearbox.
// Example: 7 counts/rev motor × 100:1 gearbox = 700 CPR at output shaft.
const float CPR = 700.0;

volatile int32_t encoderTicks = 0;
volatile int      lastA = LOW;

void IRAM_ATTR encoderISR() {
  int a = digitalRead(PIN_ENC_A);
  int b = digitalRead(PIN_ENC_B);
  // Standard quadrature decode: rising/falling A, read B for direction
  if (a != lastA) {
    if (a == HIGH) {
      encoderTicks += (b == LOW) ? 1 : -1;
    } else {
      encoderTicks += (b == HIGH) ? 1 : -1;
    }
    lastA = a;
  }
}

float getPositionDeg() {
  // noInterrupts/interrupts bracket to safely copy volatile int32
  noInterrupts();
  int32_t ticks = encoderTicks;
  interrupts();
  return (ticks / CPR) * 360.0;
}

// ── Motor control ────────────────────────────────────────────
// output: -255 (full reverse) to +255 (full forward)
void setMotor(int output) {
  output = constrain(output, -255, 255);
  if (output > 0) {
    digitalWrite(PIN_AIN1, HIGH);
    digitalWrite(PIN_AIN2, LOW);
    analogWrite(PIN_PWMA, output);
  } else if (output < 0) {
    digitalWrite(PIN_AIN1, LOW);
    digitalWrite(PIN_AIN2, HIGH);
    analogWrite(PIN_PWMA, -output);
  } else {
    // Coast (both LOW = free spin; both HIGH = brake)
    digitalWrite(PIN_AIN1, LOW);
    digitalWrite(PIN_AIN2, LOW);
    analogWrite(PIN_PWMA, 0);
  }
}

// ── PID state ────────────────────────────────────────────────
float setpointDeg  = 0.0;
float Kp           = 2.0;   // Start here — tune upward until oscillation, then halve
float Ki           = 0.0;   // Leave at 0 until Kp and Kd are settled
float Kd           = 0.0;   // Add after Kp is tuned: start ~0.05
float integral     = 0.0;
float prevError    = 0.0;
const float INTEGRAL_CLAMP = 80.0;  // prevents windup — tune alongside Ki

unsigned long lastPIDTime = 0;

void runPID() {
  unsigned long now = millis();
  float dt = (now - lastPIDTime) / 1000.0;
  if (dt < 0.005) return;  // run at ~200Hz max
  lastPIDTime = now;

  float position = getPositionDeg();
  float error    = setpointDeg - position;

  // Integral with windup clamp
  integral += Ki * error * dt;
  integral  = constrain(integral, -INTEGRAL_CLAMP, INTEGRAL_CLAMP);

  // Derivative
  float derivative = (error - prevError) / dt;
  prevError = error;

  float output = (Kp * error) + integral + (Kd * derivative);
  setMotor((int)output);
}

// ── Serial setpoint parser ───────────────────────────────────
// Type a number in Serial Monitor and press Enter to command that angle.
// Example: "90" → move to 90°, "0" → return to 0°, "-45" → go to -45°
void checkSerial() {
  if (Serial.available()) {
    String s = Serial.readStringUntil('\n');
    s.trim();
    if (s.length() > 0) {
      setpointDeg = s.toFloat();
      integral    = 0.0;   // reset integral on new setpoint
      prevError   = 0.0;
      Serial.print(">> New setpoint: ");
      Serial.println(setpointDeg);
    }
  }
}

// ── Setup ────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("Node A — Day 1 startup");

  // Motor driver pins
  pinMode(PIN_AIN1, OUTPUT);
  pinMode(PIN_AIN2, OUTPUT);
  pinMode(PIN_PWMA, OUTPUT);
  pinMode(PIN_STBY, OUTPUT);
  digitalWrite(PIN_STBY, HIGH);  // MUST be HIGH — motor is dead if this is LOW

  // Encoder pins with pull-up (N20 Hall encoders are open-collector)
  pinMode(PIN_ENC_A, INPUT_PULLUP);
  pinMode(PIN_ENC_B, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_A), encoderISR, CHANGE);
  attachInterrupt(digitalPinToInterrupt(PIN_ENC_B), encoderISR, CHANGE);

  lastA       = digitalRead(PIN_ENC_A);
  lastPIDTime = millis();

  // ── Spin test (runs once at startup) ──────────────────────
  // Confirms: motor spins both ways, encoder counts respond correctly.
  // Watch Serial Monitor during this phase.
  Serial.println("Spin test: forward...");
  setMotor(150);
  delay(1500);
  Serial.print("  Encoder after forward spin: ");
  Serial.print(getPositionDeg(), 1);
  Serial.println(" deg  (should be positive if wired correctly)");

  Serial.println("Spin test: stop...");
  setMotor(0);
  delay(500);

  Serial.println("Spin test: reverse...");
  setMotor(-150);
  delay(1500);
  Serial.print("  Encoder after reverse spin: ");
  Serial.print(getPositionDeg(), 1);
  Serial.println(" deg  (should be less than after forward)");

  setMotor(0);
  delay(500);

  // If encoder counts are backward (reverse reads positive), either:
  //   (a) swap ENC_A and ENC_B pin definitions above, or
  //   (b) swap AO1/AO2 motor wires physically
  // Pick (a) — it's easier.

  Serial.println("\nSpin test done. PID active. Type a setpoint angle and press Enter.");
  Serial.println("Format: t_ms, setpoint_deg, actual_deg  (CSV — save this for Day 2 plots)");
  Serial.println("---");

  encoderTicks = 0;  // zero position after spin test
}

// ── Main loop ────────────────────────────────────────────────
unsigned long lastPrint = 0;

void loop() {
  checkSerial();
  runPID();

  // Print CSV log every 50ms — copy this into a .csv file for Day 2 plotting
  if (millis() - lastPrint >= 50) {
    lastPrint = millis();
    Serial.print(millis());
    Serial.print(",");
    Serial.print(setpointDeg, 2);
    Serial.print(",");
    Serial.println(getPositionDeg(), 2);
  }
}
