# 🚪 Door Alert With Face Recognition

> **Smart door security system** — camera scans faces, unlocks for known individuals, alerts for unknowns.  
> Built with Python · OpenCV · face_recognition · Arduino/ESP compatible

[![GitHub](https://img.shields.io/badge/GitHub-OmShirse-blue?logo=github)](https://github.com/OmShirse/Door-Alert-With-Face-Recognition)

---

## 📌 Overview

A smart door alert system that uses a camera to perform **real-time face recognition**. Known faces (family, authorized users) trigger an unlock signal; unknown faces trigger an alert — all with live visual feedback.

**Hardware:** Pairs with an Arduino/ESP microcontroller for physical lock/buzzer control.

---

## 🎯 Features

| Feature | Details |
|---|---|
| 🎥 Real-time face detection | Webcam-based, runs at ~30 fps |
| 🧠 Face recognition | Compares against `encodings.pickle` database |
| 🏷️ Visual labeling | Live feed with "Known" / "Unknown" bounding boxes |
| 🔒 Access control | Sends serial signal to Arduino/ESP for lock/unlock |
| 🔔 Alert system | Buzzer/LED trigger for unrecognized faces |
| 📂 Extensible DB | Add new faces via `encode_faces.py` script |

---

## 🛠️ Hardware Requirements

- Webcam (USB or built-in)
- Arduino / ESP8266 / ESP32 (for lock relay + buzzer)
- Relay module (for door lock actuator)
- Optional: Piezo buzzer, RGB LED

---

## 💻 Software Requirements

```
Python 3.8+
opencv-python
face_recognition
dlib
imutils
pyserial       # for Arduino communication
pickle
```

Install with:
```bash
pip install opencv-python face_recognition imutils pyserial
```

> **Note:** `face_recognition` requires `dlib`. On Linux:  
> `sudo apt install cmake libopenblas-dev liblapack-dev`

---

## 🚀 Quick Start

### 1. Encode known faces
```bash
python encode_faces.py --dataset dataset/ --encodings encodings.pickle
```
Place face images in `dataset/<person_name>/photo.jpg` format.

### 2. Run the door alert system
```bash
python door_alert.py --encodings encodings.pickle --output output/
```

### 3. Optional: Connect to Arduino
Upload `arduino/door_lock.ino` to your board and set the serial port in `config.py`.

---

## 📁 Project Structure

```
Door-Alert-With-Face-Recognition/
├── door_alert.py          # Main face recognition loop
├── encode_faces.py        # Script to encode new faces
├── config.py              # Serial port, thresholds, camera index
├── encodings.pickle       # Pre-trained face encodings (generated)
├── arduino/
│   └── door_lock.ino      # Arduino sketch (relay + buzzer control)
├── dataset/               # Training face images (per-person folders)
└── README.md
```

---

## ⚙️ Configuration (`config.py`)

```python
SERIAL_PORT   = "/dev/ttyUSB0"   # Arduino serial port
BAUD_RATE     = 9600
TOLERANCE     = 0.5              # Lower = stricter matching
CAMERA_INDEX  = 0                # 0 = built-in, 1 = USB cam
```

---

## 🔭 Further Scope / Improvements

- [ ] **MQTT integration** — publish alerts to a home-automation broker (Home Assistant)
- [ ] **Telegram / SMS alerts** — send photo of unknown visitor to phone
- [ ] **Face registration UI** — simple Tkinter/Flask web UI to add new faces
- [ ] **Multiple camera support** — front door + back door
- [ ] **Attendance logging** — log recognized faces with timestamps to CSV/SQLite
- [ ] **Anti-spoofing** — detect printed photos vs live faces (liveness detection)
- [ ] **GPU acceleration** — use CUDA/OpenCV DNN for faster detection
- [ ] **Edge deployment** — run on Raspberry Pi with PiCamera module

---

## 🤝 Contributing

Pull requests welcome. See [GitHub repo](https://github.com/OmShirse/Door-Alert-With-Face-Recognition) for issues.

---

*Part of the [OmShirse/chess](https://github.com/OmShirse/chess) monorepo*
