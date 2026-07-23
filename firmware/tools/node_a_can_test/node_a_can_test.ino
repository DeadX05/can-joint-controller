/*
 * Node A - CAN Bus Receiver (TWAI) - Bring-up / Diagnostic Version
 * ESP32 + MCP2551 CAN Transceiver
 *
 * Listens for CAN messages from Node B and prints them.
 * Also prints TWAI status (state, TEC, REC, error counts) every 2s
 * so bus-off / stopped states are visible instead of just silence,
 * and auto-recovers from bus-off if it ever latches.
 *
 * Wiring (confirmed working - do not change):
 *   MCP2551 CTX -> GPIO21
 *   MCP2551 CRX -> GPIO22
 *   Bitrate: 250 kbps
 *
 * NOTE: This is CAN bring-up only. Motor/encoder pins (TB6612, N20)
 * and the finalized PID controller (Kp=10, Ki=0.1, Kd=0.1) are not
 * wired into this sketch yet - protocol integration (0x100 position
 * cmd / 0x110 status) is a separate next step once the bus is
 * confirmed working both directions.
 */

#include "driver/twai.h"

#define CAN_TX_PIN GPIO_NUM_21
#define CAN_RX_PIN GPIO_NUM_22

unsigned long lastStatusPrint = 0;
const unsigned long STATUS_INTERVAL_MS = 2000;

unsigned long lastRxCheck = 0;
const unsigned long RX_TIMEOUT_MS = 1000;
bool receivedSinceLastCheck = false;

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
    Serial.printf("[STATUS] state=%s  TEC=%lu  REC=%lu  tx_failed=%lu  rx_missed=%lu  arb_lost=%lu  bus_err=%lu\n",
                  stateStr,
                  (unsigned long)status.tx_error_counter,
                  (unsigned long)status.rx_error_counter,
                  (unsigned long)status.tx_failed_count,
                  (unsigned long)status.rx_missed_count,
                  (unsigned long)status.arb_lost_count,
                  (unsigned long)status.bus_error_count);

    if (status.state == TWAI_STATE_BUS_OFF) {
      Serial.println("[STATUS] Bus-off detected -> initiating recovery...");
      twai_initiate_recovery();
    } else if (status.state == TWAI_STATE_STOPPED) {
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

  twai_general_config_t g_config =
      TWAI_GENERAL_CONFIG_DEFAULT(CAN_TX_PIN, CAN_RX_PIN, TWAI_MODE_NORMAL);
  twai_timing_config_t t_config = TWAI_TIMING_CONFIG_250KBITS();
  twai_filter_config_t f_config = TWAI_FILTER_CONFIG_ACCEPT_ALL();

  if (twai_driver_install(&g_config, &t_config, &f_config) != ESP_OK) {
    Serial.println("Failed to install TWAI driver");
    while (1) delay(1000);
  }

  if (twai_start() != ESP_OK) {
    Serial.println("Failed to start TWAI driver");
    while (1) delay(1000);
  }

  Serial.println("Node A Ready - listening for CAN messages...");
}

void loop() {
  twai_message_t message;

  // Short-timeout receive so status prints can interleave with listening
  if (twai_receive(&message, pdMS_TO_TICKS(100)) == ESP_OK) {
    receivedSinceLastCheck = true;
    Serial.printf("Received  ID: 0x%03X  DLC: %d  Data: ",
                  message.identifier, message.data_length_code);
    for (int i = 0; i < message.data_length_code; i++) {
      Serial.printf("%02X ", message.data[i]);
    }
    Serial.println();
  } else {
    if (millis() - lastRxCheck > RX_TIMEOUT_MS) {
      if (!receivedSinceLastCheck) {
        Serial.println("No message received (timeout)");
      }
      receivedSinceLastCheck = false;
      lastRxCheck = millis();
    }
  }

  if (millis() - lastStatusPrint > STATUS_INTERVAL_MS) {
    printTwaiStatus();
    lastStatusPrint = millis();
  }
}
