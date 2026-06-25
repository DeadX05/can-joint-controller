CAN-Bus Joint Controller

A single-joint robotic motor controller prototype demonstrating closed-loop PID position control over a CAN bus network — built as a portfolio project and architectural prototype for a future quadruped robot.

System Overview

Two ESP32 nodes communicate over a CAN bus (MCP2551 transceivers):


Node A — Joint controller: drives an N20 motor via TB6612, reads encoder feedback, runs closed-loop PID position control
Node B — Supervisor: sends position commands over CAN, receives status, logs data to PC via USB serial


Repository Structure

can-joint-controller/
├── node_a/          # Joint controller firmware (Arduino/ESP32)
├── node_b/          # Supervisor firmware (Arduino/ESP32)
├── analysis/        # Python data logger + tracking error plotter
└── docs/            # Circuit diagram, CAN protocol spec, photos

CAN Protocol

See docs/can_protocol.md

Hardware

ComponentPartMicrocontrollerESP32 (×2)Motor driverTB6612FNGMotorN20 with Hall encoderCAN transceiverMCP2551 (×2)Termination2× 220Ω in parallel (~110Ω) at each bus endLogic level3.3V/5V bidirectional level shifterPower2S LiPo (7.4V) + buck converter → 3.3V logic

Results

(To be filled in after Day 5 — tracking error plots and RMS values will go here)

Phase 2 Plan

Scale to a 2-DOF leg with two joint nodes on the same CAN bus — hardware design and parts list in /docs/phase2.md.
