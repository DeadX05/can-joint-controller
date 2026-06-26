"""
Day 2 — PID Position Tracking Analysis
Plots commanded vs actual joint angle over time, plus tracking error,
and computes RMS error overall and per step.

Usage: python analyze_step_response.py
Expects day2_step_response.csv in the same folder.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Load data ---
df = pd.read_csv("day2_step_response.csv")

# --- Plot 1: Commanded vs Actual position over time ---
fig1, ax1 = plt.subplots(figsize=(11, 5))
ax1.plot(df["time_s"], df["target_deg"], "--", color="tab:orange", label="Commanded (target)", linewidth=1.8)
ax1.plot(df["time_s"], df["actual_deg"], "-", color="tab:blue", label="Actual (encoder)", linewidth=1.5)
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Joint angle (deg)")
ax1.set_title("Day 2 — PID Position Tracking: Commanded vs Actual\n(Kp=10, Ki=0.1, Kd=0.1, stiction breakaway=35, deadband=0.6deg)")
ax1.legend(loc="best")
ax1.grid(True, alpha=0.3)
fig1.tight_layout()
fig1.savefig("tracking_commanded_vs_actual.png", dpi=150)

# --- Plot 2: Tracking error over time ---
fig2, ax2 = plt.subplots(figsize=(11, 4))
ax2.plot(df["time_s"], df["error_deg"], color="tab:red", linewidth=1.3)
ax2.axhline(0, color="black", linewidth=0.8)
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Error (deg)")
ax2.set_title("Day 2 — Tracking Error vs Time")
ax2.grid(True, alpha=0.3)
fig2.tight_layout()
fig2.savefig("tracking_error.png", dpi=150)

# --- RMS error: overall and per phase (per commanded step) ---
overall_rms = np.sqrt(np.mean(df["error_deg"] ** 2))

print("=== Day 2 Tracking Results ===")
print(f"Overall RMS error across all 9 steps: {overall_rms:.3f} deg\n")

print("Per-step settled error (last sample of each phase):")
for phase, group in df.groupby("phase", sort=False):
    last_row = group.iloc[-1]
    phase_rms = np.sqrt(np.mean(group["error_deg"] ** 2))
    print(f"  {phase:28s} target={last_row['target_deg']:7.2f}  "
          f"final_error={last_row['error_deg']:6.2f}  phase_RMS={phase_rms:6.2f}")

print("\nFigures saved: tracking_commanded_vs_actual.png, tracking_error.png")
