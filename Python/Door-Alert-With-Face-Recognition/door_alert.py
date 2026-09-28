"""
Door Alert With Face Recognition
=================================
Real-time face recognition door security system.
Sends serial signal to Arduino/ESP for lock/unlock.

Usage:
    python door_alert.py --encodings encodings.pickle
"""

import cv2
import face_recognition
import pickle
import imutils
import numpy as np
import time
import argparse
from datetime import datetime

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

# ─── Config ──────────────────────────────────────────────────────────────────
TOLERANCE     = 0.5          # Lower = stricter face matching
CAMERA_INDEX  = 0            # 0 = built-in, 1 = USB
SERIAL_PORT   = "/dev/ttyUSB0"
BAUD_RATE     = 9600
FRAME_WIDTH   = 600          # Resize width for speed
LOG_FILE      = "access_log.csv"

# Serial commands sent to Arduino
CMD_UNLOCK    = b'U'
CMD_LOCK      = b'L'
CMD_ALERT     = b'A'

# ─── Argument Parsing ─────────────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser(description="Door Alert With Face Recognition")
    ap.add_argument("-e", "--encodings", default="encodings.pickle",
                    help="path to face encodings")
    ap.add_argument("-o", "--output", default="",
                    help="path to output video (blank = no save)")
    ap.add_argument("-d", "--display", type=int, default=1,
                    help="display live feed (1) or headless (0)")
    ap.add_argument("--no-serial", action="store_true",
                    help="disable serial port (test mode)")
    return ap.parse_args()


# ─── Serial Helper ────────────────────────────────────────────────────────────
def init_serial(port, baud):
    if not SERIAL_AVAILABLE:
        print("[WARN] pyserial not installed — serial disabled")
        return None
    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # wait for Arduino reset
        print(f"[INFO] Serial connected on {port}")
        return ser
    except serial.SerialException as e:
        print(f"[WARN] Serial init failed: {e}")
        return None


# ─── Logging ──────────────────────────────────────────────────────────────────
def log_event(name: str, status: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp},{name},{status}\n")
    print(f"[LOG] {timestamp} | {name} | {status}")


# ─── Encode Faces Helper ──────────────────────────────────────────────────────
def load_encodings(path: str) -> dict:
    print(f"[INFO] Loading encodings from {path} ...")
    with open(path, "rb") as f:
        data = pickle.loads(f.read())
    print(f"[INFO] Loaded {len(data['names'])} face(s): {set(data['names'])}")
    return data


# ─── Main Loop ────────────────────────────────────────────────────────────────
def run(args):
    data = load_encodings(args.encodings)
    ser  = None if args.no_serial else init_serial(SERIAL_PORT, BAUD_RATE)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera {CAMERA_INDEX}")

    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        writer = cv2.VideoWriter(args.output, fourcc, 20, (FRAME_WIDTH, 480))

    last_command = None
    print("[INFO] Starting door alert — press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = imutils.resize(frame, width=FRAME_WIDTH)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect faces
        boxes    = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)

        names = []
        for enc in encodings:
            matches   = face_recognition.compare_faces(data["encodings"], enc, TOLERANCE)
            distances = face_recognition.face_distance(data["encodings"], enc)

            if True in matches:
                best_idx  = np.argmin(distances)
                name      = data["names"][best_idx] if matches[best_idx] else "Unknown"
            else:
                name = "Unknown"
            names.append(name)

        # Draw boxes and send commands
        for (top, right, bottom, left), name in zip(boxes, names):
            color    = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            label    = name if name != "Unknown" else "⚠ UNKNOWN"
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 4, bottom - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cmd = CMD_UNLOCK if name != "Unknown" else CMD_ALERT
            if cmd != last_command:
                if ser:
                    ser.write(cmd)
                log_event(name, "UNLOCKED" if cmd == CMD_UNLOCK else "ALERT")
                last_command = cmd

        if writer:
            writer.write(frame)

        if args.display:
            cv2.imshow("Door Alert — Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Cleanup
    cap.release()
    if writer:
        writer.release()
    if ser:
        ser.write(CMD_LOCK)
        ser.close()
    cv2.destroyAllWindows()
    print("[INFO] Done.")


if __name__ == "__main__":
    args = parse_args()
    run(args)
