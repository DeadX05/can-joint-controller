/*
 * Node B - Supervisor
 *
 * Issues 0x100 position commands onto the bus and consumes the joint
 * controller's 0x110 status stream.
 *
 * Serial commands (115200 baud, Newline line ending):
 *   <number>  target angle in degrees, clamped to -45..180
 */

#include "driver/twai.h"

#define ID_CMD_POS 0x100
#define ID_STATUS  0x110

void setup() {
  Serial.begin(115200);
  delay(500);

  twai_general_config_t g =
      TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_21, GPIO_NUM_22, TWAI_MODE_NORMAL);
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();
  twai_driver_install(&g, &t, &f);
  twai_start();

  Serial.println("Supervisor. Commands: angle (-45..180)");
}

void loop() {
  if (Serial.available()) {
    float cmd = constrain(Serial.parseFloat(), -45.0, 180.0);
    while (Serial.available()) Serial.read();
    int16_t raw = (int16_t)(cmd * 10);
    twai_message_t m = {};
    m.identifier = ID_CMD_POS;
    m.data_length_code = 2;
    m.data[0] = raw & 0xFF;
    m.data[1] = raw >> 8;
    if (twai_transmit(&m, pdMS_TO_TICKS(100)) == ESP_OK)
      Serial.printf("# command sent: %.1f\n", cmd);
    else
      Serial.println("# SEND FAILED");
  }

  static unsigned long lastPrint = 0;
  twai_message_t rx;
  while (twai_receive(&rx, 0) == ESP_OK) {
    if (rx.identifier != ID_STATUS || rx.data_length_code != 8) continue;

    int16_t pos = rx.data[0] | (rx.data[1] << 8);
    int16_t tgt = rx.data[2] | (rx.data[3] << 8);
    int16_t err = rx.data[4] | (rx.data[5] << 8);

    if (millis() - lastPrint > 500) {
      lastPrint = millis();
      Serial.printf("STATUS: pos=%.1f  target=%.1f  err=%.1f  pwm=%u  %s\n",
                    pos/10.0, tgt/10.0, err/10.0, rx.data[6],
                    rx.data[7] & 1 ? "[SETTLED]" : "");
    }
  }
}
