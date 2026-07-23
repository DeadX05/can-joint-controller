/*
 * Node B - CAN Bus Sender (TWAI) - Connected-Bus Version
 * ESP32 + MCP2551 CAN Transceiver
 *
 * Sends test message (ID 0x001, payload 0xDEADBEEF) every 500ms.
 * Prints TWAI status (state, TEC, REC) every 2s and auto-recovers
 * from bus-off so it can't latch into permanent "Send failed".
 *
 * Wiring (bus NOW CONNECTED):
 *   MCP2551 CTX  -> GPIO21
 *   MCP2551 CRX  -> GPIO22
 *   MCP2551 VCC  -> 3.3V   (known risk: spec'd for 5V)
 *   MCP2551 GND  -> shared GND
 *   CANH -> Node A CANH (direct)
 *   CANL -> Node A CANL (direct)
 *   GND  -> Node A GND  (shared reference)
 *   Termination: 2x220R parallel (~110R) CANH-to-CANL on THIS node
 *
 * Expected behavior with bus connected and Node A powered:
 *   - Every send should print "sent OK"
 *   - A timeout/fail now means a REAL problem (wiring, transceiver,
 *     or Node A not running) - it is no longer "normal"
 */

#include "driver/twai.h"

#define CAN_TX_PIN GPIO_NUM_21
#define CAN_RX_PIN GPIO_NUM_22

const unsigned long SEND_INTERVAL_MS = 500;
const unsigned long STATUS_INTERVAL_MS = 2000;

unsigned long lastSend = 0;
unsigned long lastStatusPrint = 0;
unsigned long sendOkCount = 0;
unsigned long sendFailCount = 0;

void printTwaiStatus() {
  twai_status_info_t status;
  if (twai_get_status_info(&status) == ESP_OK) {
    const char* stateStr;
    switch (status.state) {
      case TWAI_STATE_STOPPED:    stateStr = "STOPPED";    break;
      case TWAI_STATE_RUNNING:    stateStr = "RUNNING";    break;
      case TWAI_STATE_BUS_OFF:    stateStr = "BUS_OFF";    break;
      case TWAI_STATE_RECOVERING: stateStr = "RECOVERING"; break;
      default:                    stateStr = "UNKNOWN";    break;
    }
    Serial.printf("[STATUS] state=%s  TEC=%lu  REC=%lu  tx_failed=%lu  bus_err=%lu  |  ok=%lu fail=%lu\n",
                  stateStr,
                  (unsigned long)status.tx_error_counter,
                  (unsigned long)status.rx_error_counter,
                  (unsigned long)status.tx_failed_count,
                  (unsigned long)status.bus_error_count,
                  sendOkCount, sendFailCount);

    // Auto-recovery: TWAI does NOT self-recover from bus-off.
    // Without this, the node stays dead until a manual reset.
    if (status.state == TWAI_STATE_BUS_OFF) {
      Serial.println("[STATUS] Bus-off detected -> initiating recovery...");
      twai_initiate_recovery();
    } else if (status.state == TWAI_STATE_STOPPED) {
      // After recovery completes, driver lands in STOPPED - restart it
      Serial.println("[STATUS] Driver stopped -> restarting...");
      twai_start();
    }
  } else {
    Serial.println("[STATUS] Failed to read TWAI status");
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("Node B - CAN sender starting (connected-bus version)...");

  twai_general_config_t g_config =
      TWAI_GENERAL_CONFIG_DEFAULT(CAN_TX_PIN, CAN_RX_PIN, TWAI_MODE_NORMAL);
  twai_timing_config_t t_config = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
    Serial.println("ERROR: TWAI driver install failed");
    while (true) delay(1000);
  }
  if (twai_start() != ESP_OK) {
    Serial.println("ERROR: TWAI start failed");
    while (true) delay(1000);
  }

  Serial.println("CAN init OK. Sending ID=0x001 payload=0xDEADBEEF every 500ms");
  Serial.println("---");
}

void loop() {
  unsigned long now = millis();

  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;

    twai_message_t msg;
    msg.identifier = 0x001;
    msg.flags = TWAI_MSG_FLAG_NONE;
    msg.data_length_code = 4;
    msg.data[0] = 0xDE;
    msg.data[1] = 0xAD;
    msg.data[2] = 0xBE;
    msg.data[3] = 0xEF;

    esp_err_t result = twai_transmit(&msg, pdMS_TO_TICKS(100));

    if (result == ESP_OK) {
      sendOkCount++;
      Serial.printf("%lums - sent OK: ID=0x001 payload=0xDEADBEEF\n", now);
    } else if (result == ESP_ERR_TIMEOUT) {
      sendFailCount++;
      Serial.printf("%lums - SEND TIMEOUT (bus is connected, so this is a real fault)\n", now);
    } else if (result == ESP_ERR_INVALID_STATE) {
      sendFailCount++;
      Serial.printf("%lums - SEND FAILED: driver not running (bus-off/stopped - recovery will kick in)\n", now);
    } else {
      sendFailCount++;
      Serial.printf("%lums - SEND FAILED: esp_err=%d\n", now, (int)result);
    }
  }

  if (now - lastStatusPrint >= STATUS_INTERVAL_MS) {
    printTwaiStatus();
    lastStatusPrint = now;
  }
}
