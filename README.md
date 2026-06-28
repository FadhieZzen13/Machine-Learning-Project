# Campus Hazard Detection — Bus Stop & Waiting Area

CSC4602 Machine Learning group project (4 members). A mobile app that detects
campus maintenance/safety hazards in real time by combining **four YOLO models**
through a **neural-network meta-classifier**, then suggests a maintenance action
via an **LLM**.

Member 1-Varshan
Member 2-Reydan
Member 3-Fadhie
Member 4-Ahmad Ilham Zuhairi


**Declared data-collection zone:** bus stop & waiting area.

## Repository layout
```
config/                  Class & dataset definitions (source of truth)
  classes.yaml             Global + per-member classes, overlap, parents, severity
  memberN_data.yaml        Ultralytics dataset config per member
docs/
  project_plan.md          Roles, architecture, schedule, rubric mapping  ← READ FIRST
  classes_explained.md     What "class" means + photo-count targets
  global_label_mapping.md  Overlap / hierarchy table (assignment §5)
  instructions_memberN.md  Step-by-step guide per member
  logbook_template.csv     Daily man-hour logbook (assignment §15)
ml/
  notebooks/train_yolo_template.ipynb   Per-member YOLO training template
  meta_classifier/
    label_harmonization.py  Local→global labels, synonyms, parents, context
    feature_extraction.py   IoU grouping + 70-dim feature vectors (4 models)
    model.py                PyTorch NN meta-classifier (train/load)
    build_meta_dataset.py   Run YOLO models → build features.npz for the NN
  llm/recommend_action.py   Gemini API + offline-fallback recommendations
backend/                 Flask inference service the app calls
  app.py                   /health, /recommend, /infer endpoints
  pipeline.py              Full pipeline (graceful until models exist)
mobile_app/              Flutter app (lib/ scaffolded; run `flutter create .`)
data/                    Datasets (git-ignored — share via Drive, see §safety)
```

## Status
**Verified to run** (executed this session):
- `label_harmonization.py` — resolves all member/local classes to global ids ✅
- `feature_extraction.py` — builds 70-dim feature vectors (4 models), IoU grouping ✅
- `recommend_action.py` — offline fallback recommendations ✅
- `build_meta_dataset.py` — imports + ground-truth matching logic ✅
- **backend** `/health` + `/recommend` (Flask test client) ✅; `/infer` returns a
  clear 503 listing what's missing until models are trained ✅

**Scaffolded, not yet runnable end-to-end** (needs data / heavy deps / SDKs):
- Flutter app `lib/` written — needs `flutter create .` + `flutter pub get`
- YOLO training, `features.npz` generation, meta-classifier training — need the
  collected datasets + `pip install torch ultralytics`

See [docs/project_plan.md](docs/project_plan.md) §5 for the phased schedule.

## Quick start
```bash
python -m pip install -r requirements.txt
# sanity-check the ML modules
python ml/meta_classifier/label_harmonization.py
cd ml/meta_classifier && python feature_extraction.py && cd ../..
# run the backend (app talks to this)
python backend/app.py            # http://127.0.0.1:5000  (GET /health)
```

## Roles
- **M1, M2 & M4 — data team:** lead all data collection + annotation; each trains
  their own YOLO model with M3's pipeline (assignment requires every member to
  train one model). M4 gives second-pass coverage of under-detected classes.
- **M3 — technical lead (project leader):** all shared/system code — training
  pipeline, meta-classifier, mobile app, LLM integration, end-to-end testing;
  trains own YOLO model too.

Full breakdown: [docs/project_plan.md §2](docs/project_plan.md).

## Class & overlap design at a glance
Each member owns one **dataset/model** of 5 classes (1:1 with the YOLO models):
| Dataset/model | Focus | Overlap classes |
|---------------|-------|-----------------|
| M1 | Ground & surface | pothole, uncovered_manhole, open_drain, obstacle_on_walkway |
| M2 | Shelter & electrical | pothole, dangling_wire, broken_bench, broken_shelter_panel, exposed_socket |
| M3 | Obstruction & boundary | uncovered_manhole, dangling_wire, obstacle_on_walkway, fallen_branch |
| M4 | Fixtures, drainage & debris | open_drain, broken_bench, broken_shelter_panel, exposed_socket, fallen_branch |

11 global classes total. M4 is second-pass coverage — all its classes overlap.
Full table: [docs/global_label_mapping.md](docs/global_label_mapping.md).

## Safety
No real hazards may be created (no exposed wires, removed covers, blocked exits,
restricted-area entry). Use existing conditions, safe staged examples, public or
synthetic images. Dataset stays private — share with the instructor via Drive.
