# Campus Hazard Detection — Bus Stop & Waiting Area

CSC4602 Machine Learning group project (3 members). A mobile app that detects
campus maintenance/safety hazards in real time by combining **three YOLO models**
through a **neural-network meta-classifier**, then suggests a maintenance action
via an **LLM**.

**Declared data-collection zone:** bus stop & waiting area.

## Repository layout
```
config/                  Class & dataset definitions (source of truth)
  classes.yaml             Global + per-member classes, overlap, parents, severity
  memberN_data.yaml        Ultralytics dataset config per member
docs/
  project_plan.md          Roles, architecture, schedule, rubric mapping  ← READ FIRST
  global_label_mapping.md  Overlap / hierarchy table (assignment §5)
  logbook_template.csv     Daily man-hour logbook (assignment §15)
ml/
  notebooks/train_yolo_template.ipynb   Per-member YOLO training template
  meta_classifier/
    label_harmonization.py  Local→global labels, synonyms, parents, context
    feature_extraction.py   IoU grouping + 57-dim feature vectors
    model.py                PyTorch NN meta-classifier (train/load)
  llm/recommend_action.py   Gemini API + offline-fallback recommendations
data/                    Datasets (git-ignored — share via Drive, see §safety)
mobile_app/              Flutter app plan (scaffold with `flutter create`)
```

## Status (foundation)
Scaffolding is in place and the dependency-light modules are **verified to run**:
- `label_harmonization.py` — resolves all member/local classes to global ids ✅
- `feature_extraction.py` — builds 57-dim feature vectors, IoU grouping ✅
- `recommend_action.py` — offline fallback recommendations ✅

Not yet done (needs data / heavy deps / SDKs): collecting & annotating images,
training the YOLO models, generating `features.npz`, training the meta-classifier,
and building the Flutter app. See [docs/project_plan.md](docs/project_plan.md) §5
for the phased schedule.

## Quick start (ML side)
```bash
python -m pip install -r requirements.txt
python ml/meta_classifier/label_harmonization.py     # sanity-check class design
cd ml/meta_classifier && python feature_extraction.py # sanity-check features
```

## Roles
- **M1 & M2 — data team:** lead all data collection + annotation; each trains
  their own YOLO model with M3's pipeline (assignment requires every member to
  train one model).
- **M3 — technical lead (project leader):** all shared/system code — training
  pipeline, meta-classifier, mobile app, LLM integration, end-to-end testing;
  trains own YOLO model too.

Full breakdown: [docs/project_plan.md §2](docs/project_plan.md).

## Class & overlap design at a glance
Each member owns one **dataset/model** of 5 classes (1:1 with the YOLO models):
| Dataset/model | Focus | Overlap classes |
|---------------|-------|-----------------|
| M1 | Ground & surface | pothole, uncovered_manhole, obstacle_on_walkway |
| M2 | Shelter & electrical | pothole, dangling_wire |
| M3 | Obstruction & boundary | uncovered_manhole, dangling_wire, obstacle_on_walkway |

11 global classes total. Full table: [docs/global_label_mapping.md](docs/global_label_mapping.md).

## Safety
No real hazards may be created (no exposed wires, removed covers, blocked exits,
restricted-area entry). Use existing conditions, safe staged examples, public or
synthetic images. Dataset stays private — share with the instructor via Drive.
