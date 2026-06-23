# Instructions — Member 2 (Data Team)

**Your role:** Collect and annotate the dataset for **Model 2**, then train your
own YOLO model with the pipeline M3 sets up. (Same workflow as M1 — different
hazards.)

**Your 5 classes** (from [`config/member2_data.yaml`](../config/member2_data.yaml)):

| Local ID | Class | Notes |
|----------|-------|-------|
| 0 | `pothole` | ⭐ overlap — also collected by M1 |
| 1 | `dangling_wire` | ⭐ overlap — also collected by M3 |
| 2 | `broken_bench` | seating in the waiting area |
| 3 | `broken_shelter_panel` | roof/ceiling panels of the shelter |
| 4 | `exposed_socket` | damaged power sockets / lighting points |

> ⭐ **Overlap classes matter.** For `pothole` and `dangling_wire`, photograph
> the **same real objects** that M1/M3 also shoot (different angles). Genuine
> shared examples are what train the meta-classifier's agreement features.

---

## Step 1 — Collect images 📷

Go to the campus **bus stop & waiting area**. Photograph each hazard type.

- **Target: at least 80 images per class → ~400+ total.**
- Vary angle, distance, lighting (morning/afternoon/cloudy), close + wide.
- Video allowed — extract frames later (~1 frame/sec).
- For `broken_bench`, `broken_shelter_panel`, `exposed_socket`: focus on the
  **shelter structure and lighting/electrical fittings** around the stop.

**⚠️ Safety (strict rule):** Do **not** create danger. Never touch or expose
live wires/sockets — photograph from a safe distance only. Use existing
conditions or safe public/synthetic images to fill gaps.

**Tip — count sheet:**
```
pothole              ▢▢▢▢▢ ... (aim 80)
dangling_wire        ▢▢▢▢▢ ...
broken_bench         ▢▢▢▢▢ ...
broken_shelter_panel ▢▢▢▢▢ ...
exposed_socket       ▢▢▢▢▢ ...
```

---

## Step 2 — Annotate (draw boxes) ✏️

Label every image in **YOLO format**. Recommended: **Roboflow** (web, easiest),
or LabelImg / CVAT (desktop).

Rules:
- Tight box around each hazard; label **every** hazard in the image.
- Use the **exact class names/IDs** above; confirm the order matches
  `config/member2_data.yaml` (0–4) with M3.
- `exposed_socket` vs `dangling_wire`: both are electrical but **different** —
  don't mix them. A loose hanging wire = `dangling_wire`; a broken/open wall
  socket = `exposed_socket`. See [`docs/global_label_mapping.md`](global_label_mapping.md).

Each image → one `.txt`. One line per object:
```
<class_id> <x_center> <y_center> <width> <height>   # all 0–1 normalised
```

---

## Step 3 — Split & place the files 📂

Split **80% train / 20% val**. Put them here:
```
data/member2/images/train/   data/member2/images/val/
data/member2/labels/train/   data/member2/labels/val/
```
> Git-ignored on purpose — **don't commit images**. Upload to the shared
> **Google Drive** instead.

---

## Step 4 — Train your model 🤖

Using M3's notebook:
1. Open a copy of [`ml/notebooks/train_yolo_template.ipynb`](../ml/notebooks/train_yolo_template.ipynb)
   named `train_yolo_member2.ipynb`.
2. Set `MEMBER = "member2"`.
3. Run it (use Google Colab GPU if your laptop is slow — ask M3).
4. **Record:** precision, recall, **mAP@0.5**, **mAP@0.5:0.95**, and the
   confusion matrix image.
5. If a class is weak, retry with more images/augmentation and log it as a
   second training iteration.

---

## Step 5 — Write your bit + logbook ✍️

- **Report section: Data collection & annotation (co-lead with M1)** — your
  collection method, image counts per class, labelling rules, split, model scores.
- **Logbook** — update [`docs/logbook_template.csv`](logbook_template.csv) daily:
  date, task, hours, output, problems. Honest hours = graded.

---

## Your checklist ✅
- [ ] 80+ images for each of the 5 classes (~400 total)
- [ ] All images annotated in YOLO format
- [ ] Coordinated overlap classes (pothole/dangling_wire) with M1 & M3
- [ ] 80/20 split, files in `data/member2/...`
- [ ] Dataset uploaded to shared Drive
- [ ] Trained Model 2, recorded metrics + confusion matrix
- [ ] Wrote data section of report
- [ ] Logbook kept up to date

**Questions about classes/labels?** → ask M3 (technical lead) or check
`docs/global_label_mapping.md`.
