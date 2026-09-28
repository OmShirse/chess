"""
telemetry_dashboard.py — PyQt5 Live Telemetry Dashboard
=========================================================
Reads tab-delimited IMU + AHRS data from stdin or serial port
and displays live graphs + 3D attitude visualization.

Usage:
    ./etelemetry | python telemetry_dashboard.py          # stdin pipe
    python telemetry_dashboard.py --demo                  # demo mode
    python telemetry_dashboard.py --port /dev/ttyUSB0     # serial port
"""

import sys
import argparse
import math
import time
import threading
import collections
from datetime import datetime

import numpy as np

try:
    from PyQt5 import QtWidgets, QtCore, QtGui
    import pyqtgraph as pg
    import pyqtgraph.opengl as gl
    PYQT_OK = True
except ImportError:
    PYQT_OK = False
    print("[WARN] PyQt5/pyqtgraph not installed — running data-only mode")

try:
    import serial
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False


# ─── Config ──────────────────────────────────────────────────────────────────
CHANNELS     = ["ax", "ay", "az", "gx", "gy", "gz", "roll", "pitch", "yaw"]
HISTORY_LEN  = 200     # samples kept in rolling buffer
UPDATE_MS    = 50      # UI refresh interval (ms) → 20 fps


# ─── Data Buffer ─────────────────────────────────────────────────────────────
class TelemetryBuffer:
    def __init__(self, channels, maxlen=HISTORY_LEN):
        self.channels = channels
        self.data     = {ch: collections.deque([0.0]*maxlen, maxlen=maxlen) for ch in channels}
        self.lock     = threading.Lock()
        self.latest   = {ch: 0.0 for ch in channels}

    def push(self, row: dict):
        with self.lock:
            for ch in self.channels:
                val = row.get(ch, 0.0)
                self.data[ch].append(val)
                self.latest[ch] = val

    def get_array(self, ch):
        with self.lock:
            return list(self.data[ch])


# ─── Data Reader Thread ───────────────────────────────────────────────────────
def parse_line(line: str, columns: list) -> dict:
    """Parse tab-delimited line into channel dict."""
    parts = line.strip().split('\t')
    if len(parts) < len(columns):
        return {}
    try:
        return {col: float(parts[i]) for i, col in enumerate(columns)}
    except ValueError:
        return {}


def stdin_reader(buf: TelemetryBuffer, cols: list):
    """Read from stdin pipe (etelemetry output)."""
    header_skipped = False
    for line in sys.stdin:
        if not header_skipped:
            header_skipped = True
            continue   # skip header row
        row = parse_line(line, ["time"] + CHANNELS)
        if row:
            buf.push(row)


def serial_reader(buf: TelemetryBuffer, port: str, baud: int):
    """Read from hardware UART / serial port."""
    if not SERIAL_OK:
        print("[ERROR] pyserial not available")
        return
    ser = serial.Serial(port, baud, timeout=1)
    header_skipped = False
    while True:
        raw = ser.readline().decode(errors='replace')
        if not header_skipped:
            header_skipped = True
            continue
        row = parse_line(raw, ["time"] + CHANNELS)
        if row:
            buf.push(row)


def demo_reader(buf: TelemetryBuffer):
    """Generate synthetic telemetry for demo mode."""
    t = 0.0
    while True:
        t += 0.05
        row = {
            "ax":    0.05 * math.sin(0.3 * t),
            "ay":    0.03 * math.cos(0.2 * t),
            "az":    9.81,
            "gx":    0.02 * math.sin(0.5 * t),
            "gy":    0.01 * math.cos(0.4 * t),
            "gz":    0.005,
            "roll":  15.0 * math.sin(0.15 * t),
            "pitch": 10.0 * math.cos(0.12 * t),
            "yaw":   30.0 * math.sin(0.05 * t),
        }
        buf.push(row)
        time.sleep(0.05)


# ─── PyQt5 Dashboard ─────────────────────────────────────────────────────────
if PYQT_OK:
    class TelemetryDashboard(QtWidgets.QMainWindow):
        def __init__(self, buf: TelemetryBuffer):
            super().__init__()
            self.buf = buf
            self.setWindowTitle("📡 Telemetry Dashboard")
            self.resize(1280, 800)

            tabs = QtWidgets.QTabWidget()
            self.setCentralWidget(tabs)

            # ── Tab 1: Live Graphs ────────────────────────────────────────────
            graph_widget = pg.GraphicsLayoutWidget()
            tabs.addTab(graph_widget, "📊 Sensor Data")

            self.curves = {}
            colors = {
                "ax":"#FF6B6B","ay":"#4ECDC4","az":"#45B7D1",
                "gx":"#96CEB4","gy":"#FFEAA7","gz":"#DDA0DD",
                "roll":"#FF7675","pitch":"#74B9FF","yaw":"#A29BFE"
            }
            row_map = {"ax":0,"ay":0,"az":0, "gx":1,"gy":1,"gz":1,
                       "roll":2,"pitch":2,"yaw":2}
            plots   = {}

            for ch, row in row_map.items():
                if row not in plots:
                    p = graph_widget.addPlot(row=row, col=0)
                    p.showGrid(x=True, y=True, alpha=0.3)
                    p.addLegend()
                    plots[row] = p
                self.curves[ch] = plots[row].plot(
                    pen=pg.mkPen(colors[ch], width=2), name=ch)

            # ── Tab 2: 3D Attitude ────────────────────────────────────────────
            self.view3d = gl.GLViewWidget()
            tabs.addTab(self.view3d, "🧭 3D Attitude")
            self.view3d.opts['distance'] = 40
            grid = gl.GLGridItem()
            grid.scale(2, 2, 1)
            self.view3d.addItem(grid)

            # Craft body: colored axes
            self.craft_x = gl.GLLinePlotItem(
                pos=np.array([[0,0,0],[10,0,0]]), color=(1,0,0,1), width=3)
            self.craft_y = gl.GLLinePlotItem(
                pos=np.array([[0,0,0],[0,10,0]]), color=(0,1,0,1), width=3)
            self.craft_z = gl.GLLinePlotItem(
                pos=np.array([[0,0,0],[0,0,10]]), color=(0,0,1,1), width=3)
            for item in [self.craft_x, self.craft_y, self.craft_z]:
                self.view3d.addItem(item)

            # ── Status bar ────────────────────────────────────────────────────
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("Waiting for data...")

            # ── Timer ─────────────────────────────────────────────────────────
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.update_ui)
            self.timer.start(UPDATE_MS)

        def update_ui(self):
            for ch in CHANNELS:
                arr = self.buf.get_array(ch)
                self.curves[ch].setData(arr)

            lat = self.buf.latest
            roll_r  = math.radians(lat["roll"])
            pitch_r = math.radians(lat["pitch"])
            yaw_r   = math.radians(lat["yaw"])

            # Simple rotation matrix (ZYX Euler)
            cr, sr = math.cos(roll_r),  math.sin(roll_r)
            cp, sp = math.cos(pitch_r), math.sin(pitch_r)
            cy, sy = math.cos(yaw_r),   math.sin(yaw_r)

            def rot(v):
                x = cy*cp*v[0] + (cy*sp*sr - sy*cr)*v[1] + (cy*sp*cr + sy*sr)*v[2]
                y = sy*cp*v[0] + (sy*sp*sr + cy*cr)*v[1] + (sy*sp*cr - cy*sr)*v[2]
                z = -sp*v[0]   + cp*sr*v[1]               + cp*cr*v[2]
                return [x, y, z]

            o = [0, 0, 0]
            self.craft_x.setData(pos=np.array([o, rot([10, 0, 0])]))
            self.craft_y.setData(pos=np.array([o, rot([0, 10, 0])]))
            self.craft_z.setData(pos=np.array([o, rot([0, 0, 10])]))

            self.status_bar.showMessage(
                f"Roll:{lat['roll']:+.1f}°  Pitch:{lat['pitch']:+.1f}°  "
                f"Yaw:{lat['yaw']:+.1f}°  |  "
                f"Ax:{lat['ax']:+.3f}  Ay:{lat['ay']:+.3f}  Az:{lat['az']:+.3f}  |  "
                f"{datetime.now().strftime('%H:%M:%S')}"
            )


# ─── Argument Parsing & Entry ─────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser(description="Telemetry Dashboard")
    ap.add_argument("--demo",  action="store_true", help="run in demo mode")
    ap.add_argument("--port",  default="",          help="serial port (e.g. /dev/ttyUSB0)")
    ap.add_argument("--baud",  type=int, default=115200, help="serial baud rate")
    return ap.parse_args()


def main():
    args = parse_args()
    buf  = TelemetryBuffer(CHANNELS)

    # Start reader thread
    if args.demo:
        t = threading.Thread(target=demo_reader, args=(buf,), daemon=True)
    elif args.port:
        t = threading.Thread(target=serial_reader, args=(buf, args.port, args.baud), daemon=True)
    else:
        t = threading.Thread(target=stdin_reader,  args=(buf, CHANNELS), daemon=True)
    t.start()

    if not PYQT_OK:
        # Headless: just print latest values
        print("Channel values (press Ctrl+C to stop):")
        while True:
            vals = {ch: f"{buf.latest[ch]:+.4f}" for ch in CHANNELS}
            print("\r" + "  ".join(f"{k}:{v}" for k,v in vals.items()), end="", flush=True)
            time.sleep(0.1)
        return

    app = QtWidgets.QApplication(sys.argv)
    dash = TelemetryDashboard(buf)
    dash.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
