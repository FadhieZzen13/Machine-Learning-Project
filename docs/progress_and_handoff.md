# Project Progress & Handoff

_Last updated: 2026-06-24 by M3 (tech lead)._

This document records **what has been built so far** and **exactly what Member 1
and Member 2 need to do next**. It is the single status/handoff reference — for
deeper background see [project_plan.md](project_plan.md) and the per-member
[instructions](instructions_member1.md).

---

## Part A — What M3 (tech lead) has done

**System / pipeline (all code complete and verified running):**
- Flask backend ([backend/app.py](../backend/app.py)) — `/health`, `/recommend`
  (LLM + offline) working; `/infer` returns 503 until all models exist (by design).
- Meta-classifier code ([ml/meta_classifier/](../ml/meta_classifier/)) —
  feature extraction (70-dim with 4 models), label harmonisation, build + train scripts.
- LLM recommendations ([ml/llm/recommend_action.py](../ml/llm/recommend_action.py))
  — Gemini with offline fallback.
- Flutter app scaffold ([mobile_app/](../mobile_app/)) — camera → `/infer` →
  overlay → evidence store.

**Data tooling (built this round, reusable by everyone):**
- [ml/data_prep/prepare_dataset.py](../ml/data_prep/prepare_dataset.py) — remaps
  any online YOLO dataset into a member's local 5-class scheme. New capabilities:
  - `--mix-split` — re-splits sources that ship **only** a `train` or `valid`
    folder (most do). **Use this flag.**
  - polygon → bounding-box conversion — several datasets mix segmentation +
    detection labels in one file; the old code silently corrupted those boxes.
- [ml/data_prep/coco_to_yolo.py](../ml/data_prep/coco_to_yolo.py) — converts
  COCO / "COCO segmentation" exports to YOLO. **Needed because several Roboflow
  datasets only offer COCO/CLIP, not YOLOv8.**
- Mapping files in [ml/data_prep/mappings/](../ml/data_prep/mappings/) updated
  with the real class names of the datasets we actually downloaded.

**Member 3 model — TRAINED:**
- `data/member3/` assembled from 4 online datasets (manhole, wires, obstacle,
  branches). 4 of 5 classes have data; `missing_barricade` still needs own photos.
- `yolov8n` trained on GPU (RTX 3050). Weights → `models/member3.pt`.
- See "Known issues" for the class-imbalance caveat.

---

## Part B — Current project status

| Component | Status | Blocked by |
|---|---|---|
| member3 model | ✅ trained (`models/member3.pt`) | needs `missing_barricade` data to be complete |
| member1 model | 🔴 no data yet | M1 must run the steps in Part C |
| member2 model | 🔴 no data yet | M2 must run the steps in Part D |
| member4 model | 🔴 no data yet | M4 must run the steps in Part D2 |
| meta-classifier | 🔴 not started | needs all 4 `.pt` models |
| backend `/infer` | 🟡 returns 503 | needs all 4 models + meta-classifier |
| mobile app | 🟡 scaffolded | needs backend live + device test |
| LLM recommendations | ✅ done | — |

**Critical path: M1, M2 and M4 have zero data. The ensemble cannot exist until
all four models do.** This is the top priority.

> **4th member added.** The group grew from 3 to 4. Member 4 trains a 4th YOLO
> model giving a **second detector** to five classes that previously had only
> one (`open_drain, broken_bench, broken_shelter_panel, exposed_socket,
> fallen_branch`). Global classes stay at 11; the meta-classifier feature vector
> grew **57 → 70 dims** (handled in code via `feature_extraction.MODEL_ORDER`).

---

## Setup (M1 & M2 do this once)

1. Install Python deps: `pip install -r requirements.txt`
2. Confirm GPU works: `python -c "import torch; print(torch.cuda.is_available())"`
   → should print `True`. (CPU works too, just slower.)
3. The pretrained weights file `yolov8n.pt` is already in the repo root.
4. ⚠️ **This machine's SSL blocks in-code downloads.** Download datasets via the
   **browser** (Roboflow → Download Dataset). See
   [ml/data_prep/README.md](../ml/data_prep/README.md).

**The datasets M3 already downloaded are reusable** — they live in
`D:/ML dataset/`. M1 and M2 do **not** need to re-download these for the
overlap classes.

---

## Part C — Member 1 (Ground & surface hazards)

Classes: `pothole, uncovered_manhole, open_drain, cracked_pavement, obstacle_on_walkway`

**Step 1 — reuse the datasets M3 already has** (run from `ml/data_prep/`):
```powershell
# uncovered_manhole  (reuses D:/ML dataset/manhole)
python prepare_dataset.py --source "D:/ML dataset/manhole" --member member1 --mapping mappings/manhole.yaml --mix-split

# obstacle_on_walkway  (reuses D:/ML dataset/obstacle)
python prepare_dataset.py --source "D:/ML dataset/obstacle" --member member1 --mapping mappings/obstacle.yaml --mix-split
```

**Step 2 — download what M3 doesn't have:**
- `pothole` + `cracked_pavement` → download the **malaysia-road-damage-detector**
  dataset (Roboflow `fyp-o8veb`). Then:
  ```powershell
  python prepare_dataset.py --source "C:/Downloads/malaysia-road-damage" --member member1 --mapping mappings/malaysia_road_damage.yaml --mix-split
  ```
  Run `--list` first and fix the mapping to the real class names.
- `open_drain` → **no public dataset found.** Needs own photos (~80) labelled in
  Roboflow, or search "drain"/"open drain"/"storm drain".

**Step 3 — set your data path:** edit `config/member1_data.yaml`, change `path:`
to your absolute path, e.g. `path: D:/Machine Learning Project/data/member1`.

**Step 4 — train:**
```powershell
cd "D:/Machine Learning Project"
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').train(data='config/member1_data.yaml', epochs=100, imgsz=640, batch=8, device=0, patience=20, project='runs', name='member1', exist_ok=True)"
```

**Step 5 — hand off:** copy `runs/detect/runs/member1/weights/best.pt` to
`models/member1.pt` and tell M3.

---

## Part D — Member 2 (Shelter structure & electrical hazards)

Classes: `pothole, dangling_wire, broken_bench, broken_shelter_panel, exposed_socket`

**Step 1 — reuse the datasets M3 already has:**
```powershell
# dangling_wire  (reuses D:/ML dataset/wires2 — 3275 wire boxes)
python prepare_dataset.py --source "D:/ML dataset/wires2" --member member2 --mapping mappings/wire.yaml --mix-split
```

**Step 2 — download what M3 doesn't have:**
- `pothole` → same **malaysia-road-damage-detector** as M1:
  ```powershell
  python prepare_dataset.py --source "C:/Downloads/malaysia-road-damage" --member member2 --mapping mappings/malaysia_road_damage.yaml --mix-split
  ```
- `broken_bench`, `broken_shelter_panel`, `exposed_socket` → **no public
  datasets.** These need own photos (~80 each) labelled in Roboflow. Bus-stop
  benches/shelters and exposed wall sockets are easy to photograph safely.

**Step 3 — set your data path:** edit `config/member2_data.yaml` `path:` to your
absolute path.

**Step 4 — train** (same as M1 but `member2`):
```powershell
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').train(data='config/member2_data.yaml', epochs=100, imgsz=640, batch=8, device=0, patience=20, project='runs', name='member2', exist_ok=True)"
```

**Step 5 — hand off:** copy `best.pt` to `models/member2.pt` and tell M3.

---

## Part D2 — Member 4 (Fixtures, drainage & debris)

Classes: `open_drain, broken_bench, broken_shelter_panel, exposed_socket, fallen_branch`
— **all overlaps**, all second-pass coverage. Full guide:
[instructions_member4.md](instructions_member4.md).

**Step 1 — reuse what M3 already has** (`fallen_branch`):
```powershell
python prepare_dataset.py --source "D:/ML dataset/branches" --member member4 --mapping mappings/branch.yaml --mix-split
```

**Step 2 — own photos for the rest.** `open_drain`, `broken_bench`,
`broken_shelter_panel`, `exposed_socket` have **no public datasets** — they're
bus-stop fixtures, so photograph them directly at the stop (~80 each). Coordinate
with M1 (drain) and M2 (bench/panel/socket) to shoot the **same** objects.

**Step 3 — set path:** edit `config/member4_data.yaml` `path:` to absolute.

**Step 4 — train:**
```powershell
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').train(data='config/member4_data.yaml', epochs=100, imgsz=640, batch=8, device=0, patience=20, project='runs', name='member4', exist_ok=True)"
```

**Step 5 — hand off:** copy `best.pt` to `models/member4.pt` and tell M3.

---

## Part E — Meta-classifier (M3, once all 4 models exist)

1. Assemble a **shared pool** of labelled images (ideally real bus-stop frames)
   that all four models will score on → `data/meta_classifier/`.
2. Build features:
   ```powershell
   python ml/meta_classifier/build_meta_dataset.py --images data/meta_classifier/images --labels data/meta_classifier/labels --out data/meta_classifier/features.npz
   ```
3. Train:
   ```powershell
   python ml/meta_classifier/model.py --features data/meta_classifier/features.npz --out models/meta_classifier.pt
   ```
4. Start backend (`python backend/app.py`), test `/infer`, then run the app.

---

## Part F — Known issues / report notes

- **Class imbalance.** member3 data is skewed: `dangling_wire` (~4,100 boxes) and
  `uncovered_manhole` (~1,200) dominate `obstacle_on_walkway` (356) and
  `fallen_branch` (227). Expect weaker recall on the minority classes; disclose
  this in the report. Same risk applies to M1/M2 — balance where possible.
- **Domain mismatch.** Most online images are highway/street/indoor scenes, not
  Malaysian campus bus stops. Allowed (public images permitted), but mix in own
  bus-stop photos and disclose as a limitation.
- **`missing_barricade` is unusual.** Object detectors find what IS present, not
  what is ABSENT. Group must decide: redefine as `barricade` (detect present
  barricades, infer "missing" by rules) or collect images of clearly unguarded
  hazards. Update `config/classes.yaml` if renamed.
- **Dataset privacy (§7).** The final annotated dataset is shared with the
  instructor via Google Drive, **not** made public. `data/` is git-ignored.
