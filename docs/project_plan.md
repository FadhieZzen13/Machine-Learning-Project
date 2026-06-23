# Project Plan — Campus Hazard Detection (Bus Stop & Waiting Area)

**Course:** CSC4602 Machine Learning · **Group size:** 3 · **Zone:** Bus stop & waiting area

This is the working plan. The class design lives in [`config/classes.yaml`](../config/classes.yaml)
and [`global_label_mapping.md`](global_label_mapping.md); this document covers
**roles, architecture, schedule, and how the pieces connect.**

---

## 1. System architecture (assignment §6)

```
Mobile camera frame
   → YOLO model M1 + YOLO model M2 + YOLO model M3   (each: boxes, labels, conf)
   → Label harmonisation   (exact / synonym / parent / contextual)   [label_harmonization.py]
   → IoU box matching → group detections of the same object          [feature_extraction.py]
   → Feature vector per object group                                  [feature_extraction.py]
   → Neural-network meta-classifier → final class + confidence        [model.py]
   → Severity (from config + context)
   → LLM recommended action (Gemini API / offline fallback)           [recommend_action.py]
   → Mobile app overlay: box + final label + confidence + severity + action
```

The feature vector dimension is currently **57** (verified by running
`feature_extraction.py`): per-model blocks (present, confidence, 11-class
one-hot) × 3 + 5 box features + 2 agreement features + 5 zone one-hot + 6 parent
one-hot.

---

## 2. Member roles

**Split:** M1 & M2 are the **data team** (collection + annotation), M3 (project
leader) is the **technical lead** (all shared system code + integration).

> ⚠️ **Hard constraint:** the assignment requires that *each member trains one
> YOLO model* (5 classes) and logs their own man-hours — this is individually
> marked (§16: 15 marks for individual YOLO training). So M1 and M2 cannot be
> purely data-only. The split below keeps their **technical load minimal**: M3
> sets up the training notebook + pipeline, and M1/M2 each just run *their own*
> model's training with it and record the metrics. All other coding is M3's.

| Member | Primary responsibility | Owns (technical) | Report sections led |
|--------|------------------------|------------------|---------------------|
| **M1** (data) | Lead data collection + annotation for the **ground/surface + structural** classes; help annotate across all datasets | Trains **own** YOLO model (M1 classes) using M3's notebook | §4 Data collection & annotation |
| **M2** (data) | Lead data collection + annotation for the **electrical + obstruction/boundary** classes; help annotate across all datasets | Trains **own** YOLO model (M2 classes) using M3's notebook | §4 Data collection & annotation (co-lead) |
| **M3** (lead) | All shared/system engineering + integration | Training pipeline & notebooks, **meta-classifier** (features + NN + eval), **mobile app**, **LLM** integration, end-to-end testing; trains own YOLO model | §3 Architecture, §6 Meta-classifier, §7 App, §8 App testing, §9 Results, §11 LLM |

Shared by all: §1 Introduction, §2 zones/classes, §10 challenges, §11 conclusion,
logbook (each logs their own hours), screencast.

### What each person actually does, concretely

- **M1 & M2 (data team):** scout the bus stop(s); photograph/film the 11 hazard
  types (≥80 imgs/class, ≥400 per member's class set); draw YOLO bounding-box
  annotations (e.g. in Roboflow/LabelImg/CVAT) following the rules in
  `global_label_mapping.md`; do the 80:20 split; hand clean datasets to M3. Each
  then runs their own model's training cell in `train_yolo_template.ipynb` (M3
  sets it up) and records precision/recall/mAP for the report + logbook.
- **M3 (technical lead):** owns every code file in `ml/` and `mobile_app/`;
  builds the meta-classifier (feature extraction → NN → eval), the script that
  turns YOLO outputs into `features.npz`, the LLM integration, and the Flutter
  app; wires the full pipeline together; runs the live demo/testing; trains the
  M3 YOLO model too.

> Each member still **owns one of the three datasets** so the "5 classes / ≥400
> images per student" requirement is met per-person — M1 and M2 take two of the
> three, M3 takes the third. M1/M2 may also help each other and M3 annotate.

---

## 3. Data requirements (assignment §7) — per member

- **5 classes**, **≥ 80 images/class**, **≥ 400 images total** per member.
- YOLO annotation format, **80:20 train/val** split (validation recommended).
- Sources allowed: campus photos, safe staged examples, public images,
  synthetic images, video frames. **No dangerous situations created** (§ safety).
- Overlap classes (pothole, manhole, dangling wire, walkway obstacle): members
  who share a class should ideally photograph the **same** instances from
  different angles so the meta-classifier sees genuine agreement cases.

Folder layout (already created, git-ignored — share via Drive):
```
data/memberN/images/{train,val}/   ← .jpg/.png
data/memberN/labels/{train,val}/   ← YOLO .txt (one per image)
```

---

## 4. Meta-classifier training data — how to generate it

The meta-classifier is **not** trained on raw images; it learns from the YOLO
models' *outputs*. Procedure (M3 owns this):

1. Train all three YOLO models (Phase 2).
2. On a held-out labelled set of bus-stop images, run **all three** models and
   collect every detection as a `Detection` (see `feature_extraction.py`).
3. Group detections by IoU, build a feature vector per group, and label each
   group with the **ground-truth global class** (from your annotations).
4. Save as `data/meta_classifier/features.npz` with arrays `X` (float32,
   N×57) and `y` (int, global ids).
5. `python ml/meta_classifier/model.py --features ... --out models/meta_classifier.pt`

A small script to do steps 2–4 is the next code task (not yet written — it
needs the trained YOLO weights to exist first).

---

## 5. Phased schedule

| Phase | Work | Owner | Output |
|-------|------|-------|--------|
| **0. Foundation** ✅ | Repo structure, class/overlap design, configs, harmonisation + feature + LLM modules, plan | done | this scaffold |
| 1. Proposal | Finalise classes/zones/roles, write proposal | all | proposal doc (deliverable) |
| 2. Data collection + annotation | Collect + annotate ≥400 imgs per dataset, split 80:20 | **M1 & M2 lead** (M3 sets annotation standards & own dataset) | 3 datasets on Drive |
| 3. YOLO training | Train + tune each model, record metrics | **each member trains own model** (M3 provides the pipeline/notebook) | 3× `.pt` + metrics |
| 4. Meta-classifier | features.npz script, train NN, evaluate vs single model | **M3** | `meta_classifier.pt` + eval |
| 5. Mobile app | Flutter app: camera → inference → meta → LLM → overlay | **M3** | app prototype |
| 6. Integration & test | End-to-end live test, latency/lighting notes, ≥5 conflict-resolution examples | **M3 leads**, M1/M2 assist with field testing | test results |
| 7. Report + screencast | Technical report, 8–12 min screencast, logbook | all (per section ownership in §2) | submission package |

---

## 6. Deliverables → rubric mapping (assignment §16, 100 + 5 bonus)

| Rubric component | Marks | Where covered |
|------------------|-------|---------------|
| Class definition, zones, overlap design | 10 | `classes.yaml`, `global_label_mapping.md` |
| Dataset, safety, annotation quality | 15 | `data/`, §4 of report |
| YOLO training, hyperparameters, eval | 15 | per-member notebooks, §5 |
| Meta-classifier design + conflict resolution | 15 | `meta_classifier/`, §6 |
| Mobile app real-time inference | 15 | `mobile_app/`, §7 |
| LLM recommended action | 10 | `recommend_action.py`, §11 |
| Performance analysis & comparison | 10 | §9 results, §13 |
| Report quality | 5 | report |
| Screencast | 3 | screencast |
| Logbook & transparency | 2 | `logbook_template.csv` |
| **Bonus:** distinctive classes for future hierarchy | +5 | parent hierarchy in `classes.yaml` |

---

## 7. Decisions you should confirm as a group

1. **Class split** above is a proposal — confirm it matches what's actually
   present at your chosen bus stop(s). Adjust `classes.yaml` if you swap any.
2. **YOLO version** (e.g. YOLOv8n for on-device speed vs YOLOv8s for accuracy).
3. **Inference location**: on-device (export to TFLite/ONNX) vs backend service
   the app calls. On-device is simpler to demo; backend is easier to integrate
   the meta-classifier + LLM. Pick before Phase 5.
4. **LLM**: Gemini API (needs key, `GEMINI_API_KEY`) vs a local model. The code
   falls back to offline canned actions either way.

## 8. Important safety rule (from the assignment)

Do **not** create real hazards, expose live wires, remove manhole covers, block
fire exits, or enter restricted areas. Use existing/found conditions, safe
staged examples, public images, or synthetic data only.
