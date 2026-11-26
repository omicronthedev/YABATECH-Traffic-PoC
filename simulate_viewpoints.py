"""Simulation Runner for YABATECH Adaptive Traffic Management System.

Runs adaptive signal control simulations across multiple video viewpoints,
evaluates queue counts, dynamically allocates green/yellow/red signal times,
and exports annotated simulation videos and performance statistics.
"""

import argparse
import csv
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import os
from pathlib import Path
os.environ["YOLO_CONFIG_DIR"] = str((Path(__file__).resolve().parent / ".ultralytics").resolve())

import cv2
import numpy as np
from ultralytics import YOLO

from traffic_ui import draw_high_visibility_hud

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrafficSimulation")

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


class ViewpointSimulator:
    def __init__(
        self,
        video_path: Path,
        output_dir: Path,
        model: YOLO,
        skip_frames: int = 2,
        imgsz: int = 640,
        conf: float = 0.25,
        min_green: float = 8.0,
        max_green: float = 30.0,
        yellow: float = 3.0,
        all_red: float = 2.0,
        time_per_car: float = 2.0,
        max_duration_sec: Optional[float] = None,
    ):
        self.video_path = video_path
        self.output_dir = output_dir
        self.model = model
        self.skip_frames = max(1, skip_frames)
        self.imgsz = imgsz
        self.conf = conf
        self.min_green = min_green
        self.max_green = max_green
        self.yellow = yellow
        self.all_red = all_red
        self.time_per_car = time_per_car
        self.max_duration_sec = max_duration_sec
        if len(model.names) == 5 and "keke" in model.names.values():
            self.active_classes = {k: v for k, v in model.names.items()}
        else:
            self.active_classes = {k: v for k, v in model.names.items() if v in ["car", "motorcycle", "bus", "truck", "keke"]}
            if not self.active_classes:
                self.active_classes = VEHICLE_CLASSES

    def get_approach_rois(self, width: int, height: int) -> List[Dict]:
        """Generate balanced approach zones suited to the video aspect ratio."""
        is_portrait = height > width
        if is_portrait:
            # Upper approach (inbound/far) vs Lower approach (outbound/near gate)
            return [
                {
                    "name": "Hussey Rd (Inbound)",
                    "poly": np.array(
                        [
                            [int(0.05 * width), int(0.20 * height)],
                            [int(0.95 * width), int(0.20 * height)],
                            [int(0.95 * width), int(0.55 * height)],
                            [int(0.05 * width), int(0.55 * height)],
                        ],
                        dtype=np.int32,
                    ),
                    "color": (0, 180, 255),  # Orange-yellow
                },
                {
                    "name": "Gate Approach (Outbound)",
                    "poly": np.array(
                        [
                            [int(0.05 * width), int(0.58 * height)],
                            [int(0.95 * width), int(0.58 * height)],
                            [int(0.95 * width), int(0.95 * height)],
                            [int(0.05 * width), int(0.95 * height)],
                        ],
                        dtype=np.int32,
                    ),
                    "color": (255, 140, 0),  # Sky blue
                },
            ]
        else:
            # Landscape: WAEC/FSTC Approach vs College/Jibowu Gate Approach
            return [
                {
                    "name": "Hussey Rd (WAEC/FSTC)",
                    "poly": np.array(
                        [
                            [int(0.05 * width), int(0.35 * height)],
                            [int(0.48 * width), int(0.35 * height)],
                            [int(0.48 * width), int(0.95 * height)],
                            [int(0.05 * width), int(0.95 * height)],
                        ],
                        dtype=np.int32,
                    ),
                    "color": (0, 180, 255),
                },
                {
                    "name": "Hussey Rd (College/Jibowu)",
                    "poly": np.array(
                        [
                            [int(0.52 * width), int(0.35 * height)],
                            [int(0.95 * width), int(0.35 * height)],
                            [int(0.95 * width), int(0.95 * height)],
                            [int(0.52 * width), int(0.95 * height)],
                        ],
                        dtype=np.int32,
                    ),
                    "color": (255, 140, 0),
                },
            ]

    def run(self, save_video: bool = True) -> Dict:
        logger.info(f"--- Starting Simulation on: {self.video_path.name} ---")
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open {self.video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        approaches = self.get_approach_rois(width, height)
        out_video_path = self.output_dir / f"sim_{self.video_path.stem}.mp4"
        stats_csv_path = self.output_dir / f"sim_{self.video_path.stem}_stats.csv"

        writer = None
        if save_video:
            out_fps = fps / self.skip_frames
            writer = cv2.VideoWriter(str(out_video_path), cv2.VideoWriter_fourcc(*"mp4v"), out_fps, (width, height))

        # Simulation Controller State
        active_idx = 0
        state = "GREEN"
        allocated_green = self.min_green
        sim_time = 0.0  # Simulated clock in seconds based on video FPS
        state_start_sim_time = 0.0
        decision_reason = "Simulation initialized"

        cycle_history = []
        frame_idx = 0
        processed_count = 0
        queue_records = []
        start_real_time = time.time()

        last_progress_log = 0.0

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            sim_time = frame_idx / fps
            if self.max_duration_sec and sim_time >= self.max_duration_sec:
                logger.info(f"Target duration of {self.max_duration_sec:.1f}s reached ({sim_time:.1f}s). Concluding simulation.")
                break

            if sim_time - last_progress_log >= 30.0:
                elapsed_real = time.time() - start_real_time
                fps_real = processed_count / max(1.0, elapsed_real)
                target_str = f"/{self.max_duration_sec:.0f}s" if self.max_duration_sec else ""
                logger.info(f"Progress: {sim_time:.0f}s{target_str} simulated ({processed_count} frames, {fps_real:.1f} proc FPS)")
                last_progress_log = sim_time

            if frame_idx % self.skip_frames == 0:
                # YOLO vehicle detection
                res = self.model.predict(
                    frame,
                    imgsz=self.imgsz,
                    conf=self.conf,
                    classes=list(self.active_classes.keys()),
                    device="cpu",
                    verbose=False,
                )[0]

                queue_counts = {app["name"]: 0 for app in approaches}
                detected_boxes = []

                if res.boxes is not None:
                    boxes = res.boxes.xyxy.cpu().numpy()
                    cls_ids = res.boxes.cls.cpu().numpy().astype(int)
                    for box, cls_id in zip(boxes, cls_ids):
                        x1, y1, x2, y2 = box
                        v_name = self.active_classes.get(cls_id, "car")
                        foot = (int((x1 + x2) / 2), int(y2))

                        assigned = None
                        for app in approaches:
                            if cv2.pointPolygonTest(app["poly"], foot, False) >= 0:
                                queue_counts[app["name"]] += 1
                                assigned = app["name"]
                                break

                        detected_boxes.append((int(x1), int(y1), int(x2), int(y2), v_name, foot, assigned))

                # --- Adaptive Traffic Signal Controller Logic ---
                elapsed_in_state = sim_time - state_start_sim_time
                active_approach_name = approaches[active_idx]["name"]
                active_q = queue_counts.get(active_approach_name, 0)

                # State Transitions
                if state == "GREEN":
                    rem_time = max(0.0, allocated_green - elapsed_in_state)
                    # Check gap-out: queue cleared early
                    other_q = [queue_counts[a["name"]] for i, a in enumerate(approaches) if i != active_idx]
                    if elapsed_in_state >= self.min_green and active_q == 0 and any(q > 0 for q in other_q):
                        state = "YELLOW"
                        state_start_sim_time = sim_time
                        decision_reason = f"{active_approach_name} cleared early (queue=0) -> switching"
                        cycle_history.append((sim_time, active_approach_name, "GAP_OUT", elapsed_in_state))
                    elif elapsed_in_state >= allocated_green:
                        state = "YELLOW"
                        state_start_sim_time = sim_time
                        decision_reason = f"Allocated green ({allocated_green:.1f}s) expired"
                        cycle_history.append((sim_time, active_approach_name, "MAX_OUT", elapsed_in_state))

                elif state == "YELLOW":
                    rem_time = max(0.0, self.yellow - elapsed_in_state)
                    if elapsed_in_state >= self.yellow:
                        state = "ALL_RED"
                        state_start_sim_time = sim_time
                        decision_reason = "Intersection clearance (All-Red)"

                elif state == "ALL_RED":
                    rem_time = max(0.0, self.all_red - elapsed_in_state)
                    if elapsed_in_state >= self.all_red:
                        # Adaptive decision: choose next approach and allocate green time
                        next_idx = (active_idx + 1) % len(approaches)
                        # If competing approach has higher queue, give it priority
                        best_idx = next_idx
                        max_q = queue_counts[approaches[next_idx]["name"]]
                        for i, app in enumerate(approaches):
                            if queue_counts[app["name"]] > max_q:
                                max_q = queue_counts[app["name"]]
                                best_idx = i

                        active_idx = best_idx
                        target_q = max_q
                        calculated_green = self.min_green + (target_q * self.time_per_car)
                        allocated_green = float(np.clip(calculated_green, self.min_green, self.max_green))

                        state = "GREEN"
                        state_start_sim_time = sim_time
                        decision_reason = (
                            f"Assigned {allocated_green:.1f}s green to {approaches[active_idx]['name']} "
                            f"(queue: {target_q} vehicles)"
                        )
                        logger.info(f"[{self.video_path.name} @ {sim_time:.1f}s] {decision_reason}")

                # Count vehicle classes detected in current frame
                v_counts = {cls_name: 0 for cls_name in self.active_classes.values()}
                for item in detected_boxes:
                    v_name = item[4]
                    if v_name in v_counts:
                        v_counts[v_name] += 1

                # Record statistics
                rec = {
                    "sim_time": round(sim_time, 2),
                    "frame": frame_idx,
                    "state": state,
                    "active_approach": approaches[active_idx]["name"],
                    "remaining_time": round(rem_time, 2),
                    "queue_app1": queue_counts[approaches[0]["name"]],
                    "queue_app2": queue_counts[approaches[1]["name"]] if len(approaches) > 1 else 0,
                    "keke_count": v_counts.get("keke", 0),
                    "truck_count": v_counts.get("truck", 0),
                    "car_count": v_counts.get("car", 0),
                    "bus_count": v_counts.get("bus", 0),
                    "motorcycle_count": v_counts.get("motorcycle", 0),
                    "decision": decision_reason,
                }
                queue_records.append(rec)

                # Render high-visibility annotated video frame
                if writer is not None:
                    ctrl_info = {
                        "state": state,
                        "active_approach": approaches[active_idx]["name"],
                        "remaining_time": rem_time,
                        "signals": {
                            app["name"]: (
                                state if i == active_idx else ("ALL_RED" if state == "ALL_RED" else "RED")
                            )
                            for i, app in enumerate(approaches)
                        },
                        "reason": decision_reason,
                    }

                    canvas = draw_high_visibility_hud(
                        frame=frame,
                        approaches=approaches,
                        queue_counts=queue_counts,
                        controller_info=ctrl_info,
                        fps=fps,
                        detected_boxes=detected_boxes,
                        sim_time=sim_time,
                        title_prefix=f"SIM: {self.video_path.name}",
                    )

                    writer.write(canvas)

                processed_count += 1

            frame_idx += 1

        cap.release()
        if writer is not None:
            writer.release()

        # Save stats CSV
        if queue_records:
            with open(stats_csv_path, "w", newline="", encoding="utf-8") as f_csv:
                fieldnames = list(queue_records[0].keys())
                cw = csv.DictWriter(f_csv, fieldnames=fieldnames)
                cw.writeheader()
                cw.writerows(queue_records)

        duration_sec = time.time() - start_real_time
        avg_q1 = np.mean([r["queue_app1"] for r in queue_records]) if queue_records else 0
        avg_q2 = np.mean([r["queue_app2"] for r in queue_records]) if queue_records else 0
        max_q1 = max([r["queue_app1"] for r in queue_records]) if queue_records else 0
        max_q2 = max([r["queue_app2"] for r in queue_records]) if queue_records else 0

        total_keke = sum(r.get("keke_count", 0) for r in queue_records)
        total_truck = sum(r.get("truck_count", 0) for r in queue_records)
        total_car = sum(r.get("car_count", 0) for r in queue_records)
        total_bus = sum(r.get("bus_count", 0) for r in queue_records)
        total_mc = sum(r.get("motorcycle_count", 0) for r in queue_records)

        summary = {
            "video": self.video_path.name,
            "duration_sim_seconds": round(sim_time, 1),
            "processed_frames": processed_count,
            "real_elapsed_seconds": round(duration_sec, 1),
            "output_video": str(out_video_path),
            "stats_csv": str(stats_csv_path),
            "avg_queue_app1": round(float(avg_q1), 2),
            "max_queue_app1": int(max_q1),
            "avg_queue_app2": round(float(avg_q2), 2),
            "max_queue_app2": int(max_q2),
            "phase_switches": len(cycle_history),
            "vehicle_detections": {
                "keke": int(total_keke),
                "truck": int(total_truck),
                "car": int(total_car),
                "bus": int(total_bus),
                "motorcycle": int(total_mc),
            },
        }
        logger.info(f"Finished {self.video_path.name}: {summary}")
        return summary


def main():
    parser = argparse.ArgumentParser(description="Run simulations across multiple intersection viewpoints")
    parser.add_argument(
        "--videos",
        nargs="+",
        default=[
            "videos/view_WA0033.mp4",
            "videos/view_WA0029.mp4",
            "videos/view_WA0025.mp4",
            "videos/aerial_reference.mp4",
        ],
        help="List of video files to simulate",
    )
    parser.add_argument("--skip", type=int, default=2, help="Process every Nth frame")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image resolution")
    parser.add_argument("--duration", type=float, default=None, help="Max simulated video duration in seconds (e.g. 360 for 6 mins)")
    parser.add_argument(
        "--model",
        type=str,
        default="models/yolo11n_traffic_keke.pt" if Path("models/yolo11n_traffic_keke.pt").exists() else "yolo11n.pt",
        help="Path to YOLO weights",
    )
    args = parser.parse_args()

    out_dir = Path("outputs/simulations")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print("   YABATECH INTERSECTION MULTI-VIEWPOINT SIMULATION SUITE")
    print("=" * 65)
    print(f"Loading object detector: {args.model} ...")
    model = YOLO(args.model)

    results = []
    for vid_str in args.videos:
        vid_path = Path(vid_str)
        if not vid_path.exists():
            print(f"[SKIP] Video not found: {vid_path}")
            continue

        sim = ViewpointSimulator(
            video_path=vid_path,
            output_dir=out_dir,
            model=model,
            skip_frames=args.skip,
            imgsz=args.imgsz,
            max_duration_sec=args.duration,
        )
        res = sim.run(save_video=True)
        results.append(res)

    # Save grand summary JSON
    summary_path = out_dir / "simulation_summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n" + "=" * 65)
    print("                   SIMULATION RESULTS")
    print("=" * 65)
    for r in results:
        print(f"Viewpoint: {r['video']}")
        print(f"  - Simulated Duration : {r['duration_sim_seconds']}s")
        print(f"  - Approach 1 Queue   : Avg {r['avg_queue_app1']} | Max {r['max_queue_app1']} vehicles")
        print(f"  - Approach 2 Queue   : Avg {r['avg_queue_app2']} | Max {r['max_queue_app2']} vehicles")
        print(f"  - Phase Transitions  : {r['phase_switches']} dynamic signal changes")
        if "vehicle_detections" in r:
            vd = r["vehicle_detections"]
            print(f"  - Vehicle Breakdown  : Kekes: {vd.get('keke', 0)} | Trucks: {vd.get('truck', 0)} | Cars: {vd.get('car', 0)} | Buses: {vd.get('bus', 0)} | Motorcycles: {vd.get('motorcycle', 0)}")
        print(f"  - Annotated Video    : {r['output_video']}")
        print(f"  - Performance Stats  : {r['stats_csv']}\n")
    print(f"Full results saved to: {summary_path}")


if __name__ == "__main__":
    main()
