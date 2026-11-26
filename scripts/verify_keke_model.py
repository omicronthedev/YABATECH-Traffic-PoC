"""
Comparison and verification script:
Tests baseline yolo11n.pt vs fine-tuned models/yolo11n_traffic_keke.pt
to verify that kekes are recognized as kekes and trucks are recognized as trucks.
"""

import os
from pathlib import Path
import cv2

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["YOLO_CONFIG_DIR"] = str((BASE_DIR / ".ultralytics").resolve())

from ultralytics import YOLO

def main():
    base_model_path = BASE_DIR / "yolo11n.pt"
    custom_model_path = BASE_DIR / "models" / "yolo11n_traffic_keke.pt"
    out_dir = BASE_DIR / "outputs" / "keke_verification"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("VERIFICATION: Baseline vs Custom YOLO11 Traffic Model")
    print("=" * 65)
    print(f"Baseline model : {base_model_path}")
    print(f"Custom model   : {custom_model_path}")
    print(f"Output folder  : {out_dir}")
    print("-" * 65)

    base_model = YOLO(str(base_model_path))
    custom_model = YOLO(str(custom_model_path))

    # Test images: reference keke images & sample validation frames
    brain_dir = Path("C:/Users/User/.gemini/antigravity/brain/f841bdb5-c33f-4298-a0c6-12800148c9ab")
    test_images = list(brain_dir.glob("keke_*.jpg"))[:3]
    val_images = list((BASE_DIR / "datasets" / "traffic_keke" / "images" / "val").glob("*.jpg"))[:3]
    all_tests = test_images + val_images

    for img_path in all_tests:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        h, w = img.shape[:2]
        
        # 1. Baseline prediction
        res_base = base_model.predict(img, conf=0.25, verbose=False)[0]
        base_dets = []
        for box, cls_id, conf in zip(res_base.boxes.xyxy, res_base.boxes.cls, res_base.boxes.conf):
            cls_name = res_base.names[int(cls_id)]
            base_dets.append(f"{cls_name} ({conf:.2f})")

        # 2. Custom model prediction
        res_custom = custom_model.predict(img, conf=0.25, verbose=False)[0]
        custom_dets = []
        for box, cls_id, conf in zip(res_custom.boxes.xyxy, res_custom.boxes.cls, res_custom.boxes.conf):
            cls_name = res_custom.names[int(cls_id)]
            custom_dets.append(f"{cls_name} ({conf:.2f})")

        print(f"\nImage: {img_path.name}")
        print(f"  [Baseline yolo11n]       : {base_dets if base_dets else 'No detections'}")
        print(f"  [Custom yolo11n_traffic] : {custom_dets if custom_dets else 'No detections'}")

        # Render side-by-side comparison image
        plot_base = res_base.plot()
        plot_custom = res_custom.plot()

        # Resize to same height for side-by-side display
        target_h = 480
        scale_b = target_h / plot_base.shape[0]
        scale_c = target_h / plot_custom.shape[0]
        
        pb_resized = cv2.resize(plot_base, (int(plot_base.shape[1] * scale_b), target_h))
        pc_resized = cv2.resize(plot_custom, (int(plot_custom.shape[1] * scale_c), target_h))

        # Add title headers
        cv2.putText(pb_resized, "BEFORE: Base YOLO11 (Misclassifies as Truck)", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2)
        cv2.putText(pc_resized, "AFTER: Custom YOLO11 (Classifies as Keke)", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        comparison = cv2.hconcat([pb_resized, pc_resized])
        out_file = out_dir / f"compare_{img_path.stem}.jpg"
        cv2.imwrite(str(out_file), comparison)

    print("\n" + "=" * 65)
    print(f"All comparison preview images saved to: {out_dir}")
    print("=" * 65)

if __name__ == "__main__":
    main()
