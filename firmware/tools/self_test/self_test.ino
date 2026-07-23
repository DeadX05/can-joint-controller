/*
 * TWAI physical-layer self-test
 *
 * Node-agnostic diagnostic. Flash to either node and power that node
 * ALONE (other node's USB unplugged; bus wires may stay connected).
 *
 * Uses TWAI_MODE_NO_ACK with self-reception requested, so the node
 * transmits through its own transceiver and the real bus wiring and
 * receives its own frame back - no partner node required. This gives a
 * per-node pass/fail for the entire physical loop:
 *   ESP32 TX -> transceiver TXD -> CANH/CANL -> transceiver RXD -> ESP32 RX
 *
 * PHYSICAL LOOP OK  -> that node's MCU, firmware, transceiver, divider
 *                      and termination are all functional.
 * RX: NOTHING       -> fault is on THIS node. Next step is the GPIO
 *                      loopback test (jumper GPIO21 straight to GPIO22,
 *                      transceiver bypassed) to separate MCU/firmware
 *                      from the analogue front end.
 */

#include "driver/twai.h"

void setup() {
  Serial.begin(115200);
  delay(500);

  twai_general_config_t g =
      TWAI_GENERAL_CONFIG_DEFAULT(GPIO_NUM_21, GPIO_NUM_22, TWAI_MODE_NO_ACK);
  twai_timing_config_t t = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  twai_driver_install(&g, &t, &f);
  twai_start();

  Serial.println("SELF-TEST: sending to myself every 500ms...");
}

void loop() {
  twai_message_t tx = {};
  tx.identifier = 0x055;
  tx.self = 1;                 // self-reception request
  tx.data_length_code = 2;
  tx.data[0] = 0xAA;
  tx.data[1] = 0x55;

  esp_err_t r = twai_transmit(&tx, pdMS_TO_TICKS(100));
  Serial.printf("TX: %s | ", r == ESP_OK ? "ok" : "FAIL");

  twai_message_t rx;
  if (twai_receive(&rx, pdMS_TO_TICKS(200)) == ESP_OK) {
    Serial.printf("RX: got own frame ID=0x%03X %02X %02X  <- PHYSICAL LOOP OK\n",
                  rx.identifier, rx.data[0], rx.data[1]);
  } else {
    Serial.println("RX: NOTHING <- physical loop broken on THIS node");
  }

  delay(500);
}
