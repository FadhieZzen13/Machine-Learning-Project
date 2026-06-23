"""
Build the meta-classifier training dataset (features.npz).

The meta-classifier learns from the YOLO models' OUTPUTS, not raw pixels. This
script runs all three trained YOLO models over a labelled image set, groups
their detections by IoU, builds one feature vector per object group, and labels
each group with the ground-truth GLOBAL class (matched from the YOLO .txt
labels). It writes X (N x 57) and y (global ids) to a .npz.

Prerequisites (so this can actually run):
  - All 3 YOLO models trained, weights at models/member1.pt, member2.pt, member3.pt
  - A labelled image set: images + YOLO-format .txt label files. The labels must
    use GLOBAL class ids (see config/classes.yaml -> global_classes) so the
    ground truth is unambiguous. The simplest source is a held-out slice you
    re-annotate with global ids, OR convert per-member val labels to global ids.

Usage:
  python build_meta_dataset.py \
      --images ../../data/meta_classifier/images \
      --labels ../../data/meta_classifier/labels \
      --out    ../../data/meta_classifier/features.npz

ultralytics/torch are imported lazily so the rest of the repo doesn't require
them just to import this module.
"""
from __future__ import annotations

import argparse
import glob
import os

import numpy as np

from feature_extraction import (
    Detection, FeatureBuilder, group_detections, MODEL_ORDER, iou_xywhn,
)
from label_harmonization import HazardOntology

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_WEIGHTS = {mk: os.path.join(_ROOT, "models", f"{mk}.pt") for mk in MODEL_ORDER}


def _read_gt_labels(label_path: str) -> list[tuple[int, tuple]]:
    """Read a YOLO .txt of GLOBAL-id labels -> [(global_id, (cx,cy,w,h)), ...]."""
    out = []
    if not os.path.exists(label_path):
        return out
    with open(label_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != 5:
                continue
            cls = int(float(parts[0]))
            box = tuple(float(v) for v in parts[1:5])
            out.append((cls, box))
    return out


def _match_global_class(merged_box: tuple, gt: list[tuple[int, tuple]],
                        iou_thr: float = 0.3) -> int | None:
    """Assign the ground-truth global id whose box best overlaps the group."""
    best_id, best_iou = None, iou_thr
    for cls, box in gt:
        i = iou_xywhn(merged_box, box)
        if i >= best_iou:
            best_id, best_iou = cls, i
    return best_id


def build(images_dir: str, labels_dir: str, out_path: str,
          weights: dict | None = None, conf_thr: float = 0.25):
    from ultralytics import YOLO  # lazy import

    weights = weights or DEFAULT_WEIGHTS
    missing = [p for p in weights.values() if not os.path.exists(p)]
    if missing:
        raise FileNotFoundError(
            "Train the YOLO models first; missing weights:\n  " + "\n  ".join(missing)
        )

    onto = HazardOntology.load()
    fb = FeatureBuilder(onto)
    models = {mk: YOLO(p) for mk, p in weights.items()}

    X_rows, y_rows = [], []
    image_paths = sorted(
        p for ext in ("*.jpg", "*.jpeg", "*.png")
        for p in glob.glob(os.path.join(images_dir, ext))
    )
    print(f"Found {len(image_paths)} images.")

    for img_path in image_paths:
        stem = os.path.splitext(os.path.basename(img_path))[0]
        gt = _read_gt_labels(os.path.join(labels_dir, stem + ".txt"))

        detections: list[Detection] = []
        for mk, model in models.items():
            res = model(img_path, conf=conf_thr, verbose=False)[0]
            for b in res.boxes:
                detections.append(Detection(
                    model_key=mk,
                    local_class_id=int(b.cls[0].item()),
                    confidence=float(b.conf[0].item()),
                    box_xywhn=tuple(b.xywhn[0].tolist()),
                ))

        for group in group_detections(detections):
            fv = fb.build(group, zone_context="bus_stop")
            n = len(group)
            merged = (
                sum(d.box_xywhn[0] for d in group) / n,
                sum(d.box_xywhn[1] for d in group) / n,
                sum(d.box_xywhn[2] for d in group) / n,
                sum(d.box_xywhn[3] for d in group) / n,
            )
            gid = _match_global_class(merged, gt)
            if gid is None:
                continue  # no matching ground-truth box -> skip (likely FP)
            X_rows.append(fv)
            y_rows.append(gid)

    if not X_rows:
        raise RuntimeError("No labelled feature rows produced. Check labels/IoU.")

    X = np.vstack(X_rows).astype(np.float32)
    y = np.array(y_rows, dtype=np.int64)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    np.savez(out_path, X=X, y=y)
    print(f"Saved {X.shape[0]} samples (dim={X.shape[1]}) -> {out_path}")
    print("Class distribution:", dict(zip(*np.unique(y, return_counts=True))))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default="../../data/meta_classifier/images")
    ap.add_argument("--labels", default="../../data/meta_classifier/labels")
    ap.add_argument("--out", default="../../data/meta_classifier/features.npz")
    ap.add_argument("--conf", type=float, default=0.25)
    args = ap.parse_args()
    build(args.images, args.labels, args.out, conf_thr=args.conf)
