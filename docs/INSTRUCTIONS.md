# Master Instructions — Complete Workflow

**This is the ONLY instructions document you need.** Follow it in order, top to bottom. No decisions to make, no questions.

---

## Overview

- **Group:** 4 members (M1, M2, M3, M4)
- **M1, M2, M4:** Data team. Collect images, annotate, train your own YOLO model.
- **M3:** Technical lead. Set up pipeline, train your model, build meta-classifier, test end-to-end.
- **Declared zone:** Bus stop & waiting area (Malaysian campus)

**Each member trains ONE 5-class YOLO model.** Assignment requires it (graded individually).

---

## PHASE 1 — Setup (Everyone, 1–2 hours)

### 1.1 — Install (all members)
```powershell
cd "D:/Machine Learning Project"
pip install -r requirements.txt
```

### 1.2 — Verify ML modules work (all members)
```powershell
cd ml/meta_classifier && python label_harmonization.py
python feature_extraction.py
cd ../..
```

### 1.3 — Set your data path (M1, M2, M4 only)
Edit `config/memberN_data.yaml` (where N is your member number):
```yaml
path: D:/Machine Learning Project/data/memberN
```
(Use your actual absolute path.)

---

## PHASE 2 — Data Collection & Annotation (M1, M2, M4)

You each need **≥80 images per class, ≥400 total**. Do this in parallel.

### 2.1 — Download datasets (reuse what M3 already has)

M3 has already downloaded these datasets in `D:/ML dataset/`:
- `manhole/` — for **uncovered_manhole** (M1, M3 share; M1 takes it)
- `obstacle/` — for **obstacle_on_walkway** (M1, M3 share; M1 takes it)
- `wires2/` — for **dangling_wire** (M2, M3 share; M2 takes it)
- `branches/` — for **fallen_branch** (M3, M4 share; M4 takes it)
- `malaysia-road-damage` — for **pothole** + **cracked_pavement** (M1, M2 share; both download once)

**Do this once per dataset you need; reuse across members.**

If a dataset is not there, download from Roboflow **via browser** (not code — SSL will block):
1. Go to the Roboflow URL (listed in [ml/data_prep/README.md](ml/data_prep/README.md))
2. Click **Download Dataset → format YOLOv8 → download zip**
3. Unzip to `D:/ML dataset/<dataset-name>/`

### 2.2 — Remap datasets into your `data/memberN/`

**M1 — Ground & surface hazards** (5 classes):
```powershell
cd "D:/Machine Learning Project/ml/data_prep"

# pothole + cracked_pavement
python prepare_dataset.py --source "D:/ML dataset/malaysia-road-damage" --member member1 --mapping mappings/malaysia_road_damage.yaml --mix-split

# uncovered_manhole
python prepare_dataset.py --source "D:/ML dataset/manhole" --member member1 --mapping mappings/manhole.yaml --mix-split

# obstacle_on_walkway
python prepare_dataset.py --source "D:/ML dataset/obstacle" --member member1 --mapping mappings/obstacle.yaml --mix-split
```

**M2 — Shelter & electrical hazards** (5 classes):
```powershell
cd "D:/Machine Learning Project/ml/data_prep"

# pothole
python prepare_dataset.py --source "D:/ML dataset/malaysia-road-damage" --member member2 --mapping mappings/malaysia_road_damage.yaml --mix-split

# dangling_wire
python prepare_dataset.py --source "D:/ML dataset/wires2" --member member2 --mapping mappings/wire.yaml --mix-split
```

**M4 — Fixtures, drainage & debris** (5 classes):
```powershell
cd "D:/Machine Learning Project/ml/data_prep"

# fallen_branch
python prepare_dataset.py --source "D:/ML dataset/branches" --member member4 --mapping mappings/branch.yaml --mix-split
```

### 2.3 — Collect your own photos (to fill gaps)

**M1** needs own photos for:
- `open_drain` (~80 images)

**M2** needs own photos for:
- `broken_bench` (~80 images)
- `broken_shelter_panel` (~80 images)
- `exposed_socket` (~80 images)

**M4** needs own photos for (all are fixtures; go to the bus stop):
- `open_drain` (~80 images)
- `broken_bench` (~80 images)
- `broken_shelter_panel` (~80 images)
- `exposed_socket` (~80 images)
- (You already have `fallen_branch` from the online dataset)

**How to collect:**
1. Use your phone. Photograph each hazard type ~80+ times, varying angle, distance, lighting.
2. Use [Roboflow](https://roboflow.com/annotate) (free) or LabelImg to draw YOLO-format bounding boxes.
3. Export as YOLO format, copy images + labels to `data/memberN/images/{train,val}/` and `data/memberN/labels/{train,val}/`.
4. **Split 80:20** (80% train, 20% val). Roboflow does this automatically.

**Safety rule (strict):** Do NOT create real hazards. Only photograph existing conditions or use safe public/synthetic images.

### 2.4 — Verify your data

Before training, check:
```powershell
# for your member number (e.g., member1):
ls data/member1/images/train | wc -l    # should be ~300+
ls data/member1/labels/train | wc -l    # same count
```

---

## PHASE 3 — Train Your YOLO Model (M1, M2, M3, M4)

**Run this from the repo root.** Your GPU will be used automatically (RTX 3050 on this machine).

```powershell
cd "D:/Machine Learning Project"

# Replace "member1" with your member number
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').train(data='config/memberN_data.yaml', epochs=100, imgsz=640, batch=8, device=0, patience=20, project='runs', name='memberN', exist_ok=True)"
```

**What to do while it trains:**
- Let it run (~1–2 hours on GPU)
- Go help other members with annotation
- Watch the console output for the final mAP@0.5 scores

**When it finishes:**
1. Copy your best weights to the shared folder:
   ```powershell
   mkdir models
   copy runs/detect/runs/memberN/weights/best.pt models/memberN.pt
   ```
2. **Write down these numbers for your report:**
   - **precision**, **recall**, **mAP@0.5**, **mAP@0.5:0.95**
   - These are printed at the end of training
3. Tell M3: "My model is trained, `models/memberN.pt` is ready."

---

## PHASE 4 — Meta-Classifier (M3 ONLY, after all 4 models exist)

Once M1, M2, M3, and M4 have all trained their models (all four `.pt` files exist in `models/`):

### 4.1 — Build the feature dataset
```powershell
cd "D:/Machine Learning Project"
python ml/meta_classifier/build_meta_dataset.py \
    --images data/meta_classifier/images \
    --labels data/meta_classifier/labels \
    --out data/meta_classifier/features.npz
```

(You need a labelled validation set in `data/meta_classifier/`. If you don't have one yet, hold off — build it after you shoot your own test images.)

### 4.2 — Train the meta-classifier
```powershell
cd "D:/Machine Learning Project"
python ml/meta_classifier/model.py \
    --features data/meta_classifier/features.npz \
    --out models/meta_classifier.pt
```

---

## PHASE 5 — End-to-End Test (M3)

### 5.1 — Start the backend
```powershell
cd "D:/Machine Learning Project"
python backend/app.py
```

Open http://127.0.0.1:5000/health in your browser. You should see:
```json
{
  "status": "ready",
  "torch": true,
  "ultralytics": true,
  "yolo_weights": {"member1": true, "member2": true, "member3": true, "member4": true},
  "meta": true
}
```

### 5.2 — Test /infer
Run a quick test to make sure detection works:
```powershell
curl -X POST http://127.0.0.1:5000/infer \
  -F "image=@some_test_image.jpg" \
  -F "zone=bus_stop"
```

You should see hazard detections with final classes, confidence, severity, and recommended actions.

### 5.3 — Flutter app (optional live test)
If you have a phone:
1. Edit `mobile_app/lib/config.dart`, set `backendBaseUrl` to your machine's LAN IP (not localhost)
2. Run the app, point at a hazard → detections should appear on screen

---

## PHASE 6 — Report & Logbook (All Members)

See [logbook_template.csv](logbook_template.csv) for daily hour tracking.

**Report sections:**
- **M1:** §4 Data collection & annotation (ground/surface hazards)
- **M2:** §4 Data collection & annotation (co-lead with M1; shelter/electrical)
- **M4:** §4 Data collection & annotation (co-lead with M1/M2; fixtures/drainage)
- **M3:** §3 Architecture, §6 Meta-classifier, §7 App, §8 App testing, §9 Results, §11 LLM
- **All:** §1 Introduction, §2 Classes & zones, §10 Challenges, §11 Conclusion, logbook, screencast

---

## Reference: Your 5 Classes

| Member | Class 0 | Class 1 | Class 2 | Class 3 | Class 4 |
|--------|---------|---------|---------|---------|---------|
| **M1** | pothole | uncovered_manhole | open_drain | cracked_pavement | obstacle_on_walkway |
| **M2** | pothole | dangling_wire | broken_bench | broken_shelter_panel | exposed_socket |
| **M3** | uncovered_manhole | dangling_wire | obstacle_on_walkway | fallen_branch | missing_barricade |
| **M4** | open_drain | broken_bench | broken_shelter_panel | exposed_socket | fallen_branch |

---

## Checklist

**M1:**
- [ ] Data path set in `config/member1_data.yaml`
- [ ] ≥80 images per class, ≥400 total
- [ ] Images + labels in `data/member1/images/` and `data/member1/labels/`
- [ ] 80:20 train/val split
- [ ] Model trained, `models/member1.pt` exists
- [ ] Metrics recorded for report
- [ ] Dataset uploaded to Drive
- [ ] Logbook filled in daily

**M2:**
- [ ] Data path set in `config/member2_data.yaml`
- [ ] ≥80 images per class, ≥400 total
- [ ] Images + labels in `data/member2/images/` and `data/member2/labels/`
- [ ] 80:20 train/val split
- [ ] Model trained, `models/member2.pt` exists
- [ ] Metrics recorded for report
- [ ] Dataset uploaded to Drive
- [ ] Logbook filled in daily

**M3:**
- [ ] Data path set in `config/member3_data.yaml`
- [ ] ≥80 images per class, ≥400 total
- [ ] Images + labels in `data/member3/images/` and `data/member3/labels/`
- [ ] 80:20 train/val split
- [ ] Model trained, `models/member3.pt` exists
- [ ] Metrics recorded for report
- [ ] Dataset uploaded to Drive
- [ ] Meta-classifier built + trained
- [ ] Backend `/infer` tested and working
- [ ] Flutter app tested on device
- [ ] Logbook filled in daily

**M4:**
- [ ] Data path set in `config/member4_data.yaml`
- [ ] ≥80 images per class, ≥400 total
- [ ] Images + labels in `data/member4/images/` and `data/member4/labels/`
- [ ] 80:20 train/val split
- [ ] Model trained, `models/member4.pt` exists
- [ ] Metrics recorded for report
- [ ] Dataset uploaded to Drive
- [ ] Logbook filled in daily

---

## Questions?

- **Classes/overlap:** See [docs/global_label_mapping.md](global_label_mapping.md)
- **Architecture:** See [docs/project_plan.md](project_plan.md)
- **Data gaps:** See [ml/data_prep/README.md](../ml/data_prep/README.md)

**No more scattered instructions. This is the flow. Follow it in order.**
