/*
 * Node A - basic CAN receive bring-up
 *
 * Minimal counterpart to node_b_can_test.ino: listens on the bus and
 * prints any frame received. No diagnostics - that came later, once it
 * became clear the bus was failing silently and there was nothing to
 * look at.
 *
 * ESP32 TWAI, 250 kbit/s, CTX=GPIO21, CRX=GPIO22.
 *
 * NOTE: reconstructed from session notes; the original sketch was lost
 * (a single Arduino sketch file was reused and overwritten during
 * bring-up). Behaviour matches what was recorded at the time.
 */

#include "driver/twai.h"

void setup() {
  Serial.begin(115200);
  delay(500);

  twai_general_config_t g =
      TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_21, GPIO_NUM_22, TWAI_MODE_NORMAL);
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g, &t, &f) != ESP_OK) {
    Serial.println("ERROR: TWAI driver install failed");
    while (true) delay(1000);
  }
  if (twai_start() != ESP_OK) {
    Serial.println("ERROR: TWAI start failed");
    while (true) delay(1000);
  }

  Serial.println("Node A Ready - listening for CAN messages...");
}

void loop() {
  twai_message_t msg;

  if (twai_receive(&msg, pdMS_TO_TICKS(1000)) == ESP_OK) {
    Serial.printf("Received  ID: 0x%03X  DLC: %d  Data: ",
                  msg.identifier, msg.data_length_code);
    for (int i = 0; i < msg.data_length_code; i++) {
      Serial.printf("%02X ", msg.data[i]);
    }
    Serial.println();
  } else {
    Serial.println("No message received (timeout)");
  }
}
