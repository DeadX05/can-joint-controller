# CAN Bus Protocol Specification

**Project:** CAN-Bus Joint Controller  
**Bus baud rate:** 250 kbps  
**Termination:** 110Ω effective (2× 220Ω in parallel) at each physical end of the bus  
**Frame format:** Standard 11-bit CAN ID, data frame  

---

## Message Table

| ID    | Name             | Direction              | Length  | Payload format                          | Rate   |
|-------|------------------|------------------------|---------|-----------------------------------------|--------|
| 0x100 | position_cmd     | Supervisor → Joint     | 4 bytes | `float setpoint_deg`                    | 50 Hz  |
| 0x110 | joint_status     | Joint → Supervisor     | 8 bytes | `float actual_deg` + `float velocity_dps` | 50 Hz  |

---

## Payload Detail

### 0x100 — position_cmd

Sent by Node B (supervisor) to Node A (joint controller).  
Commands the PID setpoint in degrees.

```
Byte 0–3:  float  setpoint_deg   (IEEE 754, little-endian)
```

**Example:** Command 90.0° → bytes `00 00 B4 42`

---

### 0x110 — joint_status

Sent by Node A (joint controller) to Node B (supervisor).  
Reports current position and velocity for logging and plotting.

```
Byte 0–3:  float  actual_deg     (IEEE 754, little-endian)
Byte 4–7:  float  velocity_dps   (degrees per second, little-endian)
```

**Example:** Position 87.3°, velocity 12.5 dps → `9A 19 AE 42` + `00 00 48 41`

---

## Encoding / Decoding (C)

```c
// Pack float into 4 bytes for CAN payload
float value = 90.0f;
uint8_t payload[4];
memcpy(payload, &value, 4);

// Unpack 4 bytes from CAN payload into float
float received;
memcpy(&received, payload, 4);
```

---

## Node IDs / Roles

| Node   | Role        | Sends      | Receives   |
|--------|-------------|------------|------------|
| Node A | Joint ctrl  | 0x110      | 0x100      |
| Node B | Supervisor  | 0x100      | 0x110      |

---

## Error / Debug Notes

- If no messages received: check shared GND between nodes, baud rate match, termination resistors present
- CANH and CANL must not be swapped — double check MCP2551 pin 6 (CANL) and pin 7 (CANH)
- MCP2551 VDD must be 3.3V, not 5V, when used with ESP32

---

## Phase 2 Extension (planned)

When scaling to a 2-DOF leg, additional IDs will be added:

| ID    | Name           | Description                  |
|-------|----------------|------------------------------|
| 0x101 | position_cmd_2 | Command for second joint     |
| 0x111 | joint_status_2 | Status from second joint     |
| 0x120 | imu_data       | Foot IMU (accel XYZ)         |
