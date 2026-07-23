# Engineering Log — CAN Physical-Layer Fault Isolation

*Reconstructed after the fact from session notes and serial-monitor
captures taken during bring-up. The captures below are verbatim; some were
transcribed from screenshots, so ordering within a block is faithful but
interleaving between the two nodes' monitors is approximate.*

Rough timeline: Day 1 protocol design, Day 2 PID characterisation on the
bench (direct serial, no bus), Days 3–5 CAN physical-layer bring-up — which
is what took the time and is the subject of this log.

## Summary

The CAN bus refused to pass frames for days. The root cause turned out to
be **three of five MCP2551 modules, from one hand-soldered batch, being
defective** — compounded early on by an out-of-spec 3.3 V transceiver
supply and, once, a supply wire that came loose during rewiring. What made
this tractable was not any single insight but a **diagnostic ladder**: a
sequence of tests, each of which removes one class of suspect, so that a
confusing whole-system failure is decomposed into isolated yes/no
questions.

## 1. Making failure observable

The first problem was that a dead bus is *silent*, and silence is
ambiguous: a receiver printing nothing looks identical whether the sender
is transmitting into the void or the wire is shorted. So before chasing
the fault, both nodes were instrumented with `twai_get_status_info()` —
state, TEC (transmit error counter), REC, and the bus error count printed
every 2 s — plus **bus-off auto-recovery**, because the TWAI peripheral
latches `BUS_OFF` and does not self-recover; without
`twai_initiate_recovery()` a node simply stays dead after the first error
storm.

That immediately turned silence into signal. Node B (sender) drove its
transmit error counter to the bus-off threshold after only three frames:

```
[STATUS] state=BUS_OFF  TEC=128  REC=0  tx_failed=3  bus_err=88  |  ok=3 fail=16
[STATUS] Bus-off detected -> initiating recovery...
10011ms - SEND FAILED: driver not running (bus-off/stopped - recovery will kick in)
10511ms - SEND FAILED: driver not running (bus-off/stopped - recovery will kick in)
11011ms - SEND FAILED: driver not running (bus-off/stopped - recovery will kick in)
[STATUS] state=STOPPED  TEC=0  REC=0  tx_failed=3  bus_err=88  |  ok=3 fail=20
[STATUS] Driver stopped -> restarting...
12011ms - sent OK: ID=0x001 payload=0xDEADBEEF
12511ms - SEND FAILED: driver not running (bus-off/stopped - recovery will kick in)
```

Node A (receiver) at the same moment — every counter at zero, meaning it
was not merely missing frames, it was seeing *no bus activity at all*:

```
No message received (timeout)
[STATUS] state=RUNNING  TEC=0  REC=0  tx_failed=0  rx_missed=0  arb_lost=0  bus_err=0
No message received (timeout)
[STATUS] state=RUNNING  TEC=0  REC=0  tx_failed=0  rx_missed=0  arb_lost=0  bus_err=0
```

Reading the two together: the sender is putting frames on the wire and
reading back corruption; the receiver's side of the bus is electrically
dead.

## 2. Three distinct failure modes, told apart by the counters

The instrumentation paid off by making genuinely different faults
*distinguishable*, where on a bare bus they had all looked like "nothing
works."

**Zero errors, but nothing transmits** — after moving the transceivers to
5 V (see §4), a new signature appeared:

```
[STATUS] state=RUNNING  TEC=0  REC=0  tx_failed=0  bus_err=0  |  ok=6 fail=309
157009ms - SEND TIMEOUT (bus is connected, so this is a real fault)
157509ms - SEND TIMEOUT (bus is connected, so this is a real fault)
[STATUS] state=RUNNING  TEC=0  REC=0  tx_failed=0  bus_err=0  |  ok=6 fail=313
```

All error counters at zero *with* transmits timing out means the
controller never sees the bus go idle, so it never begins arbitration —
consistent with the RX line being held dominant. Traced to a transceiver
whose supply had come loose during rewiring (VCC reading 2.2 V,
back-fed through the input protection diodes rather than actually powered).

**Traffic crossing, but corrupted** — a third signature, with `bus_err`
climbing ~5,000 every 2 s (~2,500 corrupted frames/s) and TEC pinned at
the error-passive threshold:

```
[STATUS] state=RUNNING  TEC=128  REC=0  tx_failed=0  bus_err=291643  |  ok=6 fail=225
[STATUS] state=RUNNING  TEC=128  REC=0  tx_failed=0  bus_err=296694  |  ok=6 fail=229
[STATUS] state=RUNNING  TEC=128  REC=0  tx_failed=0  bus_err=301744  |  ok=6 fail=233
```

Node A now registering receive errors where before all counters were zero
— the first hard evidence of signals actually crossing the bus:

```
[STATUS] state=RUNNING  TEC=0  REC=131  tx_failed=0  rx_missed=0  arb_lost=0  bus_err=13
```

## 3. The decisive test — per-node self-test

The breakthrough was a diagnostic that needs no working partner:
`TWAI_MODE_NO_ACK` with self-reception requested, so a node transmits
through its *own* transceiver and the *real* bus wiring and receives its
own frame back. Flash it to one node, power that node alone, and you get a
pass/fail for that node's entire physical loop
(MCU → TXD → CANH/CANL → RXD → MCU).

Node B:

```
TX: ok | RX: got own frame ID=0x055 AA 55  <- PHYSICAL LOOP OK
TX: ok | RX: got own frame ID=0x055 AA 55  <- PHYSICAL LOOP OK
TX: ok | RX: got own frame ID=0x055 AA 55  <- PHYSICAL LOOP OK
```

Node A:

```
TX: FAIL | RX: NOTHING <- physical loop broken on THIS node
TX: FAIL | RX: NOTHING <- physical loop broken on THIS node
TX: FAIL | RX: NOTHING <- physical loop broken on THIS node
```

One test, run per node, localises the fault to **Node A** and exonerates
Node B, the bus wiring, and the shared termination in a single stroke.

## 4. Narrowing further — GPIO loopback, then cross-swap

Two more rungs, each removing a suspect:

**GPIO loopback** — jumper GPIO21 straight to GPIO22, transceiver bypassed
entirely:

```
TX: ok | RX: got own frame ID=0x055 AA 55  <- PHYSICAL LOOP OK
TX: ok | RX: got own frame ID=0x055 AA 55  <- PHYSICAL LOOP OK
```

Node A's ESP32, GPIOs, TWAI driver and firmware are all healthy — the
fault is confined to the transceiver and its immediate wiring.

**Cross-swap** — move Node B's known-good transceiver into Node A's
socket. It then passed self-test, identifying the **module itself** as the
failed part. Repeating across the batch found three of five modules dead —
a hand-soldering yield problem, not a design fault.

The 3.3 V → 5 V supply migration (with 220 Ω / 440 Ω RX dividers, see
`hardware.md`) removed the out-of-spec undervoltage that had been muddying
the picture in parallel.

## 5. Working bus

Node A receiving cleanly, all counters zero:

```
Received  ID: 0x001  DLC: 4  Data: DE AD BE EF
Received  ID: 0x001  DLC: 4  Data: DE AD BE EF
Received  ID: 0x001  DLC: 4  Data: DE AD BE EF
[STATUS] state=RUNNING  TEC=0  REC=0  tx_failed=0  rx_missed=0  arb_lost=0  bus_err=0
```

Node B — note `bus_err` frozen at its pre-fix total while TEC *decays* as
successful transmissions retire accumulated error credit, the protocol's
own error counter visibly healing:

```
[STATUS] state=RUNNING  TEC=86  REC=0  tx_failed=0  bus_err=17073  |  ok=131 fail=8
70009ms - sent OK: ID=0x001 payload=0xDEADBEEF
[STATUS] state=RUNNING  TEC=82  REC=0  tx_failed=0  bus_err=17073  |  ok=135 fail=8
[STATUS] state=RUNNING  TEC=78  REC=0  tx_failed=0  bus_err=17073  |  ok=139 fail=8
[STATUS] state=RUNNING  TEC=74  REC=0  tx_failed=0  bus_err=17073  |  ok=143 fail=8
```

## Supporting measurements

| Point | Reading | Note |
|---|---|---|
| CANH–CANL, bus assembled, unpowered | ~55 Ω | two ~110 Ω terminations in parallel — correct |
| CANH–GND / CANL–GND, unpowered | high kΩ / OL | no resistive leak to ground |
| Node A transceiver VCC after 5 V migration | 5.0 V | |
| Node B transceiver VCC after 5 V migration | 4.6 V | in spec (4.5 V min) but little headroom |
| RX divider midpoint, bus idle | ~2.7–3.0 V | above the ESP32 logic-high threshold |
| Failing transceiver CRX, bus idle | 0 V | should sit high (recessive) — the failure signature |
| Failing transceiver CANH / CANL under transmit | both ~1.8 V | no differential — transmitter not driving |

Termination resistors verified as 220 Ω 1 % (red-red-black-black-brown).
Earlier in-circuit readings of ~110 Ω and ~44 Ω were measurement artifacts
of probing resistors in parallel while still on the board.

## What made the method work

Each rung of the ladder answers exactly one question and removes one class
of suspect:

1. **Status telemetry** — is the bus dead, corrupted, or idle-starved?
   (Turns silence into a signature.)
2. **Self-test (`NO_ACK` + self-reception)** — is the fault on *this* node
   or elsewhere? (No working partner required.)
3. **GPIO loopback** — is it the MCU/firmware or the analogue front end?
4. **Cross-swap** — is it the component or the wiring?

The order matters: each test is only meaningful once the ones above it
have narrowed the field. That discipline is what turned "the bus doesn't
work" into "module 3 of 5 is dead."
