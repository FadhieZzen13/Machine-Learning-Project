# Datasets (NOT committed to git)

Per assignment: the annotated dataset **must not be made public**. Image and
label files are git-ignored (see root `.gitignore`). **Share via Google Drive
with the course instructor instead.** Only this structure is tracked.

```
data/
  member1/  member2/  member3/        # one per member's YOLO model
    images/train/   images/val/       # .jpg / .png  (80:20 split)
    labels/train/   labels/val/       # YOLO-format .txt, one per image
  meta_classifier/
    features.npz                      # X (N×57 float32), y (global ids) — generated
```

## Requirements (per member)
- 5 classes (see `config/memberN_data.yaml`), ≥ 80 images/class, ≥ 400 total.
- YOLO label format: each line `class_id x_center y_center width height` (normalised 0–1).
- `class_id` is **local** to that member's model (0–4), matching `memberN_data.yaml`.

## Safety
No dangerous situations may be staged. Use existing conditions, safe staged
examples, public images, or synthetic frames only.
