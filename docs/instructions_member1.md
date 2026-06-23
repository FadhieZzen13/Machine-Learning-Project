# Instructions — Member 1 (Data Team)

**Your role:** Collect and annotate the dataset for **Model 1**, then train your
own YOLO model with the pipeline M3 sets up.

**Your 5 classes** (from [`config/member1_data.yaml`](../config/member1_data.yaml)):

| Local ID | Class | Notes |
|----------|-------|-------|
| 0 | `pothole` | ⭐ overlap — also collected by M2 |
| 1 | `uncovered_manhole` | ⭐ overlap — also collected by M3 |
| 2 | `open_drain` | |
| 3 | `cracked_pavement` | |
| 4 | `obstacle_on_walkway` | ⭐ overlap — also collected by M3 |

> ⭐ **Overlap classes matter.** For `pothole`, `uncovered_manhole`, and
> `obstacle_on_walkway`, try to photograph the **same real objects** that M2/M3
> also shoot (from different angles). The meta-classifier learns from cases
> where two models see the same thing — so genuine shared examples are gold.

---

## Step 1 — Collect images 📷

Go to the campus **bus stop & waiting area**. Photograph each hazard type.

- **Target: at least 80 images per class → ~400+ total.**
- Mix it up: different angles, distances, lighting (morning/afternoon/cloudy),
  close-ups and wide shots. Variety = a better model.
- Video is allowed — you can extract frames later (1 frame every ~1 sec).
- Use your phone; keep decent resolution but you don't need 4K.

**⚠️ Safety (strict rule):** Do **not** create or stage real danger. Don't open
manholes, expose wires, or block exits. Only photograph hazards that **already
exist**, or use safe public/synthetic images to fill gaps.

**Tip:** make a simple count sheet so you don't under-shoot a class:
```
pothole            ▢▢▢▢▢ ... (aim 80)
uncovered_manhole  ▢▢▢▢▢ ...
open_drain         ▢▢▢▢▢ ...
cracked_pavement   ▢▢▢▢▢ ...
obstacle_on_walkway▢▢▢▢▢ ...
```

---

## Step 2 — Annotate (draw boxes) ✏️

Label every image in **YOLO format**. Recommended free tools:
- **Roboflow** (web, easiest, can auto-export YOLO + do the train/val split) — recommended
- or **LabelImg** / **CVAT** (desktop)

Rules:
- Draw a tight box around each hazard. Label **every** hazard in the image, not
  just one.
- Use the **exact class names/IDs** in the table above. Confirm with M3 that
  your tool's class order matches `config/member1_data.yaml` (0–4).
- If unsure whether something is e.g. a `pothole` vs `cracked_pavement`, check
  [`docs/global_label_mapping.md`](global_label_mapping.md) and ask the group —
  keep labelling consistent.

Each image gets a matching `.txt` file. One line per object:
```
<class_id> <x_center> <y_center> <width> <height>   # all 0–1 normalised
```

---

## Step 3 — Split & place the files 📂

Split **80% train / 20% validation**. (Roboflow does this automatically; if
labelling manually, just move ~20% of each class into the val folders.)

Put them here (folders already exist):
```
data/member1/images/train/   ← training photos
data/member1/images/val/     ← validation photos
data/member1/labels/train/   ← matching .txt files
data/member1/labels/val/     ← matching .txt files
```
> These folders are git-ignored on purpose. **Do not** commit images. Upload the
> dataset to the shared **Google Drive** instead (the instructor gets the Drive).

---

## Step 4 — Train your model 🤖

M3 will give you the training notebook. Then:
1. Open [`ml/notebooks/train_yolo_template.ipynb`](../ml/notebooks/train_yolo_template.ipynb)
   (or a copy named `train_yolo_member1.ipynb`).
2. Set `MEMBER = "member1"`.
3. Run the cells (training takes a while — use Google Colab with GPU if your
   laptop is slow; ask M3).
4. **Write down these numbers** for the report + logbook:
   - precision, recall, **mAP@0.5**, **mAP@0.5:0.95**
   - the confusion matrix image (saved automatically by the tool)
5. If a class scores badly, try the improvement ideas in the notebook (more
   images, augmentation) and record it as a second "training iteration."

---

## Step 5 — Write your bit + logbook ✍️

- **Report section: Data collection & annotation** — how/where you collected,
  how many images per class, your labelling rules, the 80/20 split, and your
  model's scores.
- **Logbook** — fill in [`docs/logbook_template.csv`](logbook_template.csv)
  every day you work: date, task, hours, what you produced, problems. Be honest;
  this is graded.

---

## Your checklist ✅
- [ ] 80+ images for each of the 5 classes (~400 total)
- [ ] All images annotated in YOLO format
- [ ] Coordinated overlap classes (pothole/manhole/obstacle) with M2 & M3
- [ ] 80/20 split, files in `data/member1/...`
- [ ] Dataset uploaded to shared Drive
- [ ] Trained Model 1, recorded metrics + confusion matrix
- [ ] Wrote data section of report
- [ ] Logbook kept up to date

**Questions about classes/labels?** → ask M3 (technical lead) or check
`docs/global_label_mapping.md`.
