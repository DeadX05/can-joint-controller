# Step-Response Characterisation over CAN

Closed-loop step response of the joint, commanded and observed entirely
over the CAN bus. Below: the raw supervisor (Node B) serial output during
commanded step sequences — the joint controller (Node A) running the tuned
PID and returning 0x110 status frames — followed by the settled-error and
overshoot summaries.

## Provenance — read this before using the numbers

This file is **transcribed from serial-monitor screenshots**, not saved
from the original serial buffer. The buffer was lost when the monitor was
closed. Consequences:

- Only the portions visible on screen are reproduced. There are **gaps
  between runs and between scroll positions** — these are marked.
- Long stretches of identical `[SETTLED]` lines are **collapsed** with an
  annotation. The exact repeat counts are not recoverable, so no count is
  asserted.
- Every value below is read directly off a screenshot. Values are believed
  accurate; absence of a line is not evidence it did not occur.

The original screenshots are the primary evidence and should be kept
alongside this file.

Status frames were emitted at 10 Hz (100 ms) in these runs. The non-logging
display path throttles printing to one line per 500 ms, so **transients
between status prints are not resolved**. Peak overshoot values below are
whatever happened to be sampled, and true peaks may be larger.

---

## Run 1

```
# logging off
STATUS: pos=0.3  target=0.0  err=-0.3  pwm=0  [SETTLED]
    [line repeats]
# command sent: 10.0
STATUS: pos=9.4  target=10.0  err=0.5  pwm=0  [SETTLED]
    [line repeats]
# command sent: 45.0
STATUS: pos=20.1  target=45.0  err=24.8  pwm=245
STATUS: pos=44.6  target=45.0  err=0.3  pwm=0  [SETTLED]
    [line repeats]
# command sent: 90.0
STATUS: pos=89.5  target=90.0  err=0.4  pwm=0  [SETTLED]
    [line repeats]

    [scroll gap]

# command sent: 180.0
STATUS: pos=158.0  target=180.0  err=21.9  pwm=217
STATUS: pos=180.0  target=180.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=161.1  target=0.0  err=-161.1  pwm=255
STATUS: pos=0.9  target=0.0  err=-0.9  pwm=35
STATUS: pos=0.0  target=0.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: -45.0
STATUS: pos=-46.4  target=-45.0  err=1.4  pwm=35
STATUS: pos=-45.2  target=-45.0  err=0.2  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=0.0  target=0.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
```

Logging was then enabled while the joint was already parked, so the CSV
rows from this run contain only the stationary state:

```
ms,pos,target,err,pwm,settled
162962,0.0,0.0,0.0,0,1
162982,0.0,0.0,0.0,0,1
    [identical rows continue to at least 165002]
```

---

## Run 2

```
STATUS: pos=0.0  target=0.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=0.0  target=0.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: 10.0
STATUS: pos=10.0  target=10.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: 20.0
STATUS: pos=10.0  target=20.0  err=9.9  pwm=0
STATUS: pos=19.7  target=20.0  err=0.2  pwm=0  [SETTLED]
    [line repeats]
# command sent: 45.0
STATUS: pos=44.9  target=45.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: 90.0
STATUS: pos=63.4  target=90.0  err=26.5  pwm=255
STATUS: pos=89.5  target=90.0  err=0.4  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=-1.5  target=0.0  err=1.5  pwm=35
STATUS: pos=-0.3  target=0.0  err=0.3  pwm=0  [SETTLED]
    [line repeats]
# command sent: 180.0
STATUS: pos=37.6  target=180.0  err=142.3  pwm=255
STATUS: pos=180.3  target=180.0  err=-0.3  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=156.4  target=0.0  err=-156.4  pwm=255
STATUS: pos=1.2  target=0.0  err=-1.2  pwm=35
STATUS: pos=0.0  target=0.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: -45.0
STATUS: pos=-47.4  target=-45.0  err=2.4  pwm=35
STATUS: pos=-45.2  target=-45.0  err=0.2  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=-41.1  target=0.0  err=41.1  pwm=255
STATUS: pos=0.3  target=0.0  err=-0.3  pwm=0  [SETTLED]
    [line repeats]
```

Logging enabled after the sequence completed; again only the parked state
was recorded:

```
ms,pos,target,err,pwm,settled
891925,0.3,0.0,-0.3,0,1
891945,0.3,0.0,-0.3,0,1
    [identical rows continue]
```

---

## Run 3 (partial — earlier portion not captured)

```
STATUS: pos=89.8  target=90.0  err=0.1  pwm=0  [SETTLED]
    [line repeats]
# command sent: 180.0
STATUS: pos=179.6  target=180.0  err=0.3  pwm=35  [SETTLED]
STATUS: pos=179.6  target=180.0  err=0.3  pwm=0   [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=41.7  target=0.0  err=-41.7  pwm=255
STATUS: pos=0.0  target=0.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: -45.0
STATUS: pos=-46.1  target=-45.0  err=1.1  pwm=35
STATUS: pos=-44.9  target=-45.0  err=0.0  pwm=0  [SETTLED]
    [line repeats]
# command sent: 0.0
STATUS: pos=0.6  target=0.0  err=-0.6  pwm=35
STATUS: pos=-0.3  target=0.0  err=0.3  pwm=0  [SETTLED]
    [line repeats]
```

Logging enabled at the end, joint parked:

```
ms,pos,target,err,pwm,settled
36220,-0.3,0.0,0.3,0,1
36240,-0.3,0.0,0.3,0,1
    [identical rows continue to at least 36400]
```

Note the 20 ms timestamp spacing here: this run used the 50 Hz
characterisation build of the joint controller. The committed default is
100 ms (10 Hz).

---

## Reading artifact — `pwm` lags by one control cycle

Several lines show an inconsistent-looking `pwm` value, e.g.

```
STATUS: pos=10.0  target=20.0  err=9.9  pwm=0
STATUS: pos=179.6 target=180.0 err=0.3  pwm=35  [SETTLED]
```

This is not a control fault. `sendStatus()` reports `lastPwm`, which is
written by the previous PID iteration. When a status frame is emitted
between a target change and the next control tick, it carries the drive
value from before the change. The `settled` flag, by contrast, is computed
fresh at send time. The two can therefore disagree for one frame.

---

## Summary — settled position by commanded angle

| Command | Settled position(s) | Error |
|---|---|---|
| 10 | 9.4, 10.0 | 0.5, 0.0 |
| 20 | 19.7 | 0.2 |
| 45 | 44.6, 44.9 | 0.3, 0.0 |
| 90 | 89.5, 89.5, 89.8 | 0.4, 0.4, 0.1 |
| 180 | 180.0, 180.3, 179.6 | 0.0, 0.3, 0.3 |
| −45 | −45.2, −45.2, −44.9 | 0.2, 0.2, 0.0 |
| 0 | 0.0, −0.3, 0.3 | 0.0, 0.3, 0.3 |

Steady-state error across all runs: **0.0–0.5°**, every value inside the
0.6° control deadband. The deadband is what bounds this figure — the
controller stops correcting once within it — so the number reflects a
design parameter, not a measurement limit. Tightening the deadband
reintroduces the stiction-driven limit cycle identified during PID tuning.

## Summary — overshoot on large steps

| Transition | Sampled peak | Excursion past target | Recovered to |
|---|---|---|---|
| 89.5 → 0 | −1.5 | 1.5° | −0.3 |
| 180 → 0 | +1.2 | 1.2° | 0.0 |
| 0 → −45 | −47.4 | 2.4° | −45.2 |
| 0 → −45 | −46.1 | 1.1° | −44.9 |
| 0.9 → 0 | +0.9 | 0.9° | 0.0 |

Large, fast moves travel past the target and are pulled back. Every
recovery line reads `pwm=35`, the stiction breakaway floor — the smallest
drive the controller will apply — so the joint is being walked back into
the deadband at minimum effort.

Attributed to the rotational inertia of the printed lever back-driving the
joint after the controller cuts drive. The TB6612 is left with both
direction inputs LOW at zero command, which is high-impedance coast rather
than short brake, so nothing damps that momentum. Switching the zero case
to short brake (both inputs HIGH) is the candidate mitigation and is not
yet tested.

Peaks above are the values that happened to fall on a status frame. With
500 ms display throttling in these runs, true peak overshoot may be larger
and the recovery transient is not resolved.
