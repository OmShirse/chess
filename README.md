# ♟️ OmShirse — Code Workspace

A monorepo of personal projects spanning embedded systems, IoT, AI, and game development.

---

## 📂 Projects

### 🎮 Chess (Python + Tkinter)
Full-featured chess game — castling, en passant, promotion, timed mode, check/checkmate detection.
```bash
python chess.py
```

---

### 🚪 Door Alert With Face Recognition
**[`Python/Door-Alert-With-Face-Recognition/`](Python/Door-Alert-With-Face-Recognition/)**  
[![GitHub](https://img.shields.io/badge/GitHub-OmShirse-blue?logo=github)](https://github.com/OmShirse/Door-Alert-With-Face-Recognition)

Real-time face recognition door security system. Camera scans faces → unlocks for known individuals → sends alert for unknowns. Serial output to Arduino/ESP for physical lock/buzzer control.

| Tech | Details |
|---|---|
| Python | OpenCV, face_recognition, imutils |
| Hardware | Arduino/ESP + relay + buzzer |
| Features | Live feed, access log, serial control, extensible face DB |

```bash
python Python/Door-Alert-With-Face-Recognition/encode_faces.py --dataset dataset/ --encodings encodings.pickle
python Python/Door-Alert-With-Face-Recognition/door_alert.py --encodings encodings.pickle
```

---

### 🥚 Smart Egg Incubation System
**[`Python/Smart-Egg-Incubation-System/`](Python/Smart-Egg-Incubation-System/)**  
[![GitHub](https://img.shields.io/badge/GitHub-OmShirse-blue?logo=github)](https://github.com/OmShirse/Smart-Egg-Incubation-System)

IoT-based automated egg incubator. ESP8266 + DHT11 + Blynk with stage-based temperature (37 °C) and humidity control over a 21-day cycle.

| Tech | Details |
|---|---|
| Hardware | ESP8266 NodeMCU, DHT11, relay module, LCD 16×2 |
| Cloud | Blynk IoT (real-time mobile monitoring) |
| Features | 2-stage control, NTP day tracking, relay automation |

---

### 📡 Telemetry System
**[`C/Telemetry-System/`](C/Telemetry-System/)**  
[![GitHub](https://img.shields.io/badge/GitHub-OmShirse-blue?logo=github)](https://github.com/OmShirse/Telemetry-System)

Real-time embedded telemetry — IMU simulation, Madgwick AHRS filter in C, with PyQt5 live dashboard featuring 11-channel graphs + 3D attitude visualization.

| Tech | Details |
|---|---|
| C | Madgwick AHRS, IMU simulator, NMEA protocol |
| Python | PyQt5, pyqtgraph, serial, demo mode |
| Features | 20 Hz update, stdin/serial/demo modes, 3D craft attitude |

```bash
gcc C/Telemetry-System/etelemetry.c -o etelemetry -lm
./etelemetry | python C/Telemetry-System/telemetry_dashboard.py
# or demo mode:
python C/Telemetry-System/telemetry_dashboard.py --demo
```

---

### 🔧 Custom Embedded Driver (C)
**[`C/Custom-Embedded-Driver/`](C/Custom-Embedded-Driver/)**  
Custom GPIO driver and peripheral abstraction for bare-metal embedded targets.

---

### 🤖 TinyLLM (Arduino)
**[`C/tinyllm/`](C/tinyllm/)**  
Lightweight transformer LLM inference on microcontrollers.

---

### ⚙️ Rust Embedded
**[`Rust/`](Rust/)**  
- `led/` — ESP32 LED control in Rust (Embassy/esp-idf)
- `hello_world/` — Rust hello world

---

### 🐍 Python Utilities
**[`Python/`](Python/)**  
General Python scripts and experiments.

---

### 🌐 Site / Reader
**[`Site/`](Site/)**  
Static site reader with archive and chapter-based markdown viewer.

---

## 🛠️ Getting Started

### Prerequisites
- Python 3.8+
- GCC / MinGW
- Arduino IDE (for ESP8266/Arduino projects)
- Rust toolchain (for Rust projects)

### Python dependencies (all projects)
```bash
pip install opencv-python face_recognition imutils pyserial pyqt5 pyqtgraph numpy
```

---

## 📜 License

MIT — feel free to fork, remix, and build on these projects.
