
import csv
import time
from pathlib import Path

import cv2
from ultralytics import YOLO


VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


def main():

    video_path = Path("videos/test_clip.mp4")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(video_path)

    print("Loading YOLO11n...")
    model = YOLO("yolo11n.pt")

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError("Cannot open video.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_video = output_dir / "tracked_video.mp4"
    stats_file = output_dir / "tracking_statistics.csv"
    tracks_file = output_dir / "unique_tracks.csv"

    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    if not writer.isOpened():
        raise RuntimeError("Cannot create output video.")

    # Track IDs already encountered
    unique_tracks = {}

    frame_number = 0
    start_time = time.time()

    with open(stats_file, "w", newline="") as csv_file:

        csv_writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "frame",
                "timestamp_seconds",
                "tracked_vehicles",
                "cars",
                "motorcycles",
                "buses",
                "trucks",
                "cumulative_unique_vehicles"
            ]
        )

        csv_writer.writeheader()

        print("Starting vehicle tracking...")

        while True:

            success, frame = cap.read()

            if not success:
                break

            results = model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                classes=list(VEHICLE_CLASSES.keys()),
                conf=0.25,
                imgsz=640,
                device="cpu",
                verbose=False
            )

            result = results[0]

            counts = {
                "car": 0,
                "motorcycle": 0,
                "bus": 0,
                "truck": 0
            }

            tracked_count = 0

            if result.boxes is not None:

                ids = result.boxes.id

                if ids is not None:

                    track_ids = ids.int().cpu().tolist()
                    class_ids = (
                        result.boxes.cls.int().cpu().tolist()
                    )

                    for track_id, class_id in zip(
                        track_ids, class_ids
                    ):

                        vehicle = VEHICLE_CLASSES.get(class_id)

                        if vehicle is None:
                            continue

                        counts[vehicle] += 1
                        tracked_count += 1

                        if track_id not in unique_tracks:

                            unique_tracks[track_id] = {
                                "track_id": track_id,
                                "vehicle_type": vehicle,
                                "first_seen_frame": frame_number,
                                "first_seen_seconds": round(
                                    frame_number / fps, 2
                                )
                            }

            annotated = result.plot()

            cv2.putText(
                annotated,
                f"Tracked vehicles: {tracked_count}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )

            cv2.putText(
                annotated,
                f"Unique vehicles: {len(unique_tracks)}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            writer.write(annotated)

            csv_writer.writerow({
                "frame": frame_number,
                "timestamp_seconds": round(
                    frame_number / fps, 2
                ),
                "tracked_vehicles": tracked_count,
                "cars": counts["car"],
                "motorcycles": counts["motorcycle"],
                "buses": counts["bus"],
                "trucks": counts["truck"],
                "cumulative_unique_vehicles": len(unique_tracks)
            })

            frame_number += 1

            if frame_number % 100 == 0:
                print(f"Processed {frame_number} frames...")

    # Export unique vehicle records
    with open(tracks_file, "w", newline="") as file:

        if unique_tracks:

            fieldnames = [
                "track_id",
                "vehicle_type",
                "first_seen_frame",
                "first_seen_seconds"
            ]

            track_writer = csv.DictWriter(
                file,
                fieldnames=fieldnames
            )

            track_writer.writeheader()
            track_writer.writerows(unique_tracks.values())

    cap.release()
    writer.release()

    print("\nTracking completed.")
    print(f"Frames processed: {frame_number}")
    print(f"Unique track IDs: {len(unique_tracks)}")
    print(f"Time taken: {time.time() - start_time:.1f}s")
    print(f"Video: {output_video}")
    print(f"Statistics: {stats_file}")
    print(f"Unique tracks: {tracks_file}")


if __name__ == "__main__":
    main()