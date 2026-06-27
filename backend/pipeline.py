"""
End-to-end hazard inference pipeline (server side).

Ties together the existing ML modules:
    YOLO models (member1..N)  ->  label harmonisation  ->  IoU grouping
        ->  feature vectors  ->  NN meta-classifier  ->  severity  ->  LLM action

Design goal: **degrade gracefully**. The pipeline imports and runs even when
torch / ultralytics / trained weights are not yet available, so the backend and
the /recommend endpoint work today. /infer reports clearly what is missing until
the models are trained and placed in MODELS_DIR.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

# --- make the existing ml/ modules importable -------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "ml", "meta_classifier"))
sys.path.insert(0, os.path.join(_ROOT, "ml", "llm"))

from label_harmonization import HazardOntology              # noqa: E402
from feature_extraction import (                            # noqa: E402
    Detection, FeatureBuilder, group_detections, MODEL_ORDER,
)
from recommend_action import recommend                      # noqa: E402

MODELS_DIR = os.path.join(_ROOT, "models")
# Expected trained-weight filenames (produced by the YOLO training notebooks).
YOLO_WEIGHTS = {mk: os.path.join(MODELS_DIR, f"{mk}.pt") for mk in MODEL_ORDER}
META_WEIGHTS = os.path.join(MODELS_DIR, "meta_classifier.pt")


@dataclass
class PipelineStatus:
    yolo_ready: dict          # member_key -> bool (weights file present)
    meta_ready: bool
    torch_available: bool
    ultralytics_available: bool

    @property
    def fully_ready(self) -> bool:
        return (all(self.yolo_ready.values()) and self.meta_ready
                and self.torch_available and self.ultralytics_available)

    def missing(self) -> list[str]:
        out = []
        if not self.torch_available:
            out.append("pip install torch")
        if not self.ultralytics_available:
            out.append("pip install ultralytics")
        for mk, ok in self.yolo_ready.items():
            if not ok:
                out.append(f"missing weights: models/{mk}.pt")
        if not self.meta_ready:
            out.append("missing weights: models/meta_classifier.pt")
        return out


class HazardPipeline:
    def __init__(self):
        self.onto = HazardOntology.load()
        self.fb = FeatureBuilder(self.onto)
        self._yolo: dict = {}
        self._meta = None
        self._load_models_if_possible()

    # -- capability checks ----------------------------------------------------
    def status(self) -> PipelineStatus:
        try:
            import torch  # noqa: F401
            torch_ok = True
        except ImportError:
            torch_ok = False
        try:
            import ultralytics  # noqa: F401
            ultra_ok = True
        except ImportError:
            ultra_ok = False
        return PipelineStatus(
            yolo_ready={mk: os.path.exists(p) for mk, p in YOLO_WEIGHTS.items()},
            meta_ready=os.path.exists(META_WEIGHTS),
            torch_available=torch_ok,
            ultralytics_available=ultra_ok,
        )

    def _load_models_if_possible(self):
        st = self.status()
        if not st.fully_ready:
            return  # stay in "recommend-only" mode
        from ultralytics import YOLO
        from model import load_model  # ml/meta_classifier/model.py
        for mk, p in YOLO_WEIGHTS.items():
            self._yolo[mk] = YOLO(p)
        self._meta = load_model(META_WEIGHTS)

    # -- inference ------------------------------------------------------------
    def infer(self, image_path: str, zone_context: str = "unknown",
              conf_thr: float = 0.35) -> list[dict]:
        """Run all YOLO models + meta-classifier on one image.

        Returns a list of final hazard result dicts. Raises RuntimeError with a
        helpful message if the models are not yet available.
        """
        st = self.status()
        if not st.fully_ready:
            raise RuntimeError("Pipeline not ready: " + "; ".join(st.missing()))

        import torch
        from concurrent.futures import ThreadPoolExecutor

        device = "cuda" if torch.cuda.is_available() else "cpu"

        def _run_one(item):
            mk, model = item
            res = model(image_path, conf=conf_thr, iou=0.45, max_det=50,
                        device=device, verbose=False)[0]
            return [
                Detection(
                    model_key=mk,
                    local_class_id=int(b.cls[0].item()),
                    confidence=float(b.conf[0].item()),
                    box_xywhn=tuple(b.xywhn[0].tolist()),
                )
                for b in res.boxes
            ]

        # 1) run all YOLO models in parallel, collect detections
        detections: list[Detection] = []
        with ThreadPoolExecutor(max_workers=len(self._yolo)) as ex:
            for batch in ex.map(_run_one, self._yolo.items()):
                detections.extend(batch)

        # 2) group overlapping detections, 3) build features, 4) meta-classify
        results = []
        for group in group_detections(detections):
            fv = self.fb.build(group, zone_context=zone_context)
            with torch.no_grad():
                logits = self._meta(torch.from_numpy(fv).unsqueeze(0))
                probs = torch.softmax(logits, dim=1)[0]
                gid = int(probs.argmax().item())
                final_conf = float(probs[gid].item())
            name = self.onto.global_classes[gid]
            parent = self.onto.parent_of(name)
            severity = self.onto.severity_of(name)
            box = self._merged_box(group)
            action = recommend({
                "hazard_class": name,
                "general_category": parent or "n/a",
                "zone": zone_context,
                "severity": severity,
                "confidence": round(final_conf, 3),
            })
            results.append({
                "hazard_class": name,
                "general_category": parent,
                "confidence": round(final_conf, 3),
                "severity": severity,
                "box_xywhn": box,
                "num_models_agree": len(group),
                "recommended_action": action,
            })
        return results

    @staticmethod
    def _merged_box(group: list[Detection]) -> list[float]:
        n = len(group)
        cx = sum(d.box_xywhn[0] for d in group) / n
        cy = sum(d.box_xywhn[1] for d in group) / n
        w = sum(d.box_xywhn[2] for d in group) / n
        h = sum(d.box_xywhn[3] for d in group) / n
        return [round(cx, 4), round(cy, 4), round(w, 4), round(h, 4)]


if __name__ == "__main__":
    p = HazardPipeline()
    st = p.status()
    print("Pipeline status:")
    print("  torch:", st.torch_available, " ultralytics:", st.ultralytics_available)
    print("  yolo weights:", st.yolo_ready)
    print("  meta weights:", st.meta_ready)
    print("  fully_ready:", st.fully_ready)
    if not st.fully_ready:
        print("  to finish:", st.missing())
