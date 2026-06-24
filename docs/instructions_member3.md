# Instructions — Member 3 (Technical Lead / Project Leader)

**Your role:** Own all the code and integration. You build the training pipeline
for the team, the meta-classifier, the mobile app, and the LLM connection — and
you also collect/train **your own** dataset (Model 3) like M1 and M2.

This is the biggest role. Work roughly in the order below.

**Your 5 classes** (from [`config/member3_data.yaml`](../config/member3_data.yaml)):

| Local ID | Class | Notes |
|----------|-------|-------|
| 0 | `uncovered_manhole` | ⭐ overlap — also collected by M1 |
| 1 | `dangling_wire` | ⭐ overlap — also collected by M2 |
| 2 | `obstacle_on_walkway` | ⭐ overlap — also collected by M1 |
| 3 | `fallen_branch` | |
| 4 | `missing_barricade` | |

---

## Part A — Set up the environment & repo 🛠️

**GPU training stack (VERIFIED working on this machine — RTX 3050, CUDA 12.4):**
1. Install **GPU PyTorch FIRST** (order matters — otherwise ultralytics pulls the
   CPU-only torch):
   ```bash
   python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
   python -m pip install ultralytics
   python -m pip install -r requirements.txt   # flask, pyyaml, etc.
   ```
2. Confirm the GPU is seen:
   ```bash
   python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
   # -> True NVIDIA GeForce RTX 3050 Laptop GPU
   ```
3. **Pretrained weights — SSL workaround (IMPORTANT).** This machine's network
   (AV/proxy SSL inspection) breaks ultralytics' auto-download AND Python urllib.
   The working method is `curl --ssl-no-revoke`, wrapped in a helper:
   ```bash
   python ml/notebooks/download_weights.py n     # fetches yolov8n.pt to repo root
   ```
   The training notebook calls this automatically. If you ever see
   `CRYPT_E_NO_REVOCATION_CHECK`, run the helper instead of letting ultralytics
   download.
4. Sanity-check the foundation modules:
   ```bash
   python ml/meta_classifier/label_harmonization.py
   cd ml/meta_classifier && python feature_extraction.py && cd ../..
   python ml/llm/recommend_action.py
   ```
5. **Verify the whole training loop** before real data exists (synthetic data,
   2 epochs on GPU — already confirmed working):
   ```bash
   python ml/notebooks/smoke_test_train.py       # delete ml/notebooks/_smoke/ after
   ```
6. Point M1/M2 to their `docs/instructions_memberN.md`.

> **4 GB VRAM tips:** the smoke test used only 0.18 GB; for real training use
> `yolov8n` + `batch=8` + `imgsz=640` (set in the notebook). Drop `batch`/`imgsz`
> if you ever hit "CUDA out of memory". For faster/heavier runs, Google Colab
> (free T4, 15 GB) runs the same notebook.

---

## Part B — Give M1 & M2 a working training setup 🤖

You own [`ml/notebooks/train_yolo_template.ipynb`](../ml/notebooks/train_yolo_template.ipynb).

1. Confirm it runs end-to-end on a tiny sample (a few labelled images) so the
   team isn't debugging your notebook.
2. Decide **where** training happens: local GPU vs **Google Colab** (recommended
   if laptops are weak). If Colab, make a Colab version that mounts the shared
   Drive and `pip install ultralytics`.
3. Tell M1/M2 to copy it to `train_yolo_member1.ipynb` / `member2` and set the
   `MEMBER` variable. They run their own — but **you provide and support it**.
4. Confirm the class order in each `config/memberN_data.yaml` matches how M1/M2
   set up their annotation tool (mismatched class IDs = silently wrong labels).

---

## Part C — Collect & train your own Model 3 📷🤖

Same as M1/M2 (see their instructions for collection/annotation detail):
- 80+ images per class (~400 total), YOLO format, 80/20 split, files in
  `data/member3/...`, dataset to the shared Drive.
- Train with `MEMBER = "member3"`. Record precision/recall/mAP + confusion matrix.

---

## Part D — Build the meta-classifier 🧠

This is the core of the assignment (15 marks). Pipeline:
`3 YOLO models → harmonise labels → IoU group → feature vector → NN → final class`.

The skeleton already exists:
- [`ml/meta_classifier/label_harmonization.py`](../ml/meta_classifier/label_harmonization.py) — maps each model's local class to the 11 global classes (synonyms, parents, context). ✅ runs.
- [`ml/meta_classifier/feature_extraction.py`](../ml/meta_classifier/feature_extraction.py) — IoU grouping + builds the 57-dim feature vector. ✅ runs.
- [`ml/meta_classifier/model.py`](../ml/meta_classifier/model.py) — PyTorch NN (Dense→ReLU→Dense→ReLU→Softmax) with a train loop. (Needs torch + data.)

**What you still have to do:**
1. **Write the dataset-builder script** (the one piece not yet written). After
   the 3 YOLO models are trained, run all three over a labelled validation set,
   collect detections as `Detection` objects, group by IoU, build a feature
   vector per group, and label each with the **ground-truth** global class. Save
   to `data/meta_classifier/features.npz` (arrays `X` = N×57 float32, `y` = global ids).
   See [`docs/project_plan.md`](project_plan.md) §4 for the exact steps.
2. **Train the meta-classifier:**
   ```bash
   python ml/meta_classifier/model.py --features data/meta_classifier/features.npz --out models/meta_classifier.pt
   ```
3. **Evaluate it:** accuracy, precision, recall, F1, confusion matrix
   (use scikit-learn). **Compare** the meta-classifier vs at least one single
   YOLO model (assignment requires this).
4. **Find ≥5 conflict examples** where two models disagree and the
   meta-classifier picks the right final class — screenshot/document these for
   the report (required).

---

## Part E — Build the mobile app 📱

See [`mobile_app/README.md`](../mobile_app/README.md) for the full plan. Summary:
1. `flutter create` the app (needs Flutter SDK installed).
2. Camera → run inference → harmonise + IoU group + features → meta-classifier
   → severity (from `config/classes.yaml`) → LLM action → draw overlay.
3. **Decide on-device vs backend** (project_plan §7.3). Recommended for the demo:
   a small **backend** (FastAPI/Flask) that reuses your existing Python modules
   (`feature_extraction.py`, `model.py`, `recommend_action.py`) and returns the
   final result — least duplicated code.
4. App must: draw bounding box + final label + confidence + **severity**, show
   the **LLM recommended action**, and **save evidence** (screenshot + timestamp
   + record).

---

## Part F — Connect the LLM 💬

[`ml/llm/recommend_action.py`](../ml/llm/recommend_action.py) already works:
- Set `GEMINI_API_KEY` in the environment → it calls Gemini.
- No key → it returns sensible offline fallback actions (so the demo never crashes).

Your job: wire this into the app/backend so a detected hazard → a short
recommended maintenance action shown on screen.

---

## Part G — Integrate & test end-to-end ✅

- Run the full pipeline live (phone camera at the bus stop, or recorded video).
- Note **latency, false detections, missed detections, lighting sensitivity**
  for the report (assignment §13).
- Lead the integration; M1/M2 can help with field testing.

---

## Report sections you lead ✍️
- §3 System architecture
- §6 Meta-classifier design
- §7 Mobile app implementation
- §8 Mobile app testing
- §9 Results & discussion
- §11 LLM recommended action

Plus: keep your **logbook** (`docs/logbook_template.csv`) daily, and coordinate
the shared sections (intro, conclusion) and the 8–12 min **screencast**.

---

## Your checklist ✅
- [ ] Env set up; foundation modules verified running
- [ ] Training notebook working + handed to M1/M2 (Colab if needed)
- [ ] Class IDs in all 3 `config/memberN_data.yaml` match annotation tools
- [ ] Own dataset (Model 3) collected, trained, metrics recorded
- [ ] Dataset-builder script written → `features.npz` generated
- [ ] Meta-classifier trained + evaluated (acc/P/R/F1/confusion matrix)
- [ ] Meta-classifier compared vs a single YOLO model
- [ ] ≥5 documented conflict-resolution examples
- [ ] Mobile app built (camera → meta-classifier → LLM → overlay + evidence)
- [ ] LLM integrated (Gemini or offline fallback)
- [ ] End-to-end live test + latency/lighting notes
- [ ] Report sections written; logbook kept; screencast organised
