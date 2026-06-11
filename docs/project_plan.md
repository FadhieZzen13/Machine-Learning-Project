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

Each member owns one YOLO model (5 classes) **and** a slice of the shared work.

| Member | YOLO model (own) | Shared system component | Report sections led |
|--------|------------------|-------------------------|---------------------|
| **M1** | Ground & surface hazards | Dataset pipeline + annotation standards + data split scripts | §4 Data collection, §5 (training, own model) |
| **M2** | Shelter structure & electrical | Meta-classifier (feature extraction + NN training + eval) | §6 Meta-classifier, §9 Results |
| **M3** | Obstruction & boundary | Mobile app (Flutter) + LLM integration | §7 App, §8 App testing, §11 LLM |

Shared by all: §1 Introduction, §2 zones/classes, §3 architecture, §10
challenges, §11 conclusion, logbook (each logs their own hours), screencast.

> Roles are a starting split — adjust to your group's strengths. Everyone must
> train their own YOLO model regardless (assignment requirement).

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
models' *outputs*. Procedure (M2 owns this):

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
| 2. Data | Collect + annotate ≥400 imgs each, split 80:20 | each member | datasets on Drive |
| 3. YOLO training | Train + tune each model, record metrics | each member | 3× `.pt` + metrics |
| 4. Meta-classifier | Generate features.npz, train NN, evaluate vs single model | M2 | `meta_classifier.pt` + eval |
| 5. Mobile app | Flutter app: camera → inference → meta → LLM → overlay | M3 | app prototype |
| 6. Integration & test | End-to-end live test, latency/lighting notes, ≥5 conflict-resolution examples | all | test results |
| 7. Report + screencast | Technical report, 8–12 min screencast, logbook | all | submission package |

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
