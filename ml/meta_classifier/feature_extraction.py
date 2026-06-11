"""
Feature-vector construction for the meta-classifier.

Pipeline position (see architecture in docs/project_plan.md):

  YOLO A/B/C detections  ->  label harmonisation  ->  IoU box matching
                          ->  [THIS MODULE] feature vector  ->  NN meta-classifier

A "candidate" is a cluster of detections from one or more models that refer to
the same physical object (grouped by IoU). For each candidate we build ONE
fixed-length feature vector that the meta-classifier maps to a final global
hazard class.

Feature layout (all fixed length so the NN input size is stable):
  For each of the N_MODELS member models, a per-model block:
    [ present(0/1), confidence, global_class_onehot(C) ]
  Then shared box features:
    [ x, y, w, h, area ]          (normalised, from the merged box)
  Then agreement features:
    [ num_models_agree, mean_pairwise_iou ]
  Then context features:
    [ zone_onehot(Z) ]
  Then parent one-hot:
    [ parent_onehot(P) ]

This module depends only on numpy + label_harmonization (no torch), so the
feature logic is independently testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from label_harmonization import HazardOntology, apply_context

# Order of member models in the per-model feature blocks. Keep stable.
MODEL_ORDER = ["member1", "member2", "member3"]
N_MODELS = len(MODEL_ORDER)

# Zones the app may report (one-hot). Extend to match your declared sub-zones.
ZONES = ["bus_stop", "waiting_area", "boarding_path", "road", "unknown"]


@dataclass
class Detection:
    """One raw YOLO detection from a single model."""
    model_key: str            # "member1" | "member2" | "member3"
    local_class_id: int       # class id local to that model
    confidence: float         # 0..1
    box_xywhn: tuple          # (x_center, y_center, w, h) normalised 0..1


def iou_xywhn(a: tuple, b: tuple) -> float:
    """IoU of two normalised xywh boxes (centre format)."""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax1, ay1, ax2, ay2 = ax - aw / 2, ay - ah / 2, ax + aw / 2, ay + ah / 2
    bx1, by1, bx2, by2 = bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def group_detections(dets: list[Detection], iou_thr: float = 0.5) -> list[list[Detection]]:
    """Greedy IoU clustering: group detections that refer to the same object."""
    groups: list[list[Detection]] = []
    for det in dets:
        placed = False
        for g in groups:
            if any(iou_xywhn(det.box_xywhn, d.box_xywhn) >= iou_thr for d in g):
                g.append(det)
                placed = True
                break
        if not placed:
            groups.append([det])
    return groups


class FeatureBuilder:
    def __init__(self, onto: HazardOntology):
        self.onto = onto
        self.C = onto.num_global_classes
        self.Z = len(ZONES)
        self.P = len(onto.parents)
        self._parent_index = {p: i for i, p in enumerate(onto.parents.keys())}

    @property
    def feature_dim(self) -> int:
        per_model = 1 + 1 + self.C          # present + conf + class one-hot
        return N_MODELS * per_model + 5 + 2 + self.Z + self.P

    def _global_onehot(self, gid: int) -> np.ndarray:
        v = np.zeros(self.C, dtype=np.float32)
        v[gid] = 1.0
        return v

    def build(self, group: list[Detection], zone_context: str = "unknown") -> np.ndarray:
        feats: list[np.ndarray] = []

        # --- per-model blocks ---
        boxes, ious = [], []
        by_model = {d.model_key: d for d in group}  # if dup, keep last; fine for skeleton
        for mk in MODEL_ORDER:
            if mk in by_model:
                d = by_model[mk]
                gid = self.onto.local_to_global_id(mk, d.local_class_id)
                feats.append(np.array([1.0, float(d.confidence)], dtype=np.float32))
                feats.append(self._global_onehot(gid))
                boxes.append(d.box_xywhn)
            else:
                feats.append(np.array([0.0, 0.0], dtype=np.float32))
                feats.append(np.zeros(self.C, dtype=np.float32))

        # --- merged box features (mean of present boxes) ---
        if boxes:
            arr = np.array(boxes, dtype=np.float32)
            x, y, w, h = arr.mean(axis=0)
            area = float(w * h)
        else:
            x = y = w = h = area = 0.0
        feats.append(np.array([x, y, w, h, area], dtype=np.float32))

        # --- agreement features ---
        num_agree = float(len(boxes))
        if len(boxes) >= 2:
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    ious.append(iou_xywhn(boxes[i], boxes[j]))
            mean_iou = float(np.mean(ious))
        else:
            mean_iou = 0.0
        feats.append(np.array([num_agree, mean_iou], dtype=np.float32))

        # --- zone one-hot ---
        zone_vec = np.zeros(self.Z, dtype=np.float32)
        zname = zone_context if zone_context in ZONES else "unknown"
        zone_vec[ZONES.index(zname)] = 1.0
        feats.append(zone_vec)

        # --- parent one-hot (from the highest-confidence detection) ---
        parent_vec = np.zeros(self.P, dtype=np.float32)
        if group:
            top = max(group, key=lambda d: d.confidence)
            tname = self.onto.members[top.model_key][top.local_class_id]
            tname = apply_context(self.onto.normalise(tname), zone_context)
            parent = self.onto.parent_of(tname)
            if parent is not None:
                parent_vec[self._parent_index[parent]] = 1.0
        feats.append(parent_vec)

        return np.concatenate(feats).astype(np.float32)


if __name__ == "__main__":
    onto = HazardOntology.load()
    fb = FeatureBuilder(onto)
    print(f"feature_dim = {fb.feature_dim}")

    # Toy example: member1 and member2 both see a pothole at the same spot.
    dets = [
        Detection("member1", 0, 0.88, (0.50, 0.60, 0.20, 0.15)),  # pothole
        Detection("member2", 0, 0.71, (0.51, 0.61, 0.19, 0.16)),  # pothole
    ]
    groups = group_detections(dets)
    print(f"{len(groups)} candidate group(s)")
    for g in groups:
        fv = fb.build(g, zone_context="bus_stop")
        print("feature vector shape:", fv.shape, "sum:", round(float(fv.sum()), 3))
