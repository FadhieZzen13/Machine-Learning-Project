# Data preparation — using online datasets

We're sourcing images from public Roboflow/Kaggle datasets instead of (only)
shooting our own. Each online dataset uses **its own class ids/names**, so it
must be **remapped** into our per-member 5-class scheme before training.

`prepare_dataset.py` does the remap + copy into `data/memberN/`.

## Workflow (per dataset)
```bash
# 1) download + unzip the dataset (see "Downloading" below)
# 2) see its real class names:
python ml/data_prep/prepare_dataset.py --source "C:/Downloads/<dataset>" --list
# 3) edit the matching mapping in mappings/ so the source names map to OUR classes
# 4) remap + copy into data/memberN (run once per member that needs those classes):
python ml/data_prep/prepare_dataset.py \
    --source "C:/Downloads/<dataset>" --member member3 --mapping mappings/manhole.yaml
```
Images that end up with no target boxes are skipped (use `--keep-empty` to keep
them as background negatives). Source train/valid/test → our train/val.

## Which dataset feeds which member

| Class | Datasets (yours) | Members that need it | Mapping |
|-------|------------------|----------------------|---------|
| pothole | **malaysia-road-damage-detector** ⭐, potholes-detection-yolov8, road-damage | **M1, M2** | `malaysia_road_damage.yaml` / `pothole_roaddamage.yaml` |
| cracked_pavement | **malaysia-road-damage-detector** ⭐, road-damage | M1 | `malaysia_road_damage.yaml` |
| uncovered_manhole | manhole-cover-dataset-yolo, manhole-c1n3x, (malaysia-road-damage?) | **M1, M3** | `manhole.yaml` |
| obstacle_on_walkway | obstacle-detection-yeuzf, (bus-stop?) | **M1, M3** | `obstacle.yaml` |
| dangling_wire | wire-defect-detection | **M2, M3** | `wire.yaml` |
| fallen_branch | ⚠️ none found — collect/label manually | M3 | (make one) |
| missing_barricade | barricade-detection | M3 | ⚠️ see note |
| open_drain | ⚠️ none listed | M1 | (find/collect) |
| broken_bench | (bus-stop dataset?) | M2 | `bus_stop_domain.yaml` |
| broken_shelter_panel | ⚠️ none listed | M2 | (collect) |
| exposed_socket | electrical search | M2 | (make one) |

⭐ **Malaysian-domain datasets — prefer these.** They match our target context
(Malaysian bus stops / roads) far better than generic highway sets:
- **malaysia-road-damage-detector** (`fyp-o8veb`) → pothole + cracks (M1, M2).
- **bus-stop-7gy2a** (`mtsb`) → real Malaysian bus-stop scenes. Likely
  *infrastructure* classes, not hazards — use it for **domain images / context**
  (re-label hazards, or `--keep-empty` for background). Confirm with `--list`;
  see `bus_stop_domain.yaml`.

> The same online dataset is reused across members — run `prepare_dataset.py`
> once per member with the same mapping; the script picks each member's local id.
> This is what keeps the **overlap classes** (pothole, manhole, wire, obstacle)
> trained in two models, which the meta-classifier needs.

## ⚠️ Important caveats (read before you rely on these)

1. **"missing_barricade" can't be detected the obvious way.** Object detectors
   find things that ARE present, not things that are ABSENT. A barricade dataset
   teaches "here is a barricade", not "a barricade is missing". Options: (a)
   redefine the class as `barricade` (detect present barricades) and derive
   "missing" from context/rules, or (b) collect images of clearly unguarded
   hazards. Decide as a group and update `config/classes.yaml` +
   `global_label_mapping.md` if you rename it. Flag this in the report.

2. **Domain mismatch.** Most of these are highway/street images, not campus bus
   stops. That's allowed (§7 permits public images) but will hurt accuracy on
   real bus-stop frames and must be disclosed in the report's limitations.
   Mix in some of your own bus-stop photos so the model sees the target domain.

3. **Gaps:** open_drain, broken_bench, broken_shelter_panel, exposed_socket, and
   fallen_branch have no ready dataset. These need your own photos (M1/M2/M3) or
   a Google-Images + Roboflow-labelling pass (~80 each).

4. **Label-quality varies.** Spot-check a few converted labels in
   `data/memberN/labels/` after running — wrong source annotations carry through.

## Downloading

**Roboflow** (needs a free account):
- Open the dataset → *Download Dataset* → format **YOLOv8** → *download zip*.
- Unzip; it contains `data.yaml` + `train/ valid/ test/` (the layout this tool expects).

**Kaggle** (needs a free account):
- Easiest: the dataset page → *Download* (zip). Unzip.
- Or CLI: `pip install kaggle`, put `kaggle.json` token in `~/.kaggle/`, then
  `kaggle datasets download -d anggadwisunarto/potholes-detection-yolov8`.

> ⚠️ This machine's SSL inspection blocks some downloads in code (see
> `download_weights.py`). Downloading datasets via the **browser** avoids that.

## Dataset privacy (assignment §7)
The final **annotated dataset you submit** must be shared with the instructor via
Google Drive, **not** made public. Using public datasets as a *source* is fine;
just keep your assembled `data/` private (it's git-ignored).
