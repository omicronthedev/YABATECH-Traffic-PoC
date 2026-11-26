"""
Train Ultralytics YOLO11 to distinguish Keke Marwa (commercial tricycles)
from Trucks, Cars, Buses, and Motorcycles for the YABATECH Traffic PoC.
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["YOLO_CONFIG_DIR"] = str((BASE_DIR / ".ultralytics").resolve())

from ultralytics import YOLO

def main():
    yaml_path = BASE_DIR / "datasets" / "traffic_keke" / "traffic_keke.yaml"
    if not yaml_path.exists():
        raise FileNotFoundError(f"Dataset config not found at {yaml_path}. Run build_keke_dataset.py first.")

    models_dir = BASE_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    target_model_path = models_dir / "yolo11n_traffic_keke.pt"

    print("=" * 65)
    print("YABATECH Traffic PoC: Fine-Tuning YOLO11 for Keke vs Truck")
    print("=" * 65)
    print(f"Dataset config  : {yaml_path}")
    print(f"Base checkpoint : yolo11n.pt")
    print(f"Target model    : {target_model_path}")
    print("Device          : CPU")
    print("Classes         : [0: car, 1: motorcycle, 2: bus, 3: truck, 4: keke]")
    print("-" * 65)

    # Load base pretrained model
    model = YOLO(str(BASE_DIR / "yolo11n.pt"))

    # Train model
    results = model.train(
        data=str(yaml_path),
        epochs=15,
        imgsz=640,
        batch=8,
        workers=2,
        device="cpu",
        freeze=10,  # Freeze lower layers to retain general visual features & speed up CPU training
        project=str(BASE_DIR / "runs" / "train"),
        name="yolo11n_keke_traffic",
        exist_ok=True,
        save=True,
        verbose=True,
    )

    # Locate best checkpoint
    best_weights = BASE_DIR / "runs" / "train" / "yolo11n_keke_traffic" / "weights" / "best.pt"
    if not best_weights.exists():
        # Fallback to last.pt if best.pt is not created
        best_weights = BASE_DIR / "runs" / "train" / "yolo11n_keke_traffic" / "weights" / "last.pt"

    if best_weights.exists():
        shutil.copy(best_weights, target_model_path)
        print(f"\nSuccessfully saved trained model to: {target_model_path}")
    else:
        print("\nWarning: Could not locate weight files in runs/train/yolo11n_keke_traffic/weights/")

    # Validate trained model
    print("\nRunning validation evaluation on validation set...")
    val_model = YOLO(str(target_model_path if target_model_path.exists() else best_weights))
    metrics = val_model.val(data=str(yaml_path), verbose=True)

    print("\nValidation Metrics Summary:")
    print(f"mAP50-95 : {metrics.box.map:.4f}")
    print(f"mAP50    : {metrics.box.map50:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall   : {metrics.box.mr:.4f}")
    
    print("\nTraining and validation complete!")

if __name__ == "__main__":
    main()
