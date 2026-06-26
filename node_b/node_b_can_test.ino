// ============================================================
//  Node B — CAN send test sketch
//  Sends a fixed test message every 500ms to verify CAN bus
//  hardware is working before full protocol integration.
//
//  Hardware:
//    MCP2551 CTX → ESP32 GPIO 21
//    MCP2551 CRX → ESP32 GPIO 22
//    MCP2551 UCC → 3.3V
//    MCP2551 GND → GND
//    CANH / CANL → leave unconnected until Day 3
//
//  Library needed:
//    Arduino IDE → Tools → Manage Libraries → search "ESP32 CAN"
//    Install: "ESP32 CAN" by Thomas Barth
// ============================================================

#include <ESP32CAN.h>
#include <CAN_config.h>

CAN_device_t CAN_cfg;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("Node B — CAN send test starting...");

  // ── CAN bus config ────────────────────────────────────────
  CAN_cfg.speed     = CAN_SPEED_250KBPS;  // must match Node A
  CAN_cfg.tx_pin_id = GPIO_NUM_21;         // CTX
  CAN_cfg.rx_pin_id = GPIO_NUM_22;         // CRX
  CAN_cfg.rx_queue  = xQueueCreate(10, sizeof(CAN_frame_t));

  if (ESP32Can.CANInit() != ESP_OK) {
    Serial.println("ERROR: CAN init failed — check wiring");
    while (true) delay(1000);  // halt
  }

  Serial.println("CAN init OK. Sending test message every 500ms...");
  Serial.println("Message ID: 0x001, Payload: 0xDEADBEEF");
  Serial.println("---");
}

void loop() {
  // ── Build test CAN frame ──────────────────────────────────
  CAN_frame_t frame;
  frame.FIR.B.FF  = CAN_frame_std;  // standard 11-bit ID
  frame.MsgID     = 0x001;
  frame.FIR.B.DLC = 4;              // 4 bytes payload

  // Payload: 0xDEADBEEF
  frame.data.u8[0] = 0xDE;
  frame.data.u8[1] = 0xAD;
  frame.data.u8[2] = 0xBE;
  frame.data.u8[3] = 0xEF;

  // ── Send ─────────────────────────────────────────────────
  if (ESP32Can.CANWriteFrame(&frame) == ESP_OK) {
    Serial.print(millis());
    Serial.println("ms — sent: ID=0x001  payload=0xDEADBEEF");
  } else {
    Serial.print(millis());
    Serial.println("ms — ERROR: send failed");
  }

  delay(500);
}
