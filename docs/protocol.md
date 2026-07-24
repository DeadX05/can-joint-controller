# CAN Bus Protocol Specification

**Project:** Distributed Joint Controller over CAN
**Bus baud rate:** 250 kbit/s
**Termination:** ~110 Ω per node (2 × 220 Ω in parallel), ~55 Ω across the bus
**Frame format:** Standard 11-bit CAN ID, data frame

> The original Day-1 design used 4-byte IEEE-754 floats. The implementation
> switched to **int16 fixed-point in units of 0.1°** — half the payload,
> no endianness/float portability concerns, and ample resolution for a
> position loop. This document describes the protocol as implemented.

---

## Message Table

| ID    | Name         | Direction          | Length  | Rate            |
|-------|--------------|--------------------|---------|-----------------|
| 0x100 | position_cmd | Supervisor → Joint | 2 bytes | on command      |
| 0x110 | joint_status | Joint → Supervisor | 8 bytes | 10 Hz           |

All multi-byte fields are **little-endian**, signed unless noted.

---

## 0x100 — position_cmd

Sent by Node B (supervisor) to Node A (joint controller) when a target is
entered. Commands the PID setpoint.

```
Byte 0-1:  int16  target_deg_x10   (degrees × 10; 900 = 90.0°)
```

Clamped to the joint's −45°…180° range **at the receiver**.

**Example:** command 90.0° → `900` → bytes `84 03`.

---

## 0x110 — joint_status

Sent by Node A to Node B at 10 Hz. Carries everything the supervisor needs
to display, log, and detect settling.

```
Byte 0-1:  int16   position_deg_x10   (degrees × 10)
Byte 2-3:  int16   target_deg_x10     (degrees × 10)
Byte 4-5:  int16   error_deg_x10      (degrees × 10)
Byte 6:    uint8   effort             (abs PWM duty, 0-255)
Byte 7:    uint8   flags              (bit0 = settled, within deadband)
```

**Example:** position 87.3°, target 90.0°, error 2.7°, PWM 40, not settled
→ `69 03  84 03  1B 00  28  00`.

---

## Encoding / decoding (C)

```c
// Pack a degree value into an int16 field (0.1° units)
int16_t v = (int16_t)(deg * 10);
data[0] = v & 0xFF;
data[1] = v >> 8;

// Unpack
int16_t v = (int16_t)(data[0] | (data[1] << 8));
float deg = v / 10.0f;
```

---

## Node IDs / roles

| Node   | Role       | Sends | Receives |
|--------|------------|-------|----------|
| Node A | Joint ctrl | 0x110 | 0x100    |
| Node B | Supervisor | 0x100 | 0x110    |

---

## Error / debug notes

- No frames received: check shared GND between nodes, matching 250 kbit/s
  bitrate, and that termination is present at both nodes.
- CANH/CANL must not be swapped.
- The MCP2551 is run at **5 V** (it is spec'd for 4.5–5.5 V); each ESP32 RX
  line uses a 220 Ω / 440 Ω divider to bring the 5 V RXD down to ~3.3 V.
  See `hardware.md` and `engineering-log.md` for why.

---

## Future extension (planned, not implemented)

Scaling to a multi-DOF leg would add per-joint IDs, e.g. `0x101`/`0x111`
for a second joint and `0x120` for a foot IMU. Multi-node bus arbitration
is untested — see the README's known limitations.
