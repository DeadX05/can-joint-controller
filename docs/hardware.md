# Hardware

Two-node CAN system: **Node A** (joint controller) and **Node B**
(supervisor), each an ESP32 paired with an MCP2551 CAN transceiver on a
shared 250 kbit/s bus driven by the ESP32 TWAI peripheral.

> This document reflects the **bring-up configuration** — the wiring as it
> stood while the bus was first brought online and debugged.

## CAN bus / physical layer

| Signal | Connection |
|---|---|
| MCP2551 CTX (TXD) | ESP32 GPIO21 |
| MCP2551 CRX (RXD) | ESP32 GPIO22 — direct, no divider at this stage |
| MCP2551 VCC | 3.3 V |
| MCP2551 GND | common ground |
| Bitrate | 250 kbit/s (ESP32 TWAI) |

A level shifter on the RXD line was tried and dropped — the modules on
hand tested defective — so CRX is wired straight to GPIO22.

**Known risk (flagged at bring-up):** the MCP2551 is specified for a
4.5 V minimum supply. Running the transceivers at 3.3 V is out of spec;
undervolting this part is associated with silent frame loss — frames
appear to transmit but never arrive intact. Recorded here as a suspected
fault source, not a validated design choice.

### Bus topology & termination
- CANH ↔ CANH, CANL ↔ CANL, GND ↔ GND between nodes.
- Termination: 2 × 220 Ω in parallel at each node (~110 Ω per node),
  giving **~55 Ω measured across the bus**.

## Node A — motor & encoder

### TB6612 H-bridge
| Signal | Pin |
|---|---|
| AIN1 | GPIO26 |
| AIN2 | GPIO27 |
| PWMA | GPIO25 |
| STBY | GPIO14 (driven HIGH — motor is disabled if LOW) |
| VCC (logic) | 3.3 V |
| VM (motor) | battery + |
| GND | common ground (battery −) |

### Quadrature encoder
| Signal | Pin |
|---|---|
| Ch A | GPIO32 |
| Ch B | GPIO33 |
| Vcc | 3.3 V |
| GND | common ground |

**Counts per rev:** 700 (nominal — 7 PPR × 100:1 gearbox). Superseded by
hand calibration; see the engineering log. *Verify physically before
trusting the degree scale: command 90° and measure the lever with a
protractor.*

## Node B — supervisor

ESP32 + MCP2551 only, CAN wiring as above. No motor hardware — it issues
position-command frames, consumes status frames off the bus, and logs to
the PC over USB serial.

## Pin summary

| Node | Function | Pin |
|---|---|---|
| Both | CAN CTX / CRX | GPIO21 / GPIO22 |
| A | TB6612 AIN1 / AIN2 / PWMA | GPIO26 / GPIO27 / GPIO25 |
| A | TB6612 STBY | GPIO14 |
| A | Encoder Ch A / Ch B | GPIO32 / GPIO33 |
