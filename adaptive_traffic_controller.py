"""YABATECH Adaptive Traffic Management System - Proof-of-Concept.

Features:
- Real-time livestream capture from phone cameras (IP Webcam HTTP, DroidCam, RTSP,
  USB/virtual webcam) with threaded zero-latency frame reader.
- Fallback/simulation mode with local video loop (--source videos/main_intersection.mp4).
- YOLO11n vehicle detection (cars, buses, trucks, motorcycles).
- Multi-approach Region of Interest (ROI) queue estimation.
- Adaptive traffic signal controller state machine (GREEN -> YELLOW -> ALL-RED).
- Dynamic green time allocation based on vehicle queue counts (gap-out / max-out logic).
- Live HUD displaying traffic light indicators (Red/Yellow/Green), countdown timers,
  queue lengths, and decision diagnostics.
"""

import argparse
import json
import logging
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from traffic_ui import draw_high_visibility_hud

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrafficPoC")

# COCO vehicle classes
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# Vehicle equivalent weights (Passenger Car Units / PCU equivalent)
VEHICLE_WEIGHTS = {
    "car": 1.0,
    "motorcycle": 0.5,
    "bus": 2.5,
    "truck": 2.5,
    "unknown": 1.0,
}


# ============================================================================
# 1. Threaded Zero-Latency Livestream Reader
# ============================================================================
class LiveStreamCapture:
    """Threaded OpenCV video capture that discards stale frames from buffer.

    Essential for IP Webcam / RTSP streams to avoid multi-second buffer lag.
    """

    def __init__(self, source: str, loop: bool = False, reconnect_delay: float = 2.0):
        self.source = source
        self.loop = loop
        self.reconnect_delay = reconnect_delay

        # Parse numeric camera index if applicable
        if isinstance(source, str) and source.isdigit():
            self.cap_source = int(source)
        else:
            self.cap_source = source

        self.cap: Optional[cv2.VideoCapture] = None
        self.latest_frame: Optional[np.ndarray] = None
        self.frame_id = 0  # goes up by one for every new picture, so the main loop never re-counts the same one
        self.last_frame_time = 0.0
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.is_file = Path(source).is_file() if isinstance(source, str) else False
        self.is_network = isinstance(source, str) and "://" in source

        self._open_capture()

    def _store(self, frame: np.ndarray):
        with self.lock:
            self.latest_frame = frame
            self.frame_id += 1
            self.last_frame_time = time.time()

    def _open_capture(self):
        if self.cap is not None:
            self.cap.release()

        logger.info(f"Connecting to video stream: {self.source}")
        if self.is_network:
            # Phone streams: give up after 5 s instead of hanging (OpenCV's default is 30 s+ when the
            # phone is off, asleep or on another Wi-Fi), then the reader thread simply tries again.
            self.cap = cv2.VideoCapture(
                self.cap_source,
                cv2.CAP_FFMPEG,
                [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000],
            )
        else:
            self.cap = cv2.VideoCapture(self.cap_source)

        if not self.is_file:
            # Optimize buffer size for live network streams
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: {self.source}")
            return False

        # Read first frame to verify connection
        ok, frame = self.cap.read()
        if ok and frame is not None:
            self._store(frame)
            logger.info(f"Stream connected successfully. Resolution: {frame.shape[1]}x{frame.shape[0]}")
            return True
        else:
            logger.warning("Connected but failed to retrieve first frame.")
            return False

    def start(self):
        if self.running:
            return self
        self.running = True
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()
        return self

    def _capture_worker(self):
        while self.running:
            if self.cap is None or not self.cap.isOpened():
                time.sleep(self.reconnect_delay)
                self._open_capture()
                continue

            ok, frame = self.cap.read()

            if not ok:
                if self.is_file and self.loop:
                    # Rewind video file in loop mode
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(0.01)
                    continue
                elif self.is_file:
                    logger.info("End of video file reached.")
                    break
                else:
                    logger.warning("Stream frame dropped or disconnected, attempting reconnect...")
                    time.sleep(self.reconnect_delay)
                    self._open_capture()
                    continue

            self._store(frame)

            # In file loop mode, throttle to avoid burning 100% CPU on frame grabbing
            if self.is_file:
                time.sleep(0.02)
            else:
                time.sleep(0.002)

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        with self.lock:
            if self.latest_frame is None:
                return False, None
            return True, self.latest_frame.copy()

    def read_latest(self) -> Tuple[Optional[np.ndarray], int, float]:
        """Newest frame (a copy), its number, and how many seconds ago it arrived."""
        with self.lock:
            if self.latest_frame is None:
                return None, 0, float("inf")
            return self.latest_frame.copy(), self.frame_id, time.time() - self.last_frame_time

    def release(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        logger.info("Video capture released.")


# ============================================================================
# 2. Approach Region of Interest (ROI) Manager
# ============================================================================
class ApproachZone:
    def __init__(self, name: str, polygon_norm: List[Tuple[float, float]], color: Tuple[int, int, int]):
        self.name = name
        self.polygon_norm = polygon_norm  # Normalized [0..1] coordinates
        self.color = color

    def get_pixel_polygon(self, width: int, height: int) -> np.ndarray:
        points = [[int(x * width), int(y * height)] for x, y in self.polygon_norm]
        return np.array(points, dtype=np.int32)

    def contains_point(self, point: Tuple[int, int], width: int, height: int) -> bool:
        poly = self.get_pixel_polygon(width, height)
        # cv2.pointPolygonTest returns > 0 inside, == 0 on edge, < 0 outside
        return cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), False) >= 0


def load_or_create_approach_zones(config_path: Path, frame_w: int, frame_h: int) -> List[ApproachZone]:
    """Load approach ROIs from JSON or generate sensible default dual-approach zones."""
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            zones = []
            colors = [(0, 165, 255), (255, 100, 0), (0, 200, 200), (200, 0, 255)]
            for i, item in enumerate(data.get("approaches", [])):
                color = colors[i % len(colors)]
                zones.append(ApproachZone(item["name"], item["polygon"], color))
            if zones:
                logger.info(f"Loaded {len(zones)} approach zones from {config_path}")
                return zones
        except Exception as e:
            logger.warning(f"Could not parse {config_path}: {e}. Creating default zones.")

    # Default two-approach setup for Yabatech front gate intersection:
    # Approach 1: Hussey Road (Traffic to/from Higher College Rd & Jibowu Pedestrian Bridge junction)
    # Approach 2: Gate & WAEC / Military Hospital / FSTC direction
    default_zones = [
        ApproachZone(
            name="Hussey Rd (Jibowu/College)",
            polygon_norm=[(0.05, 0.45), (0.48, 0.45), (0.48, 0.95), (0.05, 0.95)],
            color=(0, 180, 255),  # Orange-yellow
        ),
        ApproachZone(
            name="Gate & FSTC/WAEC",
            polygon_norm=[(0.52, 0.45), (0.95, 0.45), (0.95, 0.95), (0.52, 0.95)],
            color=(255, 140, 0),  # Sky blue
        ),
    ]

    save_approach_zones(config_path, default_zones)
    return default_zones


def save_approach_zones(config_path: Path, zones: List[ApproachZone]):
    data = {
        "description": "Normalized coordinates (0.0 to 1.0) for intersection approach zones",
        "approaches": [{"name": z.name, "polygon": z.polygon_norm} for z in zones],
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info(f"Saved approach zones configuration to {config_path}")


def interactive_roi_setup(first_frame: np.ndarray, config_path: Path) -> List[ApproachZone]:
    """Allows user to click 4 points to define polygons for each approach."""
    h, w = first_frame.shape[:2]
    shown = first_frame.copy()
    scale = min(1100 / w, 750 / h, 1.0)
    disp_w, disp_h = int(w * scale), int(h * scale)
    shown = cv2.resize(shown, (disp_w, disp_h))

    print("\n" + "=" * 60)
    print("INTERACTIVE APPROACH ROI SETUP")
    print("Click 4 corners to define an approach queue zone.")
    print("Press ENTER to accept the current approach, R to reset, ESC to exit.")
    print("=" * 60)

    try:
        num_approaches = int(input("How many approaches does this camera view cover? (typically 2): ").strip() or "2")
    except ValueError:
        num_approaches = 2

    zones = []
    colors = [(0, 180, 255), (255, 140, 0), (0, 220, 100), (200, 50, 255)]

    for idx in range(num_approaches):
        pts = []
        name = input(f"\nEnter name for Approach {idx + 1} (e.g. 'Main Road' or 'Yabatech Gate'): ").strip()
        if not name:
            name = f"Approach {idx + 1}"

        window_name = f"Define {name} (Click 4 points)"

        def mouse_cb(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(pts) < 4:
                pts.append((int(x / scale), int(y / scale)))

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, mouse_cb)

        while True:
            canvas = shown.copy()
            cv2.putText(
                canvas,
                f"Setting: {name} ({len(pts)}/4 points) | ENTER=accept | R=redraw",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

            # Draw clicked points and lines
            scaled_pts = [(int(px * scale), int(py * scale)) for px, py in pts]
            for p in scaled_pts:
                cv2.circle(canvas, p, 6, (0, 0, 255), -1)

            if len(scaled_pts) > 1:
                cv2.polylines(canvas, [np.array(scaled_pts)], isClosed=(len(scaled_pts) == 4), color=(0, 255, 0), thickness=2)

            cv2.imshow(window_name, canvas)
            key = cv2.waitKey(30) & 0xFF
            if key in (13, 10) and len(pts) >= 3:
                break
            elif key in (ord("r"), ord("R")):
                pts.clear()
            elif key == 27:
                cv2.destroyWindow(window_name)
                sys.exit(0)

        cv2.destroyWindow(window_name)
        norm_pts = [(p[0] / w, p[1] / h) for p in pts]
        color = colors[idx % len(colors)]
        zones.append(ApproachZone(name, norm_pts, color))
        print(f"-> Saved {name}")

    save_approach_zones(config_path, zones)
    return zones


# ============================================================================
# 3. Adaptive Traffic Signal Controller State Machine
# ============================================================================
class SignalState:
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ALL_RED = "ALL_RED"


class AdaptiveTrafficController:
    """Adaptive signal controller that dynamically allocates green durations

    based on instantaneous vehicle queue counts on each approach.
    """

    def __init__(
        self,
        approaches: List[ApproachZone],
        min_green: float = 8.0,
        max_green: float = 35.0,
        yellow_duration: float = 3.0,
        all_red_duration: float = 2.0,
        time_per_vehicle: float = 2.0,
    ):
        self.approaches = approaches
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_duration = yellow_duration
        self.all_red_duration = all_red_duration
        self.time_per_vehicle = time_per_vehicle

        self.num_approaches = len(approaches)
        self.active_index = 0  # Index of approach that currently has or next gets GREEN
        self.state = SignalState.GREEN

        # Timing tracking
        self.state_start_time = time.time()
        self.current_allocated_green = self.min_green
        self.decision_reason = "Initial Startup Phase"

    def update(self, queue_counts: Dict[str, int]) -> Dict[str, any]:
        """Update controller clock and evaluate adaptive light transitions.

        Returns status dict for HUD visualization.
        """
        now = time.time()
        elapsed = now - self.state_start_time
        active_approach = self.approaches[self.active_index].name
        active_queue = queue_counts.get(active_approach, 0)

        if self.state == SignalState.GREEN:
            remaining = max(0.0, self.current_allocated_green - elapsed)

            # GAP-OUT / EARLY EXTENSION LOGIC:
            # If minimum green has elapsed AND active queue has fully cleared (0 cars)
            # while another approach is waiting with cars, switch early to yellow.
            other_queues = [queue_counts.get(app.name, 0) for i, app in enumerate(self.approaches) if i != self.active_index]
            has_waiting_traffic = any(q > 0 for q in other_queues)

            if elapsed >= self.min_green and active_queue == 0 and has_waiting_traffic:
                self._transition_to(SignalState.YELLOW)
                self.decision_reason = f"{active_approach} cleared early (queue=0) -> switching"
                remaining = self.yellow_duration
            elif elapsed >= self.current_allocated_green:
                self._transition_to(SignalState.YELLOW)
                self.decision_reason = f"Allocated green ({self.current_allocated_green:.1f}s) expired"
                remaining = self.yellow_duration

        elif self.state == SignalState.YELLOW:
            remaining = max(0.0, self.yellow_duration - elapsed)
            if elapsed >= self.yellow_duration:
                self._transition_to(SignalState.ALL_RED)
                remaining = self.all_red_duration

        elif self.state == SignalState.ALL_RED:
            remaining = max(0.0, self.all_red_duration - elapsed)
            if elapsed >= self.all_red_duration:
                # Select next approach to receive GREEN
                self._select_next_phase(queue_counts)
                self._transition_to(SignalState.GREEN)
                remaining = self.current_allocated_green

        # Build signal display map for each approach
        signals = {}
        for i, app in enumerate(self.approaches):
            if i == self.active_index:
                signals[app.name] = self.state
            else:
                signals[app.name] = SignalState.ALL_RED if self.state == SignalState.ALL_RED else "RED"

        return {
            "state": self.state,
            "active_approach": active_approach,
            "remaining_time": remaining,
            "allocated_time": (
                self.current_allocated_green
                if self.state == SignalState.GREEN
                else (self.yellow_duration if self.state == SignalState.YELLOW else self.all_red_duration)
            ),
            "signals": signals,
            "reason": self.decision_reason,
        }

    def _select_next_phase(self, queue_counts: Dict[str, int]):
        """Adaptive decision: Next approach is chosen based on highest queue, or round-robin."""
        if self.num_approaches <= 1:
            self.active_index = 0
            target_queue = queue_counts.get(self.approaches[0].name, 0)
        else:
            # Round-robin next candidate by default
            next_index = (self.active_index + 1) % self.num_approaches

            # If the next candidate has 0 cars, but another approach has cars, prioritize the one with cars!
            best_idx = next_index
            max_q = queue_counts.get(self.approaches[next_index].name, 0)

            for i in range(self.num_approaches):
                q = queue_counts.get(self.approaches[i].name, 0)
                if q > max_q:
                    max_q = q
                    best_idx = i

            self.active_index = best_idx
            target_queue = max_q

        # Dynamically calculate green time based on the detected queue
        # T_green = min_green + (cars * time_per_car), bounded by max_green
        calculated_time = self.min_green + (target_queue * self.time_per_vehicle)
        self.current_allocated_green = float(np.clip(calculated_time, self.min_green, self.max_green))

        app_name = self.approaches[self.active_index].name
        self.decision_reason = (
            f"Assigned {self.current_allocated_green:.0f}s green to {app_name} " f"(detected {target_queue} waiting vehicles)"
        )
        logger.info(self.decision_reason)

    def _transition_to(self, new_state: str):
        self.state = new_state
        self.state_start_time = time.time()


# ============================================================================
# 4. HUD / Visual Overlay Rendering
# ============================================================================
def draw_hud(
    frame: np.ndarray,
    approaches: List[ApproachZone],
    queue_counts: Dict[str, int],
    controller_info: Dict[str, any],
    fps: float,
) -> np.ndarray:
    """Draw traffic signal lights, countdown timers, and system status on the frame."""
    h, w = frame.shape[:2]
    canvas = frame.copy()

    # 1. Draw Approach ROI polygons and queue counts
    for app in approaches:
        poly = app.get_pixel_polygon(w, h)
        overlay = canvas.copy()
        cv2.fillPoly(overlay, [poly], app.color)
        # Transparent fill
        cv2.addWeighted(overlay, 0.20, canvas, 0.80, 0, canvas)
        # Solid border
        cv2.polylines(canvas, [poly], isClosed=True, color=app.color, thickness=2)

        # Label ROI with current queue count
        centroid = np.mean(poly, axis=0).astype(int)
        count = queue_counts.get(app.name, 0)
        label = f"{app.name}: {count} vehicles"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.rectangle(
            canvas, (centroid[0] - 10, centroid[1] - lh - 10), (centroid[0] + lw + 10, centroid[1] + 10), (20, 20, 20), -1
        )
        cv2.putText(canvas, label, (centroid[0], centroid[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    # 2. Draw Top Control Panel Banner
    cv2.rectangle(canvas, (0, 0), (w, 54), (15, 15, 15), -1)
    title = f"YABATECH Adaptive Traffic Control PoC | Live Stream ({fps:.1f} FPS)"
    cv2.putText(canvas, title, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

    reason = f"Decision: {controller_info['reason']}"
    cv2.putText(canvas, reason, (15, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1)

    # 3. Draw Traffic Signal Heads for each approach (Top-Right / Dashboard Card)
    signals = controller_info["signals"]
    card_w = 260
    card_h = 110
    start_x = w - card_w - 15
    start_y = 65

    for i, app in enumerate(approaches):
        y = start_y + i * (card_h + 12)
        signal_state = signals.get(app.name, "RED")

        # Background card
        cv2.rectangle(canvas, (start_x, y), (start_x + card_w, y + card_h), (25, 25, 25), -1)
        border_col = (0, 255, 0) if signal_state == "GREEN" else ((0, 255, 255) if signal_state == "YELLOW" else (70, 70, 70))
        cv2.rectangle(canvas, (start_x, y), (start_x + card_w, y + card_h), border_col, 2)

        # Approach title
        cv2.putText(canvas, app.name, (start_x + 12, y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        # Traffic Light Graphic (3 circles: Red, Yellow, Green)
        light_box_x = start_x + 15
        light_box_y = y + 38
        cv2.rectangle(canvas, (light_box_x, light_box_y), (light_box_x + 95, light_box_y + 36), (10, 10, 10), -1)

        # Lamp positions
        r_pos = (light_box_x + 18, light_box_y + 18)
        y_pos = (light_box_x + 48, light_box_y + 18)
        g_pos = (light_box_x + 78, light_box_y + 18)

        # Lamp colors (bright when active, dimmed when off)
        is_red = signal_state in ("RED", SignalState.ALL_RED)
        is_yellow = signal_state == SignalState.YELLOW
        is_green = signal_state == SignalState.GREEN

        r_col = (0, 0, 255) if is_red else (0, 0, 60)
        y_col = (0, 255, 255) if is_yellow else (0, 60, 60)
        g_col = (0, 255, 0) if is_green else (0, 60, 0)

        cv2.circle(canvas, r_pos, 11, r_col, -1)
        cv2.circle(canvas, y_pos, 11, y_col, -1)
        cv2.circle(canvas, g_pos, 11, g_col, -1)

        # Status text & countdown
        if app.name == controller_info["active_approach"]:
            rem = controller_info["remaining_time"]
            timer_text = f"{signal_state}: {rem:.1f}s"
            timer_color = (0, 255, 0) if is_green else ((0, 255, 255) if is_yellow else (0, 0, 255))
        else:
            timer_text = "RED"
            timer_color = (0, 0, 255)

        cv2.putText(canvas, timer_text, (start_x + 120, y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.65, timer_color, 2)

        # Queue length info
        q_text = f"Queue: {queue_counts.get(app.name, 0)} vehicles"
        cv2.putText(canvas, q_text, (start_x + 15, y + 95), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (180, 180, 180), 1)

    return canvas


# ============================================================================
# 5. Main Loop & CLI
# ============================================================================
def parse_arguments():
    parser = argparse.ArgumentParser(description="Adaptive Traffic Management System for Yabatech Front Gate")
    parser.add_argument(
        "--source",
        default="http://192.168.1.100:8080/video",
        help="Stream source: Phone camera IP (e.g. http://192.168.x.x:8080/video), webcam index (0), or video file",
    )
    parser.add_argument(
        "--loop", action="store_true", help="Continuously loop the video source if using a recorded video file"
    )
    parser.add_argument("--setup", action="store_true", help="Interactive polygon setup for approach zones")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO vehicle detection confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image resolution")
    parser.add_argument("--skip", type=int, default=1, help="Process inference every Nth frame for CPU speedup")
    parser.add_argument("--min-green", type=float, default=8.0, help="Minimum green light time in seconds")
    parser.add_argument("--max-green", type=float, default=35.0, help="Maximum green light time in seconds")
    parser.add_argument("--yellow", type=float, default=3.0, help="Yellow light duration in seconds")
    parser.add_argument("--all-red", type=float, default=2.0, help="All-red clearance duration in seconds")
    parser.add_argument(
        "--time-per-car", type=float, default=2.0, help="Additional green seconds allocated per detected vehicle"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run without opening a GUI window (for background/headless testing)"
    )
    parser.add_argument(
        "--max-frames", type=int, default=0, help="Stop after processing N frames (0 for unlimited)"
    )
    parser.add_argument(
        "--rotate",
        type=int,
        default=0,
        choices=[0, 90, 180, 270],
        help="Turn the picture clockwise by this many degrees. Use it when the phone's stream arrives sideways: "
        "YOLO misses most vehicles in a sideways picture",
    )
    parser.add_argument(
        "--stale-after",
        type=float,
        default=3.0,
        help="Seconds without a new picture before the camera counts as lost (queues are then ignored and the "
        "lights fall back to fixed minimum-green timing)",
    )
    return parser.parse_args()


ROTATIONS = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}


def rotate(frame: np.ndarray, degrees: int) -> np.ndarray:
    return cv2.rotate(frame, ROTATIONS[degrees]) if degrees else frame


def draw_camera_lost(frame: np.ndarray, seconds: float) -> np.ndarray:
    h, w = frame.shape[:2]
    out = (frame * 0.45).astype(np.uint8)  # dim the frozen picture so nobody mistakes it for live video
    scale = max(0.6, min(w / 1100.0, 1.6))
    text = f"CAMERA LOST ({seconds:.0f}s) - reconnecting. Lights on fixed timing."
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.7 * scale, 2)
    y = h // 2
    cv2.rectangle(out, (0, y - th - int(20 * scale)), (w, y + int(20 * scale)), (0, 0, 170), -1)
    cv2.putText(out, text, (max(10, (w - tw) // 2), y), cv2.FONT_HERSHEY_DUPLEX, 0.7 * scale, (255, 255, 255), 2, cv2.LINE_AA)
    return out


def main():
    args = parse_arguments()

    print("\n" + "=" * 65)
    print("   YABATECH FRONT GATE ADAPTIVE TRAFFIC MANAGEMENT PoC")
    print("=" * 65)
    print(f"Target Stream Source : {args.source}")
    print(f"Detection Model      : YOLO11n (COCO vehicle classes)")
    print(f"Timing Parameters    : Min Green={args.min_green}s, Max Green={args.max_green}s, Yellow={args.yellow}s")
    print("=" * 65 + "\n")

    # Start live stream reader thread
    stream = LiveStreamCapture(args.source, loop=args.loop).start()

    # Wait for first frame. A phone stream keeps retrying (Ctrl+C to stop), so the program can be
    # started before the phone app is ready.
    print("Connecting to live stream and awaiting video frames...")
    tips = (
        "\nStill no picture from: " + str(args.source) + "\n"
        "Troubleshooting tips for Phone Camera streaming:\n"
        "1. Android IP Webcam App: Enter URL as: http://<PHONE_IP>:8080/video\n"
        "2. DroidCam App (Android/iPhone): Enter URL as: http://<PHONE_IP>:4747/video\n"
        "3. Both PC and Phone must be connected to the SAME Wi-Fi network.\n"
        "4. Keep the app open with the screen on. Free DroidCam serves ONE viewer at a time:\n"
        "   close any browser tab or other program that is showing the stream.\n"
        "5. Open the same address in a browser on the PC: if no video shows there, the problem is the network.\n"
        "   (Close that tab again afterwards.)\n"
        "6. To test with a local recorded video, run:\n"
        "   python adaptive_traffic_controller.py --source videos/test_clip.mp4 --loop\n"
        "Still trying - press Ctrl+C to stop."
    )
    first_frame = None
    wait_start = time.time()
    tips_shown = False
    try:
        while first_frame is None:
            ok, frame = stream.read()
            if ok and frame is not None:
                first_frame = frame
                break
            waited = time.time() - wait_start
            if not stream.is_network and waited > 5:
                break  # a file or webcam that gives nothing in 5 s will not start giving pictures
            if stream.is_network and waited > 10 and not tips_shown:
                print(tips)
                tips_shown = True
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    if first_frame is None:
        print(f"\n[ERROR] Unable to receive frames from source: {args.source}")
        if not tips_shown:
            print(tips.replace("Still trying - press Ctrl+C to stop.", ""))
        stream.release()
        sys.exit(1)
    first_frame = rotate(first_frame, args.rotate)

    fh, fw = first_frame.shape[:2]
    config_path = Path("outputs/approach_zones.json")

    # Load or configure approach zones
    if args.setup:
        approaches = interactive_roi_setup(first_frame, config_path)
    else:
        approaches = load_or_create_approach_zones(config_path, fw, fh)

    print(f"Active Approaches ({len(approaches)}):")
    for app in approaches:
        print(f"  - {app.name}")

    # Initialize YOLO11n model
    print("\nLoading YOLO11n object detector...")
    model = YOLO("yolo11n.pt")

    # Initialize adaptive signal controller
    controller = AdaptiveTrafficController(
        approaches=approaches,
        min_green=args.min_green,
        max_green=args.max_green,
        yellow_duration=args.yellow,
        all_red_duration=args.all_red,
        time_per_vehicle=args.time_per_car,
    )

    window_title = "YABATECH Adaptive Traffic Management System (PoC)"
    if not args.headless:
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

    frame_counter = 0
    fps_measure_start = time.time()
    fps = 0.0
    latest_boxes = []
    last_frame_id = 0
    camera_lost = False

    print("\n[SYSTEM RUNNING] Press 'q' to quit, 's' to snapshot, 'r' to redraw zones.\n")

    try:
        while True:
            frame, frame_id, age = stream.read_latest()
            if frame is None:
                time.sleep(0.01)
                continue

            # Camera lost = no new picture for a while (phone locked, app closed, Wi-Fi dropped).
            lost_now = not stream.is_file and age > args.stale_after
            if lost_now != camera_lost:
                camera_lost = lost_now
                if camera_lost:
                    logger.warning(f"No new picture for {age:.0f}s - camera lost. Queues ignored until it is back.")
                else:
                    logger.info("Camera is back - live counting resumed.")

            new_frame = frame_id != last_frame_id
            if not new_frame and not camera_lost:
                if stream.is_file and not (stream.thread and stream.thread.is_alive()):
                    print("End of video file reached (use --loop to replay it). Stopping.")
                    break
                time.sleep(0.003)  # no new picture yet: never detect or count the same frame twice
                continue
            frame = rotate(frame, args.rotate)
            h, w = frame.shape[:2]

            if new_frame:
                last_frame_id = frame_id
                frame_counter += 1
                if args.max_frames > 0 and frame_counter >= args.max_frames:
                    print(f"Reached max frames limit ({args.max_frames}). Stopping.")
                    break
            if camera_lost:
                latest_boxes = []  # a frozen picture says nothing about the queues now
                time.sleep(0.05)

            # Run inference periodically according to --skip
            if new_frame and frame_counter % args.skip == 0:
                results = model.predict(
                    frame,
                    imgsz=args.imgsz,
                    conf=args.conf,
                    classes=list(VEHICLE_CLASSES.keys()),
                    device="cpu",
                    verbose=False,
                )[0]

                current_detections = []
                if results.boxes is not None:
                    boxes = results.boxes.xyxy.cpu().numpy()
                    classes = results.boxes.cls.cpu().numpy().astype(int)
                    confs = results.boxes.conf.cpu().numpy()

                    for box, cls_id, conf in zip(boxes, classes, confs):
                        x1, y1, x2, y2 = box
                        vehicle_type = VEHICLE_CLASSES.get(cls_id, "unknown")
                        foot_point = (int((x1 + x2) / 2), int(y2))
                        current_detections.append(
                            {"box": (int(x1), int(y1), int(x2), int(y2)), "type": vehicle_type, "foot": foot_point, "conf": conf}
                        )
                latest_boxes = current_detections

            # Count vehicles currently inside each approach zone
            queue_counts = {app.name: 0 for app in approaches}
            annotated_frame = frame.copy()

            for det in latest_boxes:
                foot = det["foot"]
                assigned_approach = None
                for app in approaches:
                    if app.contains_point(foot, w, h):
                        queue_counts[app.name] += 1
                        assigned_approach = app.name
                        break
                det["assigned"] = assigned_approach

            # Update adaptive traffic light state machine
            ctrl_info = controller.update(queue_counts)

            # Calculate FPS
            if new_frame and frame_counter % 15 == 0:
                elapsed_sec = time.time() - fps_measure_start
                if elapsed_sec > 0:
                    fps = 15.0 / elapsed_sec
                fps_measure_start = time.time()

            # Render live high-visibility HUD overlay
            display_frame = draw_high_visibility_hud(
                frame=frame,
                approaches=approaches,
                queue_counts=queue_counts,
                controller_info=ctrl_info,
                fps=fps,
                detected_boxes=latest_boxes,
                title_prefix="LIVE STREAM",
            )
            if camera_lost:
                display_frame = draw_camera_lost(display_frame, age)

            if not args.headless:
                # Resize for comfortable screen display if video is high resolution
                disp_h, disp_w = display_frame.shape[:2]
                scale = min(1200 / disp_w, 800 / disp_h, 1.0)
                if scale < 1.0:
                    display_frame = cv2.resize(display_frame, (int(disp_w * scale), int(disp_h * scale)))

                cv2.imshow(window_title, display_frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    print("\nTerminating system...")
                    break
                elif key in (ord("s"), ord("S")):
                    snap_path = Path(f"outputs/snapshot_{int(time.time())}.jpg")
                    cv2.imwrite(str(snap_path), display_frame)
                    print(f"Snapshot saved: {snap_path}")
                elif key in (ord("r"), ord("R")):
                    print("\nEntering ROI reconfiguration...")
                    cv2.destroyWindow(window_title)
                    approaches = interactive_roi_setup(frame, config_path)
                    controller.approaches = approaches
                    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
            else:
                if new_frame and frame_counter % 30 == 0:
                    logger.info(
                        f"Frame {frame_counter} | {fps:.1f} FPS | Active: {ctrl_info['active_approach']} ({ctrl_info['state']}) | "
                        f"Remaining: {ctrl_info['remaining_time']:.1f}s | Queues: {queue_counts}"
                    )
                time.sleep(0.01)

    finally:
        stream.release()
        cv2.destroyAllWindows()
        print("System shutdown complete.")


if __name__ == "__main__":
    main()
