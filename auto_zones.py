"""Automatic approach zones for adaptive_traffic_controller.py (--auto-zones).

The zones follow the camera, so nobody has to redraw them when the phone moves.

ViewWatcher
    Keeps the picture the zones were made on (the reference). About once a second it matches ORB
    features between that picture and the live one:
    - same view: nothing to do;
    - nudged, panned or tilted a little: the zones are moved with the picture (homography), so a
      phone that slipped keeps counting the right road;
    - no longer matches for a few seconds: the view has changed, so the roads are learned again.

ZoneLearner
    Watches where vehicles are detected for a while (20 s by default) and turns those positions into
    zones. The positions are split into N groups (k-means on where each vehicle touches the road).
    Each group is wrapped (convex hull of the box bottoms), widened by a margin, and kept on its own
    side of the other groups. Each zone then covers the whole stretch where vehicles were seen on
    that road, not just a hand-drawn patch.

This module only deals in plain polygons (normalised 0..1 points), so it does not import the controller.
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("TrafficPoC")

Zone = Tuple[str, List[Tuple[float, float]]]  # (name, normalised polygon)


# ============================================================================
# Camera view watcher
# ============================================================================
class ViewWatcher:
    SAME = "same"
    SHIFTED = "shifted"
    NO_MATCH = "no-match"

    def __init__(self, reference: np.ndarray, work_width: int = 640):
        self.work_width = work_width
        self.orb = cv2.ORB_create(nfeatures=1500)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.set_reference(reference)

    def _features(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        scale = min(1.0, self.work_width / float(w))
        small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        kps, des = self.orb.detectAndCompute(gray, None)
        return kps, des, scale

    def set_reference(self, frame: np.ndarray):
        self.reference = frame.copy()
        self.ref_size = (frame.shape[1], frame.shape[0])
        self.ref_kps, self.ref_des, self.ref_scale = self._features(frame)

    def compare(self, frame: np.ndarray) -> Tuple[str, Optional[np.ndarray]]:
        """Compare the live picture with the reference.

        Returns (status, H). H maps reference pixels to live pixels and is only given for SHIFTED.
        """
        if (frame.shape[1], frame.shape[0]) != self.ref_size:
            return self.NO_MATCH, None
        if self.ref_des is None or len(self.ref_kps) < 30:
            return self.NO_MATCH, None
        kps, des, scale = self._features(frame)
        if des is None or len(kps) < 30:
            return self.NO_MATCH, None

        # Lowe's ratio test keeps only distinctive matches; moving vehicles are thrown out by RANSAC below.
        good = []
        for pair in self.matcher.knnMatch(self.ref_des, des, k=2):
            if len(pair) == 2 and pair[0].distance < 0.75 * pair[1].distance:
                good.append(pair[0])
        if len(good) < 20:
            return self.NO_MATCH, None

        src = np.float32([self.ref_kps[m.queryIdx].pt for m in good]) / self.ref_scale
        dst = np.float32([kps[m.trainIdx].pt for m in good]) / scale
        # A nudged phone mostly slides, turns or zooms the picture. This 4-parameter model is far steadier
        # than a full perspective fit, whose small errors pile up when the zones follow the camera for long.
        M, mask = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=6.0)
        if M is None or mask is None:
            return self.NO_MATCH, None
        H = np.vstack([M, [0.0, 0.0, 1.0]])
        inliers = int(mask.sum())
        if inliers < 20 or inliers < 0.35 * len(good):
            return self.NO_MATCH, None

        # How far do the picture's corners move? Tiny = same view, huge = a bad fit.
        w, h = self.ref_size
        corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
        moved = cv2.perspectiveTransform(corners, H).reshape(-1, 2) - corners.reshape(-1, 2)
        shift = float(np.linalg.norm(moved, axis=1).max())
        diag = float(np.hypot(w, h))
        if shift > 0.5 * diag:
            return self.NO_MATCH, None
        if shift < 0.015 * diag:
            return self.SAME, None
        return self.SHIFTED, H


# ============================================================================
# Road learner
# ============================================================================
class ZoneLearner:
    def __init__(self, n_zones: int = 2, seconds: float = 20.0, min_spots: int = 12, cell: int = 16):
        self.n_zones = max(1, n_zones)
        self.seconds = seconds
        self.min_spots = min_spots
        self.cell = cell  # positions are pooled on a grid so a parked car does not outweigh moving traffic
        self.start = time.time()
        self.spots = {}  # grid cell -> (foot point, bottom-of-box corner points)

    def add(self, detections: List[dict]):
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            fx, fy = det["foot"]
            key = (fx // self.cell, fy // self.cell)
            if key in self.spots:
                continue
            lift = 0.25 * (y2 - y1)  # include the lower quarter of the vehicle, where it sits on the road
            corners = [(x1, y2), (x2, y2), (x1, y2 - lift), (x2, y2 - lift)]
            self.spots[key] = ((fx, fy), corners)

    def warp(self, H: np.ndarray):
        """The camera moved a little while learning: move the collected spots with the picture."""
        old = list(self.spots.values())
        self.spots = {}
        for foot, corners in old:
            pts = np.float32([foot] + list(corners)).reshape(-1, 1, 2)
            moved = cv2.perspectiveTransform(pts, H).reshape(-1, 2)
            f = (int(moved[0][0]), int(moved[0][1]))
            key = (f[0] // self.cell, f[1] // self.cell)
            if key not in self.spots:
                self.spots[key] = (f, [(float(x), float(y)) for x, y in moved[1:]])

    @property
    def elapsed(self) -> float:
        return time.time() - self.start

    def ready(self) -> bool:
        return self.elapsed >= self.seconds and len(self.spots) >= max(self.min_spots, self.n_zones)

    def status_text(self) -> str:
        left = max(0, self.seconds - self.elapsed)
        if left > 0:
            return f"LEARNING THE ROADS - watching where vehicles drive ({left:.0f}s, {len(self.spots)} spots)"
        return f"LEARNING THE ROADS - waiting for more vehicles ({len(self.spots)}/{self.min_spots} spots)"

    def foot_points(self) -> List[Tuple[int, int]]:
        return [foot for foot, _ in self.spots.values()]

    def build(self, width: int, height: int, margin: float = 0.06) -> List[Zone]:
        feet = np.float32([foot for foot, _ in self.spots.values()])
        corner_sets = [corners for _, corners in self.spots.values()]
        k = min(self.n_zones, len(feet))
        if k <= 1:
            labels = np.zeros(len(feet), dtype=int)
            centres = feet.mean(axis=0, keepdims=True)
        else:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5)
            _, labels, centres = cv2.kmeans(feet, k, None, criteria, 8, cv2.KMEANS_PP_CENTERS)
            labels = labels.ravel()

        # Work on a quarter-size grid: wrap each group, widen it, then split any overlap by nearest group.
        s = 0.25
        gw, gh = int(width * s), int(height * s)
        yy, xx = np.mgrid[0:gh, 0:gw].astype(np.float32)
        dists = np.stack([(xx - cx * s) ** 2 + (yy - cy * s) ** 2 for cx, cy in centres])
        nearest = dists.argmin(axis=0)
        pad = max(3, int(margin * width * s))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1))

        zones = []
        for i in range(len(centres)):
            pts = [p for j, corners in enumerate(corner_sets) if labels[j] == i for p in corners]
            if len(pts) < 3:
                continue
            hull = cv2.convexHull(np.int32([[x * s, y * s] for x, y in pts]))
            mask = np.zeros((gh, gw), np.uint8)
            cv2.fillConvexPoly(mask, hull, 255)
            mask = cv2.dilate(mask, kernel)
            mask[nearest != i] = 0
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            c = max(contours, key=cv2.contourArea)
            c = cv2.approxPolyDP(c, 0.01 * cv2.arcLength(c, True), True).reshape(-1, 2)
            if len(c) < 3:
                continue
            poly = [(min(1.0, max(0.0, x / gw)), min(1.0, max(0.0, y / gh))) for x, y in c]
            zones.append((float(np.mean([p[0] for p in poly])), poly))

        zones.sort(key=lambda z: z[0])  # name them left to right
        names = {1: ["Road"], 2: ["Left road", "Right road"], 3: ["Left road", "Middle road", "Right road"]}
        labels_for = names.get(len(zones), [f"Road {i + 1}" for i in range(len(zones))])
        return [(labels_for[i], poly) for i, (_, poly) in enumerate(zones)]


# ============================================================================
# The piece the controller talks to
# ============================================================================
def warp_zones(zones: List[Zone], H: np.ndarray, width: int, height: int) -> List[Zone]:
    """Move zones with the picture. Points may leave the frame (kept as-is so the shape survives)."""
    out = []
    for name, poly in zones:
        pts = np.float32([[x * width, y * height] for x, y in poly]).reshape(-1, 1, 2)
        moved = cv2.perspectiveTransform(pts, H).reshape(-1, 2)
        out.append((name, [(min(1.5, max(-0.5, float(x) / width)), min(1.5, max(-0.5, float(y) / height)))
                           for x, y in moved]))
    return out


def visible_fraction(poly: List[Tuple[float, float]], width: int, height: int) -> float:
    """How much of a zone is still inside the picture (0..1)."""
    s = 0.25
    pts = np.int32([[x * width * s, y * height * s] for x, y in poly])
    full = abs(cv2.contourArea(pts.astype(np.float32)))
    if full < 1:
        return 0.0
    mask = np.zeros((int(height * s), int(width * s)), np.uint8)
    cv2.fillPoly(mask, [pts], 255)  # fillPoly only paints what lies inside the picture
    return min(1.0, cv2.countNonZero(mask) / full)


class AutoZones:
    """Keeps the approach zones matched to what the camera sees.

    Call update() with every new frame and its detections. It returns an event when the zones change:
    "moved" (camera nudged, zones shifted with it), "relearning" (view changed, learning started) or
    "learned" (new zones ready). The current zones are in .zones; while .learning is True there are
    none, and the controller should ignore queues.
    """

    def __init__(self, first_frame: np.ndarray, config_path: Path, n_zones: int = 2, learn_seconds: float = 20.0,
                 check_every: float = 1.0, relearn_after: float = 4.0, initial: Optional[List[Zone]] = None):
        self.config_path = Path(config_path)
        self.ref_path = self.config_path.with_name(self.config_path.stem + "_ref.jpg")
        self.n_zones = n_zones
        self.learn_seconds = learn_seconds
        self.check_every = check_every
        self.relearn_after = relearn_after
        self.height, self.width = first_frame.shape[:2]
        self.zones: List[Zone] = []
        self.learner: Optional[ZoneLearner] = None
        self.last_check = 0.0
        self.last_move_log = 0.0
        self.no_match_since: Optional[float] = None
        self.watcher = ViewWatcher(first_frame)

        saved = None if initial else self._load_saved()
        if initial:
            # Zones just drawn by hand (--setup) on this very picture: keep them and follow the camera from here.
            self.zones = list(initial)
            self._save(first_frame)
            logger.info("Auto zones: using the road areas you drew; they will follow the camera from now on.")
        elif saved:
            zones, ref = saved
            self.watcher = ViewWatcher(ref)
            status, H = self.watcher.compare(first_frame)
            if status == ViewWatcher.SAME:
                self.zones = zones
                logger.info("Auto zones: same camera view as last time - reusing the saved road areas.")
            elif status == ViewWatcher.SHIFTED:
                self.zones = warp_zones(zones, H, self.width, self.height)
                self.watcher.set_reference(first_frame)
                self._save(first_frame)
                logger.info("Auto zones: camera moved a little since last time - road areas shifted to match.")
        if not self.zones:
            self._start_learning(first_frame, "no saved road areas for this camera view")

    @property
    def learning(self) -> bool:
        return self.learner is not None

    # -- saving -------------------------------------------------------------
    def _load_saved(self):
        if not (self.config_path.exists() and self.ref_path.exists()):
            return None
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            zones = [(a["name"], [tuple(p) for p in a["polygon"]]) for a in data.get("approaches", [])]
            ref = cv2.imread(str(self.ref_path))
            if zones and ref is not None:
                return zones, ref
        except Exception as e:  # a broken file just means we learn again
            logger.warning(f"Auto zones: could not read saved zones ({e}).")
        return None

    def _save(self, frame: np.ndarray):
        data = {
            "description": "Normalized coordinates (0.0 to 1.0) for intersection approach zones",
            "approaches": [{"name": n, "polygon": [list(p) for p in poly]} for n, poly in self.zones],
        }
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        cv2.imwrite(str(self.ref_path), frame)

    # -- running ------------------------------------------------------------
    def relearn(self, frame: np.ndarray, why: str = "R pressed"):
        self._start_learning(frame, why)

    def _start_learning(self, frame: np.ndarray, why: str):
        self.zones = []
        self.learner = ZoneLearner(self.n_zones, self.learn_seconds)
        self.watcher.set_reference(frame)
        self.no_match_since = None
        logger.info(f"Auto zones: learning the roads ({why}). Lights run on fixed timing meanwhile.")

    def update(self, frame: np.ndarray, detections: List[dict]) -> Optional[str]:
        now = time.time()
        if self.learning:
            self.learner.add(detections)

        if now - self.last_check >= self.check_every:
            self.last_check = now
            status, H = self.watcher.compare(frame)

            if status == ViewWatcher.SHIFTED:
                # Nudged or hand-held phone: move everything with the picture and carry on.
                self.no_match_since = None
                self.watcher.set_reference(frame)
                if self.learning:
                    self.learner.warp(H)
                else:
                    self.zones = warp_zones(self.zones, H, self.width, self.height)
                    if any(visible_fraction(p, self.width, self.height) < 0.35 for _, p in self.zones):
                        self._start_learning(frame, "a road moved out of the picture")
                        return "relearning"
                    self._save(frame)
                    if now - self.last_move_log > 10:  # a hand-held phone moves all the time; don't flood the log
                        logger.info("Auto zones: camera moved - road areas shifted to follow it.")
                        self.last_move_log = now
                    return "moved"
            elif status == ViewWatcher.NO_MATCH:
                # Could be a bus filling the picture for a moment, so only a lasting mismatch counts.
                if self.no_match_since is None:
                    self.no_match_since = now
                elif now - self.no_match_since >= self.relearn_after:
                    self._start_learning(frame, "camera view changed")
                    return "relearning"
            else:
                self.no_match_since = None

        if self.learning and self.learner.ready():
            zones = self.learner.build(self.width, self.height)
            if zones:
                spots = len(self.learner.spots)
                self.zones = zones
                self.learner = None
                self.watcher.set_reference(frame)
                self._save(frame)
                logger.info(f"Auto zones: learned {len(zones)} road(s) from {spots} vehicle spots: "
                            + ", ".join(n for n, _ in zones))
                return "learned"
            self.learner.start = now  # too scattered to make a zone yet: keep watching for another round
        return None

    def draw_learning(self, frame: np.ndarray) -> np.ndarray:
        """Dots where vehicles have been seen, plus a banner, while learning."""
        if not self.learning:
            return frame
        out = frame.copy()
        for x, y in self.learner.foot_points():
            cv2.circle(out, (int(x), int(y)), 5, (0, 255, 255), -1)
        h, w = out.shape[:2]
        scale = max(0.6, min(w / 1100.0, 1.6))
        text = self.learner.status_text()
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.6 * scale, 2)
        y = h - int(30 * scale)
        cv2.rectangle(out, (0, y - th - int(14 * scale)), (w, y + int(14 * scale)), (120, 60, 0), -1)
        cv2.putText(out, text, (max(10, (w - tw) // 2), y), cv2.FONT_HERSHEY_DUPLEX, 0.6 * scale, (255, 255, 255),
                    2, cv2.LINE_AA)
        return out
