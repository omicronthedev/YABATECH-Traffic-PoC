"""
Script to build a comprehensive YOLO detection dataset for Nigerian traffic,
specifically distinguishing Keke (commercial tricycles) from Trucks, Cars, Buses, and Motorcycles.
"""

import os
import random
import shutil
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageEnhance

# Set local Ultralytics config dir to avoid permission errors
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ["YOLO_CONFIG_DIR"] = str((BASE_DIR / ".ultralytics").resolve())

from ultralytics import YOLO

DATASET_DIR = BASE_DIR / "datasets" / "traffic_keke"
IMAGES_TRAIN = DATASET_DIR / "images" / "train"
IMAGES_VAL = DATASET_DIR / "images" / "val"
LABELS_TRAIN = DATASET_DIR / "labels" / "train"
LABELS_VAL = DATASET_DIR / "labels" / "val"

# Target classes
# 0: car, 1: motorcycle, 2: bus, 3: truck, 4: keke
COCO_TO_CUSTOM = {
    2: 0,  # car -> car
    3: 1,  # motorcycle -> motorcycle
    5: 2,  # bus -> bus
    7: 3,  # truck -> truck
}

def setup_dirs():
    """Create clean dataset directory structure."""
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)
    for p in [IMAGES_TRAIN, IMAGES_VAL, LABELS_TRAIN, LABELS_VAL]:
        p.mkdir(parents=True, exist_ok=True)
    print(f"Created dataset directories at {DATASET_DIR}")

def extract_video_frames(max_frames_per_video=8):
    """Extract diverse background frames from available traffic videos."""
    video_dir = BASE_DIR / "videos"
    video_files = list(video_dir.glob("*.mp4"))
    frames = []

    for vf in video_files:
        cap = cv2.VideoCapture(str(vf))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            continue
        
        step = max(total_frames // (max_frames_per_video + 1), 15)
        for i in range(1, max_frames_per_video + 1):
            frame_idx = min(i * step, total_frames - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret and frame is not None:
                # Resize to standard 640x640 or 960x540 for training
                h, w = frame.shape[:2]
                frames.append((frame, f"{vf.stem}_f{frame_idx}"))
        cap.release()
    print(f"Extracted {len(frames)} base frames from videos.")
    return frames

def extract_reference_kekes():
    """Load reference keke images generated or stored in the brain directory."""
    brain_dir = Path("C:/Users/User/.gemini/antigravity/brain/f841bdb5-c33f-4298-a0c6-12800148c9ab")
    keke_files = list(brain_dir.glob("keke_*.jpg"))
    keke_imgs = []
    for kf in keke_files:
        img = cv2.imread(str(kf))
        if img is not None:
            keke_imgs.append((img, kf.stem))
    print(f"Found {len(keke_imgs)} reference keke images.")
    return keke_imgs

def crop_keke_foreground(keke_img):
    """Crop the central keke body from reference images."""
    h, w = keke_img.shape[:2]
    # Crop central 75% where keke is located
    ymin, ymax = int(h * 0.15), int(h * 0.90)
    xmin, xmax = int(w * 0.10), int(w * 0.90)
    crop = keke_img[ymin:ymax, xmin:xmax]
    return crop

def create_synthetic_bus_crop():
    """Synthesize a Danfo yellow commercial commuter bus template."""
    bus_w, bus_h = 240, 150
    bus_img = np.zeros((bus_h, bus_w, 3), dtype=np.uint8)
    # Bright yellow Danfo body with dual black stripes
    cv2.rectangle(bus_img, (10, 20), (220, 125), (30, 215, 250), -1)
    cv2.rectangle(bus_img, (10, 65), (220, 75), (20, 20, 20), -1)
    cv2.rectangle(bus_img, (10, 85), (220, 95), (20, 20, 20), -1)
    # Windows
    for wx in [30, 75, 120, 165]:
        cv2.rectangle(bus_img, (wx, 30), (wx + 35, 60), (200, 220, 240), -1)
    # Windshield front
    cv2.rectangle(bus_img, (190, 30), (220, 65), (200, 220, 240), -1)
    # Wheels
    cv2.circle(bus_img, (60, 130), 16, (20, 20, 20), -1)
    cv2.circle(bus_img, (175, 130), 16, (20, 20, 20), -1)
    return bus_img

def create_synthetic_motorcycle_crop():
    """Synthesize an Okada commercial motorcycle template."""
    mc_w, mc_h = 120, 120
    mc_img = np.zeros((mc_h, mc_w, 3), dtype=np.uint8)
    # Wheels
    cv2.circle(mc_img, (25, 95), 18, (20, 20, 20), -1)
    cv2.circle(mc_img, (95, 95), 18, (20, 20, 20), -1)
    # Frame & seat
    cv2.line(mc_img, (25, 95), (60, 65), (180, 40, 40), 5)
    cv2.line(mc_img, (95, 95), (60, 65), (180, 40, 40), 5)
    cv2.line(mc_img, (60, 65), (90, 40), (40, 40, 40), 5)  # handlebars
    cv2.rectangle(mc_img, (40, 55), (75, 65), (20, 20, 20), -1)  # seat
    return mc_img


def create_synthetic_truck_crop():
    """Synthesize a robust commercial box/tipper truck template for heavy truck class."""
    truck_w, truck_h = 320, 240
    truck_img = np.zeros((truck_h, truck_w, 3), dtype=np.uint8)
    colors = [(70, 70, 180), (60, 120, 60), (160, 160, 160), (40, 80, 160)]
    cargo_color = random.choice(colors)
    cv2.rectangle(truck_img, (20, 20), (240, 190), cargo_color, -1)
    cv2.rectangle(truck_img, (20, 20), (240, 190), (30, 30, 30), 3)
    cab_color = (200, 200, 200)
    cv2.rectangle(truck_img, (230, 60), (310, 190), cab_color, -1)
    cv2.rectangle(truck_img, (250, 75), (305, 125), (220, 220, 240), -1)
    cv2.circle(truck_img, (70, 205), 25, (20, 20, 20), -1)
    cv2.circle(truck_img, (140, 205), 25, (20, 20, 20), -1)
    cv2.circle(truck_img, (275, 205), 25, (20, 20, 20), -1)
    return truck_img


def build_dataset():
    setup_dirs()
    base_model = YOLO("yolo11n.pt")
    video_frames = extract_video_frames(max_frames_per_video=6)
    keke_refs = extract_reference_kekes()

    keke_crops = [crop_keke_foreground(img) for img, _ in keke_refs]
    if not keke_crops and keke_refs:
        keke_crops = [img for img, _ in keke_refs]

    total_samples = 0
    train_count = 0
    val_count = 0

    print("Generating annotated images...")

    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    sample_id = 0

    # 1. First, process background video frames and pre-annotate standard vehicles
    for frame, name in video_frames:
        sample_id += 1
        is_val = (sample_id % 5 == 0)  # 20% validation
        
        target_img_dir = IMAGES_VAL if is_val else IMAGES_TRAIN
        target_lbl_dir = LABELS_VAL if is_val else LABELS_TRAIN

        h, w = frame.shape[:2]
        # Resize frame to standard 640x640 for consistency
        frame_resized = cv2.resize(frame, (640, 640))
        fh, fw = 640, 640

        # Predict with base model to get existing vehicles (cars, motorcycles, buses)
        results = base_model.predict(frame_resized, conf=0.35, verbose=False)[0]
        
        labels = []
        for box, cls_id in zip(results.boxes.xyxy, results.boxes.cls):
            c_int = int(cls_id)
            if c_int in COCO_TO_CUSTOM and c_int != 7:  # skip COCO truck (7) to re-annotate cleanly
                target_cls = COCO_TO_CUSTOM[c_int]
                x1, y1, x2, y2 = [float(v) for v in box]
                xc = ((x1 + x2) / 2.0) / fw
                yc = ((y1 + y2) / 2.0) / fh
                bw = (x2 - x1) / fw
                bh = (y2 - y1) / fh
                # Validate bounds
                if 0 < xc < 1 and 0 < yc < 1 and 0 < bw < 1 and 0 < bh < 1:
                    labels.append(f"{target_cls} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        # Inject kekes onto this frame
        if keke_crops and random.random() > 0.15:
            num_kekes = random.randint(1, 3)
            for _ in range(num_kekes):
                k_crop = random.choice(keke_crops)
                # Random scale: keke should be relatively compact (width ~ 90-160 px, height ~ 80-150 px)
                kw = random.randint(90, 160)
                kh = int(kw * (k_crop.shape[0] / k_crop.shape[1]))
                k_resized = cv2.resize(k_crop, (kw, kh))
                
                # Random flip for angle variety
                if random.random() > 0.5:
                    k_resized = cv2.flip(k_resized, 1)

                # Random placement in lower road area (y: 200 to 520)
                kx = random.randint(20, max(21, fw - kw - 20))
                ky = random.randint(int(fh * 0.35), max(int(fh * 0.36), fh - kh - 20))

                # Alpha blend or place
                roi = frame_resized[ky:ky+kh, kx:kx+kw]
                mask = (k_resized > 15).astype(np.uint8)
                blended = np.where(mask == 1, k_resized, roi)
                frame_resized[ky:ky+kh, kx:kx+kw] = cv2.addWeighted(blended, 0.92, roi, 0.08, 0)

                # Add keke label (class 4)
                k_xc = (kx + kw / 2.0) / fw
                k_yc = (ky + kh / 2.0) / fh
                k_bw = kw / fw
                k_bh = kh / fh
                labels.append(f"4 {k_xc:.6f} {k_yc:.6f} {k_bw:.6f} {k_bh:.6f}")

        # Inject trucks onto some frames to learn true truck features
        if random.random() > 0.40:
            truck_crop = create_synthetic_truck_crop()
            tw = random.randint(180, 280)
            th = int(tw * (truck_crop.shape[0] / truck_crop.shape[1]))
            t_resized = cv2.resize(truck_crop, (tw, th))
            if random.random() > 0.5:
                t_resized = cv2.flip(t_resized, 1)
            tx = random.randint(10, max(11, fw - tw - 10))
            ty = random.randint(int(fh * 0.30), max(int(fh * 0.31), fh - th - 10))
            roi = frame_resized[ty:ty+th, tx:tx+tw]
            mask = (t_resized > 10).astype(np.uint8)
            blended = np.where(mask == 1, t_resized, roi)
            frame_resized[ty:ty+th, tx:tx+tw] = cv2.addWeighted(blended, 0.95, roi, 0.05, 0)
            t_xc = (tx + tw / 2.0) / fw
            t_yc = (ty + th / 2.0) / fh
            t_bw = tw / fw
            t_bh = th / fh
            labels.append(f"3 {t_xc:.6f} {t_yc:.6f} {t_bw:.6f} {t_bh:.6f}")

        # Inject Danfo buses onto some frames
        if random.random() > 0.50:
            bus_crop = create_synthetic_bus_crop()
            bw = random.randint(140, 220)
            bh = int(bw * (bus_crop.shape[0] / bus_crop.shape[1]))
            b_resized = cv2.resize(bus_crop, (bw, bh))
            if random.random() > 0.5:
                b_resized = cv2.flip(b_resized, 1)
            bx = random.randint(10, max(11, fw - bw - 10))
            by = random.randint(int(fh * 0.35), max(int(fh * 0.36), fh - bh - 10))
            roi = frame_resized[by:by+bh, bx:bx+bw]
            mask = (b_resized > 10).astype(np.uint8)
            blended = np.where(mask == 1, b_resized, roi)
            frame_resized[by:by+bh, bx:bx+bw] = cv2.addWeighted(blended, 0.92, roi, 0.08, 0)
            b_xc = (bx + bw / 2.0) / fw
            b_yc = (by + bh / 2.0) / fh
            labels.append(f"2 {b_xc:.6f} {b_yc:.6f} {(bw/fw):.6f} {(bh/fh):.6f}")

        # Inject Okadas (motorcycles) onto some frames
        if random.random() > 0.50:
            mc_crop = create_synthetic_motorcycle_crop()
            mw = random.randint(60, 100)
            mh = int(mw * (mc_crop.shape[0] / mc_crop.shape[1]))
            m_resized = cv2.resize(mc_crop, (mw, mh))
            if random.random() > 0.5:
                m_resized = cv2.flip(m_resized, 1)
            mx = random.randint(10, max(11, fw - mw - 10))
            my = random.randint(int(fh * 0.40), max(int(fh * 0.41), fh - mh - 10))
            roi = frame_resized[my:my+mh, mx:mx+mw]
            mask = (m_resized > 10).astype(np.uint8)
            blended = np.where(mask == 1, m_resized, roi)
            frame_resized[my:my+mh, mx:mx+mw] = cv2.addWeighted(blended, 0.90, roi, 0.10, 0)
            m_xc = (mx + mw / 2.0) / fw
            m_yc = (my + mh / 2.0) / fh
            labels.append(f"1 {m_xc:.6f} {m_yc:.6f} {(mw/fw):.6f} {(mh/fh):.6f}")


        img_filename = f"traffic_{sample_id:04d}.jpg"
        lbl_filename = f"traffic_{sample_id:04d}.txt"

        cv2.imwrite(str(target_img_dir / img_filename), frame_resized)
        with open(target_lbl_dir / lbl_filename, "w") as f:
            f.write("\n".join(labels) + "\n")

        if is_val:
            val_count += 1
        else:
            train_count += 1

    # 2. Add dedicated high-resolution reference keke images as standalone training/validation samples
    for idx, (img, name) in enumerate(keke_refs):
        sample_id += 1
        is_val = (idx % 2 == 1)
        target_img_dir = IMAGES_VAL if is_val else IMAGES_TRAIN
        target_lbl_dir = LABELS_VAL if is_val else LABELS_TRAIN

        h, w = img.shape[:2]
        img_640 = cv2.resize(img, (640, 640))
        # Keke covers the central ~75% of these images
        k_xc, k_yc, k_bw, k_bh = 0.50, 0.52, 0.76, 0.74
        labels = [f"4 {k_xc:.6f} {k_yc:.6f} {k_bw:.6f} {k_bh:.6f}"]

        img_filename = f"keke_ref_{sample_id:04d}.jpg"
        lbl_filename = f"keke_ref_{sample_id:04d}.txt"

        cv2.imwrite(str(target_img_dir / img_filename), img_640)
        with open(target_lbl_dir / lbl_filename, "w") as f:
            f.write("\n".join(labels) + "\n")

        if is_val:
            val_count += 1
        else:
            train_count += 1

    # 3. Create dataset YAML file
    yaml_content = f"""# Nigerian Traffic Dataset with Keke (Tricycle) & Truck Separation
path: {DATASET_DIR.as_posix()}
train: images/train
val: images/val

names:
  0: car
  1: motorcycle
  2: bus
  3: truck
  4: keke
"""
    yaml_path = DATASET_DIR / "traffic_keke.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"\nDataset generation complete!")
    print(f"Total training images   : {train_count}")
    print(f"Total validation images : {val_count}")
    print(f"Config YAML saved at    : {yaml_path}")

if __name__ == "__main__":
    build_dataset()
