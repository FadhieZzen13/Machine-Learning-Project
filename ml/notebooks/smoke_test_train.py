"""
Smoke test: prove the YOLO training setup works on this machine BEFORE real
data exists. Creates a tiny synthetic dataset (a few images with one coloured
box each), writes a temporary data.yaml, and runs 2 training epochs on the GPU.

This is NOT part of the real project — it only verifies that
torch + ultralytics + GPU + the train/val loop all work end to end. Delete the
generated `_smoke/` folder afterwards.

Run:  python ml/notebooks/smoke_test_train.py
"""
from __future__ import annotations

import os
import random

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "_smoke")


def make_image(path: str, label_path: str, cls: int):
    """Draw one filled rectangle on noise; write its YOLO label."""
    W = H = 320
    arr = (np.random.rand(H, W, 3) * 60).astype("uint8")
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    bw, bh = random.randint(40, 90), random.randint(40, 90)
    cx, cy = random.randint(bw, W - bw), random.randint(bh, H - bh)
    color = (220, 60, 60) if cls == 0 else (60, 120, 220)
    d.rectangle([cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2], fill=color)
    img.save(path)
    # YOLO label: class cx cy w h (normalised)
    with open(label_path, "w") as f:
        f.write(f"{cls} {cx / W:.4f} {cy / H:.4f} {bw / W:.4f} {bh / H:.4f}\n")


def build_dataset():
    for split, n in (("train", 8), ("val", 4)):
        for sub in ("images", "labels"):
            os.makedirs(os.path.join(ROOT, sub, split), exist_ok=True)
        for i in range(n):
            cls = i % 2
            stem = f"{split}_{i}"
            make_image(
                os.path.join(ROOT, "images", split, stem + ".jpg"),
                os.path.join(ROOT, "labels", split, stem + ".txt"),
                cls,
            )
    yaml_path = os.path.join(ROOT, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(
            f"path: {ROOT}\n"
            "train: images/train\n"
            "val: images/val\n"
            "names:\n  0: red_box\n  1: blue_box\n"
        )
    return yaml_path


def main():
    from ultralytics import YOLO

    data_yaml = build_dataset()
    print("Synthetic dataset at:", ROOT)

    model = YOLO("yolov8n.pt")  # downloads ~6 MB pretrained weights on first run
    model.train(
        data=data_yaml,
        epochs=2,
        imgsz=320,
        batch=4,          # safe for 4 GB VRAM
        device=0,         # use the RTX 3050; set "cpu" to force CPU
        project=os.path.join(ROOT, "runs"),
        name="smoke",
        verbose=True,
    )
    print("\n✅ Training loop works. Setup is good.")
    print("   Delete ml/notebooks/_smoke/ when done.")


if __name__ == "__main__":
    main()
