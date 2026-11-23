"""YABATECH Traffic PoC: YOLO11n + ByteTrack + virtual-line counting.

Usage:
  python track_and_count.py --source videos/test_clip.mp4 --setup --skip 2
  python track_and_count.py --source videos/main_intersection.mp4 --skip 2

On first run (or with --setup), draw each counting line by clicking two endpoints
on the displayed first frame. Press ENTER to accept, R to redraw. Lines are saved
as normalized coordinates in outputs/counting_lines.json.
"""

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
from ultralytics import YOLO

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


def display_scale(frame, max_w=1000, max_h=760):
    h, w = frame.shape[:2]
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1:
        shown = cv2.resize(frame, (int(w * scale), int(h * scale)))
    else:
        shown = frame.copy()
    return shown, scale


def configure_lines(frame, output_dir):
    """Interactively draw lines; coordinates are stored normalized to frame size."""
    h, w = frame.shape[:2]
    shown, scale = display_scale(frame)
    lines = []

    print("\nCOUNTING-LINE SETUP")
    print("For each approach, draw a line across the road near the boundary of the junction.")
    print("Click two endpoints spanning the traffic lane(s). Press ENTER to accept, R to redraw.")
    print("Use a short test clip with a stable camera view for this first calibration.\n")
    try:
        n_lines = int(input("How many counting lines do you want to configure? (Start with 1 or 2): ").strip())
    except ValueError:
        raise SystemExit("Please enter a whole number.")
    if n_lines < 1 or n_lines > 8:
        raise SystemExit("Choose between 1 and 8 lines.")

    for idx in range(n_lines):
        points = []
        window = f"Draw counting line {idx + 1} of {n_lines}"

        def mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
                points.append((int(x / scale), int(y / scale)))

        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window, mouse)
        while True:
            canvas = shown.copy()
            cv2.putText(canvas, "Click 2 endpoints across the road | ENTER=accept | R=redraw",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2)
            for p in points:
                cv2.circle(canvas, (int(p[0] * scale), int(p[1] * scale)), 7, (0, 0, 255), -1)
            if len(points) == 2:
                p1 = (int(points[0][0] * scale), int(points[0][1] * scale))
                p2 = (int(points[1][0] * scale), int(points[1][1] * scale))
                cv2.line(canvas, p1, p2, (0, 255, 0), 3)
            cv2.imshow(window, canvas)
            key = cv2.waitKey(30) & 0xFF
            if key in (13, 10) and len(points) == 2:
                break
            if key in (ord('r'), ord('R')):
                points.clear()
            if key == 27:
                cv2.destroyWindow(window)
                raise SystemExit("Line setup cancelled.")

        cv2.destroyWindow(window)
        name = input(f"Name this line (e.g. South approach): ").strip() or f"Line {idx + 1}"
        lines.append({
            "name": name,
            "p1": [points[0][0] / w, points[0][1] / h],
            "p2": [points[1][0] / w, points[1][1] / h],
        })
        print(f"Saved: {name}")

    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = output_dir / "counting_lines.json"
    config_path.write_text(json.dumps({"reference_width": w, "reference_height": h, "lines": lines}, indent=2))
    print(f"\nCounting lines saved to: {config_path}")
    return lines



def load_lines(config_path, frame_shape):
    data = json.loads(config_path.read_text())

    h, w = frame_shape[:2]

    reference_w = data.get("reference_width", w)
    reference_h = data.get("reference_height", h)

    lines = []

    for item in data["lines"]:
        raw_p1 = [float(v) for v in item["p1"]]
        raw_p2 = [float(v) for v in item["p2"]]

        # Support both normalized and pixel coordinates.
        if all(0 <= v <= 1 for v in raw_p1 + raw_p2):
            p1 = (
                int(round(raw_p1[0] * w)),
                int(round(raw_p1[1] * h))
            )
            p2 = (
                int(round(raw_p2[0] * w)),
                int(round(raw_p2[1] * h))
            )
        else:
            p1 = (
                int(round(raw_p1[0] * w / reference_w)),
                int(round(raw_p1[1] * h / reference_h))
            )
            p2 = (
                int(round(raw_p2[0] * w / reference_w)),
                int(round(raw_p2[1] * h / reference_h))
            )

        lines.append({
            "name": item["name"],
            "p1": p1,
            "p2": p2
        })

    return lines


def signed_side(point, p1, p2):
    return (p2[0] - p1[0]) * (point[1] - p1[1]) - (p2[1] - p1[1]) * (point[0] - p1[0])


def crossing_direction(prev_pt, curr_pt, p1, p2, tolerance=6):
    """Return A_to_B or B_to_A if movement crosses the finite line segment."""
    d1 = signed_side(prev_pt, p1, p2)
    d2 = signed_side(curr_pt, p1, p2)
    if abs(d1) < tolerance or abs(d2) < tolerance or d1 * d2 >= 0:
        return None
    ratio = d1 / (d1 - d2)
    ix = prev_pt[0] + ratio * (curr_pt[0] - prev_pt[0])
    iy = prev_pt[1] + ratio * (curr_pt[1] - prev_pt[1])
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return None
    projection = ((ix - p1[0]) * dx + (iy - p1[1]) * dy) / length_sq
    if projection < -0.05 or projection > 1.05:
        return None
    return "A_to_B" if d1 < 0 < d2 else "B_to_A"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="videos/test_clip.mp4")
    parser.add_argument("--setup", action="store_true", help="Redraw counting lines")
    parser.add_argument("--skip", type=int, default=2, help="Process every Nth frame")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    if args.skip < 1:
        raise SystemExit("--skip must be at least 1")

    source = Path(args.source)
    if not source.exists():
        raise FileNotFoundError(f"Video not found: {source}")

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    config_path = out_dir / "counting_lines.json"

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {source}")
    if hasattr(cv2, "CAP_PROP_ORIENTATION_AUTO"):
        cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)

    ok, first_frame = cap.read()
    if not ok:
        raise RuntimeError("Could not read the first video frame.")

    if args.setup or not config_path.exists():
        lines = configure_lines(first_frame, out_dir)
    else:
        lines = load_lines(config_path, first_frame.shape)

    # Restart from the beginning after line setup.
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ok, first_frame = cap.read()
    if not ok:
        raise RuntimeError("Could not restart video.")
    h, w = first_frame.shape[:2]

    output_video = out_dir / f"{source.stem}_counted.mp4"
    events_csv = out_dir / f"{source.stem}_crossing_events.csv"
    summary_csv = out_dir / f"{source.stem}_counting_summary.csv"
    writer = cv2.VideoWriter(str(output_video), cv2.VideoWriter_fourcc(*"mp4v"), fps / args.skip, (w, h))
    if not writer.isOpened():
        raise RuntimeError("Could not create annotated output video.")

    print("\nLoading YOLO11n and starting ByteTrack + line counting...")
    model = YOLO("yolo11n.pt")
    previous_points = {}  # (track_id, line_index) -> last bottom-centre point
    already_counted = set()  # (track_id, line_index)
    event_rows = []
    line_counts = Counter()
    class_counts = Counter()
    frame_index = 0
    processed = 0
    start_time = time.time()

    with open(events_csv, "w", newline="", encoding="utf-8") as f_events:
        fields = ["timestamp_seconds", "frame", "track_id", "vehicle_class", "counting_line", "direction"]
        event_writer = csv.DictWriter(f_events, fieldnames=fields)
        event_writer.writeheader()

        while True:
            if frame_index == 0:
                frame = first_frame
                ok = True
            else:
                ok, frame = cap.read()
            if not ok:
                break

            if frame_index % args.skip == 0:
                result = model.track(
                    frame, persist=True, tracker="bytetrack.yaml",
                    classes=list(VEHICLE_CLASSES.keys()), conf=args.conf,
                    imgsz=args.imgsz, device="cpu", verbose=False
                )[0]

                annotated = result.plot()
                if result.boxes is not None and result.boxes.id is not None:
                    boxes = result.boxes.xyxy.cpu().tolist()
                    ids = result.boxes.id.int().cpu().tolist()
                    class_ids = result.boxes.cls.int().cpu().tolist()
                    for box, track_id, class_id in zip(boxes, ids, class_ids):
                        vehicle_class = VEHICLE_CLASSES.get(class_id, "unknown")
                        x1, y1, x2, y2 = box
                        foot_point = (int((x1 + x2) / 2), int(y2))
                        for line_idx, line in enumerate(lines):
                            key = (track_id, line_idx)
                            p1, p2 = line["p1"], line["p2"]
                            prev = previous_points.get(key)
                            if prev is not None and key not in already_counted:
                                direction = crossing_direction(prev, foot_point, p1, p2)
                                if direction:
                                    row = {
                                        "timestamp_seconds": round(frame_index / fps, 2),
                                        "frame": frame_index,
                                        "track_id": track_id,
                                        "vehicle_class": vehicle_class,
                                        "counting_line": line["name"],
                                        "direction": direction,
                                    }
                                    event_writer.writerow(row)
                                    f_events.flush()
                                    event_rows.append(row)
                                    already_counted.add(key)
                                    line_counts[(line["name"], direction)] += 1
                                    class_counts[(line["name"], direction, vehicle_class)] += 1
                            previous_points[key] = foot_point

                # Draw counting lines and current totals.
                y_text = 35
                for line in lines:
                    p1 = tuple(int(v) for v in line["p1"])
                    p2 = tuple(int(v) for v in line["p2"])

                    cv2.line(annotated, p1, p2, (0, 255, 255), 3)
                    mid = ((line["p1"][0] + line["p2"][0]) // 2, (line["p1"][1] + line["p2"][1]) // 2)
                    cv2.putText(annotated, line["name"], mid, cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                    a = line_counts[(line["name"], "A_to_B")]
                    b = line_counts[(line["name"], "B_to_A")]
                    cv2.putText(annotated, f"{line['name']}: A>B {a} | B>A {b}", (15, y_text),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
                    y_text += 30

                writer.write(annotated)
                processed += 1
                if processed % 100 == 0:
                    pct = (frame_index / total_frames * 100) if total_frames else 0
                    print(f"Progress: {pct:.1f}% ({processed} processed frames; {len(event_rows)} crossings)")

            frame_index += 1

    cap.release()
    writer.release()

    with open(summary_csv, "w", newline="", encoding="utf-8") as f_summary:
        fields = ["counting_line", "direction", "vehicle_class", "count"]
        sw = csv.DictWriter(f_summary, fieldnames=fields)
        sw.writeheader()
        for (line_name, direction, vehicle_class), count in sorted(class_counts.items()):
            sw.writerow({"counting_line": line_name, "direction": direction,
                         "vehicle_class": vehicle_class, "count": count})

    print("\nCOUNTING COMPLETE")
    print(f"Frames processed: {processed}")
    print(f"Crossing events: {len(event_rows)}")
    print(f"Annotated video: {output_video}")
    print(f"Crossing event log: {events_csv}")
    print(f"Counting summary: {summary_csv}")
    print(f"Elapsed time: {time.time() - start_time:.1f} seconds")
    print("Direction key: A_to_B / B_to_A refers to the two sides determined by your line endpoint order.")
    print("Review the video before treating counts as final; ID switches and camera movement can affect results.")


if __name__ == "__main__":
    main()
