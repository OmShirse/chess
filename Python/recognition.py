import cv2
import face_recognition
import pickle
import sys
import csv
import argparse
from datetime import datetime
from pathlib import Path

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Face Recognition Door Alert")
parser.add_argument("--camera",    type=int,   default=0,    help="Camera index (default 0)")
parser.add_argument("--threshold", type=float, default=0.55, help="Match threshold 0.0–1.0 (lower = stricter, default 0.55)")
parser.add_argument("--encodings", type=str,   default="encodings.pickle", help="Path to encodings file")
parser.add_argument("--log",       type=str,   default="access_log.csv",   help="Path to access log CSV")
args = parser.parse_args()

MATCH_THRESHOLD = args.threshold   # Bug fix #2: was hardcoded 0.7, now configurable
LOG_PATH        = args.log
PROCESS_EVERY_N = 3               # run recognition every Nth frame

# ── Load encodings ────────────────────────────────────────────────────────────
try:
    with open(args.encodings, "rb") as f:
        data = pickle.load(f)
        known_encodings = data["encodings"]
        known_names     = data["names"]
    print(f"✅ Loaded {len(known_names)} known face(s): {', '.join(set(known_names))}")
except FileNotFoundError:
    print(f"❌ Error: '{args.encodings}' not found.")
    print("   Run the encoding script first to generate it.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading encodings: {e}")
    sys.exit(1)

# ── Bug fix #1: authorised_names = people who SHOULD have access ───────────────
# These are the names whose photos are in your encodings database.
# Anyone recognised at or below MATCH_THRESHOLD gets GREEN (access granted).
# Anyone not recognised or above threshold gets RED (alert / unknown).
# Previously this was inverted — the owner's name triggered a red alert.
authorised_names = set(known_names)   # everyone in your database is authorised by default

# ── Access log ────────────────────────────────────────────────────────────────
def log_access(name: str, confidence: float, status: str):
    """Bug fix #6: append every detection event to a CSV log."""
    log_exists = Path(LOG_PATH).exists()
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not log_exists:
            writer.writerow(["timestamp", "name", "confidence", "status"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            name,
            f"{confidence:.3f}",
            status
        ])

# ── Open webcam ───────────────────────────────────────────────────────────────
# Bug fix #3: CAP_DSHOW is Windows-only — pick backend per platform
if sys.platform == "win32":
    video_capture = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
else:
    video_capture = cv2.VideoCapture(args.camera)   # Linux/Mac: no backend flag

if not video_capture.isOpened():
    print(f"❌ Error: Could not open camera index {args.camera}.")
    print("   Try --camera 1 if you have multiple cameras.")
    sys.exit(1)

print(f"✅ Camera opened (index {args.camera})")
print(f"   Threshold : {MATCH_THRESHOLD} (lower = stricter)")
print(f"   Log file  : {LOG_PATH}")
print("   Press 'q' to quit\n")

# ── State ─────────────────────────────────────────────────────────────────────
frame_count        = 0
# Bug fix #4: store per-face results as a list, not a single last_name
face_results       = []   # list of (top, right, bottom, left, name, color)
logged_this_second = set()   # avoid spamming log with duplicates

# ── Colours ───────────────────────────────────────────────────────────────────
COLOR_AUTHORISED = (0, 200, 0)    # green  — known, access granted
COLOR_UNKNOWN    = (0, 0, 220)    # red    — unknown, alert

try:
    while True:
        ret, frame = video_capture.read()
        if not ret or frame is None:
            print("❌ Failed to grab frame.")
            break

        # Resize to 1/4 for faster face detection
        small_frame     = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]   # BGR → RGB

        frame_count += 1

        # ── Run recognition every Nth frame ───────────────────────────────────
        if frame_count % PROCESS_EVERY_N == 0:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_results   = []   # reset results for this batch

            if face_locations:
                # Bug fix #4: encode ALL faces, not just face_locations[0]
                face_encodings = face_recognition.face_encodings(
                    rgb_small_frame, face_locations
                )

                for face_loc, face_enc in zip(face_locations, face_encodings):
                    top, right, bottom, left = [int(v * 4) for v in face_loc]
                    name   = "Unknown"
                    status = "ALERT"
                    color  = COLOR_UNKNOWN
                    confidence = 1.0   # distance (lower = better match)

                    if len(known_encodings) > 0:
                        distances = face_recognition.face_distance(known_encodings, face_enc)
                        best_idx  = distances.argmin()
                        confidence = float(distances[best_idx])

                        # Bug fix #2: threshold 0.55 instead of 0.7
                        if confidence < MATCH_THRESHOLD:
                            name   = known_names[best_idx]
                            status = "GRANTED"
                            # Bug fix #1: authorised names get GREEN
                            color  = COLOR_AUTHORISED if name in authorised_names else COLOR_UNKNOWN

                    face_results.append((top, right, bottom, left, name, color, confidence, status))

                    # Log — throttle to once per second per person
                    log_key = f"{name}_{datetime.now().strftime('%H:%M:%S')}"
                    if log_key not in logged_this_second:
                        logged_this_second.add(log_key)
                        log_access(name, confidence, status)
                        if len(logged_this_second) > 500:
                            logged_this_second.clear()

        # ── Draw results on frame ─────────────────────────────────────────────
        for result in face_results:
            top, right, bottom, left, name, color, confidence, status = result

            # Bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Label background
            cv2.rectangle(frame, (left, bottom - 26), (right, bottom), color, cv2.FILLED)

            # Name + confidence
            label = f"{name}  {confidence:.2f}"
            cv2.putText(frame, label, (left + 4, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            # Status badge top-left corner
            badge_color = (30, 180, 30) if status == "GRANTED" else (30, 30, 200)
            cv2.rectangle(frame, (left, top - 22), (left + 90, top), badge_color, cv2.FILLED)
            cv2.putText(frame, status, (left + 4, top - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)

        # ── HUD overlay ───────────────────────────────────────────────────────
        ts = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"Faces: {len(face_results)}  |  {ts}  |  thr:{MATCH_THRESHOLD}",
                    (10, 22), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Door Alert — Face Recognition  [q to quit]", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    video_capture.release()
    cv2.destroyAllWindows()
    print(f"\n✅ Session ended. Access log saved to: {LOG_PATH}")