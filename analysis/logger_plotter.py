"""
analysis/logger_plotter.py
CAN Joint Controller — serial data logger + tracking error plotter

Day 1: Run in MOCK mode to test plots against generated fake data.
Day 2+: Run in LIVE mode to log real serial data from Node B.

Usage:
    # Mock mode (no hardware needed — Day 1):
    python logger_plotter.py --mock

    # Live mode (Node B connected via USB):
    python logger_plotter.py --port COM3 --output data/trial_01.csv
    python logger_plotter.py --port /dev/ttyUSB0 --output data/trial_01.csv

    # Plot only from existing CSV (no serial needed):
    python logger_plotter.py --plot data/trial_01.csv

Requirements:
    pip install pyserial matplotlib numpy
"""

import argparse
import csv
import math
import os
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np


# ── Mock data generator ──────────────────────────────────────────────────────
def generate_mock_data(duration_s=30, dt_ms=50, period_s=6.0, amplitude_deg=45.0):
    """
    Generates fake commanded + actual position data.
    Simulates a sine-wave setpoint with a slightly lagging, noisy actual response.
    Used on Day 1 to test the plotter without any hardware.
    """
    rows = []
    t = 0
    prev_actual = 0.0

    while t <= duration_s * 1000:
        cmd = amplitude_deg * math.sin(2 * math.pi * (t / 1000.0) / period_s)

        # Simulate a sluggish, noisy motor response
        lag        = 0.92
        noise      = np.random.normal(0, 0.8)
        actual     = lag * prev_actual + (1 - lag) * cmd + noise
        prev_actual = actual

        rows.append({
            "t_ms":        round(t),
            "setpoint_deg": round(cmd, 3),
            "actual_deg":   round(actual, 3),
            "error_deg":    round(cmd - actual, 3),
        })
        t += dt_ms

    return rows


# ── Serial logger ────────────────────────────────────────────────────────────
def log_from_serial(port, baudrate=115200, output_path=None, duration_s=60):
    """
    Reads CSV lines from Node B over USB serial and saves to a file.
    Expected Node B serial format:  t_ms,setpoint_deg,actual_deg
    """
    import serial  # imported here so mock mode works without pyserial

    if output_path is None:
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/trial_{timestamp}.csv"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Logging from {port} → {output_path}  (duration: {duration_s}s)")
    print("Press Ctrl+C to stop early.\n")

    rows = []
    start = time.time()

    with serial.Serial(port, baudrate, timeout=1) as ser:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["t_ms", "setpoint_deg", "actual_deg", "error_deg"])
            writer.writeheader()

            while time.time() - start < duration_s:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line or line.startswith("#") or line.startswith(">>"):
                    continue
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                try:
                    row = {
                        "t_ms":         int(parts[0]),
                        "setpoint_deg": float(parts[1]),
                        "actual_deg":   float(parts[2]),
                        "error_deg":    round(float(parts[1]) - float(parts[2]), 3),
                    }
                    writer.writerow(row)
                    rows.append(row)
                    print(f"  {row['t_ms']:6d} ms  cmd={row['setpoint_deg']:7.2f}°  actual={row['actual_deg']:7.2f}°  err={row['error_deg']:+.2f}°")
                except ValueError:
                    continue

    print(f"\nLogged {len(rows)} samples → {output_path}")
    return rows, output_path


# ── Plotter ──────────────────────────────────────────────────────────────────
def plot_results(rows, title_suffix="", save_dir="figures"):
    """
    Generates two figures:
      1. Commanded vs actual position over time
      2. Tracking error over time + RMS annotation
    Saves as PNG in save_dir.
    """
    os.makedirs(save_dir, exist_ok=True)

    t        = np.array([r["t_ms"]        for r in rows]) / 1000.0  # → seconds
    cmd      = np.array([r["setpoint_deg"] for r in rows])
    actual   = np.array([r["actual_deg"]   for r in rows])
    error    = cmd - actual
    rms      = float(np.sqrt(np.mean(error ** 2)))

    # ── Figure 1: position tracking ──────────────────────────
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(t, cmd,    "--", color="#534AB7", linewidth=1.5, label="Commanded (setpoint)")
    ax1.plot(t, actual, "-",  color="#D85A30", linewidth=1.5, label="Actual (encoder)")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Position (degrees)")
    ax1.set_title(f"Joint Position Tracking — PID Closed-Loop via CAN{title_suffix}")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    path1 = os.path.join(save_dir, f"tracking{title_suffix.replace(' ', '_')}.png")
    fig1.savefig(path1, dpi=150)
    print(f"Saved: {path1}")

    # ── Figure 2: tracking error ──────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(10, 3))
    ax2.plot(t, error, "-", color="#3B6D11", linewidth=1.2, label="Tracking error")
    ax2.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax2.fill_between(t, error, alpha=0.15, color="#3B6D11")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Error (degrees)")
    ax2.set_title(f"Tracking Error{title_suffix}  |  RMS = {rms:.2f}°")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    fig2.tight_layout()
    path2 = os.path.join(save_dir, f"error{title_suffix.replace(' ', '_')}.png")
    fig2.savefig(path2, dpi=150)
    print(f"Saved: {path2}")

    plt.show()
    print(f"\nRMS tracking error: {rms:.3f}°")
    return rms


# ── Multi-trial comparison plot ───────────────────────────────────────────────
def plot_multi_trial(csv_paths, labels, save_dir="figures"):
    """
    Overlays tracking error curves from multiple CSV trials on one figure.
    Used on Day 5: slow / medium / fast sine-wave comparison.
    """
    os.makedirs(save_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 4))
    colors = ["#534AB7", "#D85A30", "#3B6D11"]

    for i, (path, label) in enumerate(zip(csv_paths, labels)):
        rows   = load_csv(path)
        t      = np.array([r["t_ms"] for r in rows]) / 1000.0
        error  = np.array([r["setpoint_deg"] for r in rows]) - np.array([r["actual_deg"] for r in rows])
        rms    = float(np.sqrt(np.mean(error ** 2)))
        ax.plot(t, error, "-", color=colors[i % len(colors)],
                linewidth=1.3, label=f"{label}  (RMS={rms:.2f}°)")

    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Error (degrees)")
    ax.set_title("Tracking Error — Slow / Medium / Fast Sine Comparison")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path_out = os.path.join(save_dir, "multi_trial_comparison.png")
    fig.savefig(path_out, dpi=150)
    print(f"Saved: {path_out}")
    plt.show()


# ── CSV helpers ──────────────────────────────────────────────────────────────
def save_csv(rows, path):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["t_ms", "setpoint_deg", "actual_deg", "error_deg"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV saved: {path}")


def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC))


# ── Entry point ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CAN Joint Controller — logger + plotter")
    parser.add_argument("--mock",     action="store_true",  help="Generate and plot mock data (no hardware)")
    parser.add_argument("--port",     type=str, default=None, help="Serial port for live logging (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--output",   type=str, default=None, help="Output CSV path for live logging")
    parser.add_argument("--plot",     type=str, default=None, help="Plot from existing CSV file")
    parser.add_argument("--duration", type=int, default=60,   help="Live logging duration in seconds (default 60)")
    args = parser.parse_args()

    if args.mock:
        print("Running in MOCK mode — generating fake data...\n")
        rows = generate_mock_data(duration_s=30, period_s=6.0, amplitude_deg=45.0)
        save_csv(rows, "data/mock_trial.csv")
        plot_results(rows, title_suffix=" (mock data)")

    elif args.plot:
        print(f"Plotting from: {args.plot}\n")
        rows = load_csv(args.plot)
        plot_results(rows, title_suffix=f" ({os.path.basename(args.plot)})")

    elif args.port:
        rows, out_path = log_from_serial(args.port, output_path=args.output, duration_s=args.duration)
        if rows:
            plot_results(rows, title_suffix=" (live data)")

    else:
        print("No mode specified. Try:")
        print("  python logger_plotter.py --mock")
        print("  python logger_plotter.py --port COM3")
        print("  python logger_plotter.py --plot data/trial_01.csv")


if __name__ == "__main__":
    main()
