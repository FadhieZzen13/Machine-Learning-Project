# Instructions — Member 4 (Data Team)

**Your role:** Collect and annotate the dataset for **Model 4**, then train your
own YOLO model with the pipeline M3 sets up. Your model is **second-pass
coverage**: every one of your classes is also detected by another member, which
gives the meta-classifier cross-model agreement it didn't have before.

**Your 5 classes** (from [`config/member4_data.yaml`](../config/member4_data.yaml)):

| Local ID | Class | Notes |
|----------|-------|-------|
| 0 | `open_drain` | ⭐ overlap — also collected by M1 |
| 1 | `broken_bench` | ⭐ overlap — also collected by M2 |
| 2 | `broken_shelter_panel` | ⭐ overlap — also collected by M2 |
| 3 | `exposed_socket` | ⭐ overlap — also collected by M2 |
| 4 | `fallen_branch` | ⭐ overlap — also collected by M3 |

> ⭐ **All 5 of your classes are overlaps** — that's the whole point of your
> model. Wherever possible, photograph the **same real objects** that M1/M2/M3
> shoot, from different angles. The meta-classifier learns most from cases where
> two models see the same thing, so genuine shared examples are gold.

---

## Step 1 — Collect images 📷

Go to the campus **bus stop & waiting area**. Your classes are mostly **bus-stop
fixtures**, so this is a good beat to walk:

- `broken_bench`, `broken_shelter_panel`, `exposed_socket` → the shelter itself
  (seats, roof/wall panels, any wall sockets or lighting boxes).
- `open_drain` → kerbside/road drains near the stop.
- `fallen_branch` → debris on the path; trees overhanging the stop.

**Target: at least 80 images per class → ~400+ total.** Vary angle, distance,
and lighting. Video is allowed (extract ~1 frame/sec later).

**⚠️ Safety (strict rule):** Do **not** create or stage danger. Don't pry open
drains, expose sockets, or damage benches/panels. Only photograph hazards that
**already exist**, or use safe public images to fill gaps.

**Datasets that can help (download via browser — see
[ml/data_prep/README.md](../ml/data_prep/README.md)):**
- `fallen_branch` → the **utem/branch-7qne7** dataset M3 already used
  (`D:/ML dataset/branches`). You can reuse it:
  ```powershell
  cd "D:/Machine Learning Project/ml/data_prep"
  python prepare_dataset.py --source "D:/ML dataset/branches" --member member4 --mapping mappings/branch.yaml --mix-split
  ```
- `open_drain`, `broken_bench`, `broken_shelter_panel`, `exposed_socket` →
  **no ready public datasets.** These need your own photos (this is the bulk of
  your job, and it's exactly the bus-stop-specific data the project needs).

---

## Step 2 — Annotate (draw boxes) ✏️

Label every image in **YOLO format**. Recommended: **Roboflow** (web — easiest,
auto-exports YOLO + does the train/val split).

Rules:
- Draw a tight box around each hazard; label **every** hazard in the image.
- Use the **exact class IDs** in the table above (0–4), matching
  `config/member4_data.yaml`.
- For overlap classes, keep your labelling consistent with the other member who
  shares that class — check [`docs/global_label_mapping.md`](global_label_mapping.md)
  and ask the group.

Each image gets a matching `.txt` file, one line per object:
```
<class_id> <x_center> <y_center> <width> <height>   # all 0–1 normalised
```

---

## Step 3 — Split & place the files 📂

Split **80% train / 20% validation** (Roboflow does this automatically). Put
them here (folders already exist):
```
data/member4/images/train/   data/member4/labels/train/
data/member4/images/val/     data/member4/labels/val/
```
> Git-ignored on purpose. **Do not** commit images — upload the dataset to the
> shared **Google Drive** (the instructor gets the Drive).

**If you used the `prepare_dataset.py` command above** for fallen_branch, it
already placed files into `data/member4/...` for you.

---

## Step 4 — Train your model 🤖

1. Set your data path: edit `config/member4_data.yaml`, change `path:` to your
   absolute path, e.g. `path: D:/Machine Learning Project/data/member4`.
2. Train (from the repo root, GPU recommended):
   ```powershell
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').train(data='config/member4_data.yaml', epochs=100, imgsz=640, batch=8, device=0, patience=20, project='runs', name='member4', exist_ok=True)"
   ```
   (If your laptop has no GPU, use Google Colab — ask M3.)
3. **Write down** for the report + logbook: precision, recall, **mAP@0.5**,
   **mAP@0.5:0.95**, and the confusion matrix image (saved automatically).
4. Copy `runs/detect/runs/member4/weights/best.pt` → `models/member4.pt` and
   tell M3.

---

## Step 5 — Write your bit + logbook ✍️

- **Report section: Data collection & annotation** — how/where you collected,
  images per class, labelling rules, the 80/20 split, your model's scores.
- **Logbook** — fill in [`docs/logbook_template.csv`](logbook_template.csv) each
  working day. Be honest; this is graded.

---

## Your checklist ✅
- [ ] 80+ images for each of the 5 classes (~400 total)
- [ ] All images annotated in YOLO format
- [ ] Coordinated overlap classes with M1 (drain), M2 (bench/panel/socket), M3 (branch)
- [ ] 80/20 split, files in `data/member4/...`
- [ ] Dataset uploaded to shared Drive
- [ ] Trained Model 4, recorded metrics + confusion matrix
- [ ] Wrote data section of report
- [ ] Logbook kept up to date

**Questions about classes/labels?** → ask M3 (technical lead) or check
`docs/global_label_mapping.md`.
