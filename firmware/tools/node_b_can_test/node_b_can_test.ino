// ============================================================
//  Node B — CAN send test sketch
//  Uses ESP32 built-in TWAI driver — NO external library needed
//
//  Sends a fixed test message every 500ms to verify CAN bus
//  hardware is working before full protocol integration.
//
//  Hardware:
//    MCP2551 CTX → ESP32 GPIO 21
//    MCP2551 CRX → ESP32 GPIO 22
//    MCP2551 UCC → 3.3V
//    MCP2551 GND → GND
//    CANH / CANL → leave unconnected until Day 4
// ============================================================

#include "driver/twai.h"

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("Node B — CAN send test starting...");

  // ── TWAI driver config ────────────────────────────────────
  twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(
    (gpio_num_t)21,   // TX pin (CTX on MCP2551)
    (gpio_num_t)22,   // RX pin (CRX on MCP2551)
    TWAI_MODE_NORMAL
  );
  twai_timing_config_t t_config = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  // ── Install and start driver ──────────────────────────────
  if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
    Serial.println("ERROR: TWAI driver install failed");
    while (true);
  }
  if (twai_start() != ESP_OK) {
    Serial.println("ERROR: TWAI start failed");
    while (true);
  }

  Serial.println("CAN init OK. Sending test message every 500ms...");
  Serial.println("Message ID: 0x001, Payload: 0xDEADBEEF");
  Serial.println("---");
}

void loop() {
  // ── Build test message ────────────────────────────────────
  twai_message_t msg;
  msg.identifier      = 0x001;
  msg.flags           = TWAI_MSG_FLAG_NONE;
  msg.data_length_code = 4;
  msg.data[0]         = 0xDE;
  msg.data[1]         = 0xAD;
  msg.data[2]         = 0xBE;
  msg.data[3]         = 0xEF;

  // ── Send ──────────────────────────────────────────────────
  esp_err_t result = twai_transmit(&msg, pdMS_TO_TICKS(100));

  if (result == ESP_OK) {
    Serial.print(millis());
    Serial.println("ms — sent: ID=0x001  payload=0xDEADBEEF");
  } else if (result == ESP_ERR_TIMEOUT) {
    // Expected when CANH/CANL are unconnected — bus has no receiver
    Serial.print(millis());
    Serial.println("ms — timeout (normal if CANH/CANL unconnected)");
  } else {
    Serial.print(millis());
    Serial.print("ms — ERROR: ");
    Serial.println(result);
  }

  delay(500);
}
