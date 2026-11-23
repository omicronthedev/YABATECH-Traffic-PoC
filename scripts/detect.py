from os import stat
import argparse
import csv
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

# COCO Dataset class IDs
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

def main():
    parser = argparse.ArgumentParser(
        description="YABATECH Traffic Vehicle Detection"
    )
    
    parser.add_argument(
        "--source",
        default="videos/main_intersection.mp4",
        help="Path to the input video"
    )
    
    parser.add_argument(
        "--skip",
        type=int,
        default=2,
        help="Process every Nth frame"
    )
    
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Detection confidence threshold"
    )
    
    args = parser.parse_args()
    
    source = Path(args.source)
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    if not source.exists():
        raise FileNotFoundError(
            f"Video not found: {source}"
        )
        
    if args.skip < 1:
        raise ValueError("--skip must be at least 1")
    
    # Load lightweight YOLO model
    print("Loading YOLO11n...")
    model = YOLO("yolo11n.pt")
    
    # Open video
    cap = cv2.VideoCapture(str(source))
    
    if not cap.isOpened():
        raise RuntimeError("Could not open video.")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if fps <= 0:
        fps = 25
        
    output_fps = fps / args.skip
    
    output_video = output_dir / (
        source.stem + "_detected_0_25_960.mp4"
    )
    
    output_csv = output_dir / (
        source.stem + "_statistics_0_25_960.csv"
    )
    
    writer = cv2.VideoWriter(
        str(output_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        output_fps,
        (width, height)
    )
    
    if not writer.isOpened():
        raise RuntimeError("Could not create output video.")
    
    processed_frames = 0
    start_time = time.time()
    
    print(f"Video: {source}")
    print(f"Resolution: {width}x{height}")
    print(f"Original FPS: {fps}")
    print(f"Total frames: {total_frames}")
    print("Starting detection...\n")
    
    with open(output_csv, "w", newline="") as csv_file:
        
        csv_writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "frame",
                "timestamp_seconds",
                "car",
                "motorcycle",
                "bus",
                "truck",
                "total_vehicles"
            ]
        )
        
        csv_writer.writeheader()
        
        frame_index = 0
        
        while True:
            success, frame = cap.read()
            
            if not success:
                break
            
            # Process only selected frames
            if frame_index % args.skip == 0:
                
                result = model.predict(
                    frame,
                    imgsz=960,
                    conf=args.conf,
                    classes=list(VEHICLE_CLASSES.keys()),
                    device="cpu",
                    verbose=False
                )[0]
                
                counts = {
                    name: 0
                    for name in VEHICLE_CLASSES.values()
                }
                
                if result.boxes is not None:
                    for class_id in (
                        result.boxes.cls.cpu().numpy().astype(int)
                    ):
                        vehicle_name = VEHICLE_CLASSES.get(class_id)
                        
                        if vehicle_name:
                            counts[vehicle_name] += 1
                            
                total = sum(counts.values())
                
                # Draw bounding boxes
                annotated_frame = result.plot()
                
                # Display detection information
                cv2.putText(
                    annotated_frame,
                    f"Vehicles detected: {total}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )
                
                writer.write(annotated_frame)
                
                csv_writer.writerow({
                    "frame": frame_index,
                    "timestamp_seconds": round(
                        frame_index / fps, 2
                    ),
                    **counts,
                    "total_vehicles": total,
                })
                
                processed_frames += 1
                
                if processed_frames % 100 == 0:
                    progress = (
                        frame_index / total_frames * 100
                        if total_frames else 0
                    )
                    
                    print(
                        f"Progress: {progress:.1f}% | "
                        f"Processed: {processed_frames} frames"
                    )
                    
            frame_index += 1
            
    cap.release()
    writer.release()
    
    elapsed = time.time() - start_time
    
    print("\nDetection completed!")
    print(f"Processed frames: {processed_frames}")
    print(f"Processing time: {elapsed:.1f} seconds")
    print(f"Annotated video: {output_video}")
    print(f"Statistics CSV: {output_csv}")
    

if __name__ == "__main__":
    main()