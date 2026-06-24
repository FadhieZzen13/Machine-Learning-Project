# What "class" means (and how many photos you need)

## A "class" = one type of hazard the model learns to recognise

In object detection, a **class** is a category/label. Our model doesn't just
find "a hazard" — it must say **which kind**. Each kind is one class.

Each member's YOLO model is trained on **5 classes**:

| Member | The 5 classes (categories) it detects |
|--------|----------------------------------------|
| M1 | pothole · uncovered_manhole · open_drain · cracked_pavement · obstacle_on_walkway |
| M2 | pothole · dangling_wire · broken_bench · broken_shelter_panel · exposed_socket |
| M3 | uncovered_manhole · dangling_wire · obstacle_on_walkway · fallen_branch · missing_barricade |
| M4 | open_drain · broken_bench · broken_shelter_panel · exposed_socket · fallen_branch |

When you annotate a photo, you draw a box around each hazard **and pick which of
those 5 classes it is**. The model learns "this shape/look = pothole",
"that = dangling_wire", etc. Across all 4 members there are **11 distinct
classes** total (some are shared on purpose — those are the *overlap* classes).
M4's 5 classes are all overlaps — it's a second detector for hazards that
otherwise only one member would catch.

## "Per class" vs "per member" — important

The two numbers measure different things:
- **Images per class** = how many photos contain that one hazard type.
- **Images per member** = total photos for that member (across all 5 classes).

A single photo can contain several classes, so it can count toward more than one
class's total.

## ⚠️ Photo-count target — please confirm

The assignment minimum (§7) is:
- **≥ 80 images per class**, and
- **≥ 400 images per member** (≈ 80 × 5).

Your group said **"~100 per member."** If that means **100 photos total per
member**, that's only about **20 per class** — which is **below the minimum on
both counts** and risks the 15-mark dataset rubric.

**Recommended reading: ~100 images _per class_** → ~500 per member. That
comfortably clears the minimum and gives each class enough examples to train
well. If collecting 80–100 of a rare class is hard, prioritise:
1. the **overlap classes** (pothole, uncovered_manhole, dangling_wire,
   obstacle_on_walkway) — they need the most examples, and
2. fill gaps with **safe public/synthetic images** (allowed by §7).

| Plan | Per class | Per member | Meets §7 minimum? |
|------|-----------|-----------|-------------------|
| "100 per member" (total) | ~20 | ~100 | ❌ no |
| **100 per class (recommended)** | ~100 | ~500 | ✅ yes (comfortably) |
| Bare minimum | 80 | 400 | ✅ just meets it |

> **Action:** decide as a group which target you mean, then tell me and I'll set
> the number consistently across `project_plan.md` and the member instructions.
> Until then the instruction files keep the safe **80/class, 400/member** figure.
