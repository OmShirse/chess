# 📡 Telemetry System

> **Real-time embedded telemetry** — IMU sensor simulation, Madgwick AHRS filter, and live Python dashboard.  
> C (GCC) · Python · PyQt5 · Matplotlib

[![GitHub](https://img.shields.io/badge/GitHub-OmShirse-blue?logo=github)](https://github.com/OmShirse/Telemetry-System)

---

## 📌 Overview

A two-part telemetry system for embedded platforms:

- **Part 1 (Basic):** Core IMU simulation + AHRS filter in C, simple data output
- **Part 2 (Advanced):** Full PyQt5 live dashboard with 3D attitude visualization, NMEA protocol, cross-platform serial support

---

## 📁 Project Structure

| File | Description |
|---|---|
| `etelemetry.c` | IMU simulator + Madgwick AHRS — outputs tab-delimited or NMEA format |
| `telemetry_tx.c` | NMEA transmitter at 20 Hz — cross-platform (Linux / Windows) |
| `ahrs_filter.c` | Standalone AHRS filter reference implementation |
| `sensor_sim.c` | Sensor simulation utilities (accel, gyro, mag) |
| `visualizer.py` | Matplotlib visualizer — 11 channels + 3D attitude cube |
| `telemetry_dashboard.py` | Full PyQt5 dashboard — tabs, live graphs, 3D craft model |
| `uart_rx.py` | Serial receiver utility for hardware UART |

---

## 🚀 Quick Start

### Compile
```bash
gcc etelemetry.c -o etelemetry -lm
gcc telemetry_tx.c -o telemetry_tx -lm
```

### Run with live dashboard
```bash
# Pipe simulated telemetry into dashboard
./etelemetry | python telemetry_dashboard.py

# Demo mode (no hardware needed)
python telemetry_dashboard.py --demo

# Live serial port
python telemetry_dashboard.py --port /dev/ttyUSB0 --baud 115200
```

### Lightweight visualizer
```bash
./etelemetry | python visualizer.py
```

---

## 🛠️ Dependencies

### C side
- GCC (or MinGW on Windows)
- Standard C library + math (`-lm`)

### Python side
```bash
pip install pyqt5 pyserial matplotlib numpy
```

---

## 📊 Dashboard Features

| Feature | Details |
|---|---|
| 11-channel live graphs | Accel XYZ, Gyro XYZ, Mag XYZ, Roll/Pitch/Yaw |
| 3D attitude cube | Real-time OpenGL-style craft orientation |
| NMEA protocol | `$IMUDT` sentence format |
| 20 Hz update rate | Suitable for flight/robotics control loops |
| Demo mode | No hardware needed — runs fully simulated |

---

## 🔭 Further Scope / Improvements

- [ ] **Hardware integration** — port C code to STM32/Arduino for real IMU (MPU6050, ICM-42688)
- [ ] **Kalman filter** — implement EKF alongside Madgwick for comparison
- [ ] **Logging to CSV/HDF5** — timestamped session recording
- [ ] **UDP/WebSocket streaming** — broadcast telemetry over network (for multi-device dashboards)
- [ ] **GPS fusion** — integrate NMEA GPS sentences for position + attitude
- [ ] **Alert thresholds** — visual/audio alert if roll/pitch exceeds safe limits
- [ ] **Python → Rust port** — rewrite dashboard in Rust/egui for lower latency
- [ ] **CAN bus support** — parse automotive CAN frames alongside IMU
- [ ] **ROS2 node** — publish as ROS2 topics for robot integration

---

## 📐 NMEA Sentence Format

```
$IMUDT,<roll>,<pitch>,<yaw>,<ax>,<ay>,<az>,<gx>,<gy>,<gz>*<checksum>
```

Example:
```
$IMUDT,12.34,-5.67,89.01,0.12,-0.03,9.81,0.01,-0.02,0.00*4F
```

---

## 🤝 Contributing

See [GitHub repo](https://github.com/OmShirse/Telemetry-System) for open issues and roadmap.

---

*Part of the [OmShirse/chess](https://github.com/OmShirse/chess) monorepo*
