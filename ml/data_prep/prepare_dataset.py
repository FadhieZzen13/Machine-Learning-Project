"""
Prepare an online YOLO dataset for one of our member models.

Online datasets (Roboflow, Kaggle) each use their OWN class ids and names. To
train a member's 5-class model we must:
  1. keep only the classes we want,
  2. RENAME/REMAP each kept class to our local id (from config/memberN_data.yaml),
  3. copy images + rewritten labels into data/memberN/{images,labels}/{train,val}.

This script does that, driven by a small mapping YAML. It is idempotent-ish:
re-running appends/overwrites the same target files.

Usage:
  python prepare_dataset.py \
      --source  "C:/Downloads/manhole-cover-dataset-yolo" \
      --member  member3 \
      --mapping mappings/manhole_to_member3.yaml

Mapping YAML format (source class name -> our class name, or null to drop):
  source_names_yaml: data.yaml      # optional: source classes file (default: <source>/data.yaml)
  map:
    "Uncovered": uncovered_manhole  # source label "Uncovered" -> our class
    "Covered": null                 # drop this class entirely
"""
from __future__ import annotations

import argparse
import os
import shutil
import random

import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_names(path: str) -> dict[int, str]:
    """Read a YOLO data.yaml 'names' (list or dict) -> {id: name}."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    names = cfg["names"]
    if isinstance(names, list):
        return {i: str(n) for i, n in enumerate(names)}
    return {int(k): str(v) for k, v in names.items()}


def _target_name_to_id(member: str) -> dict[str, int]:
    cfg_path = os.path.join(_ROOT, "config", f"{member}_data.yaml")
    id_to_name = _load_names(cfg_path)
    return {v: k for k, v in id_to_name.items()}


def _norm(s: str) -> str:
    return s.strip().lower().replace("-", "_").replace(" ", "_")


def _discover_splits(source: str) -> list[tuple[str, str, str]]:
    """Find (split_name, images_dir, labels_dir) groups in a source dataset.

    Handles Roboflow layout ({train,valid,test}/images + /labels) and flat
    (images/ + labels/). Returns the source split mapped to our 'train'/'val'.
    """
    found = []
    candidates = {
        "train": "train", "valid": "val", "val": "val", "test": "val",
    }
    for src_split, dest_split in candidates.items():
        img = os.path.join(source, src_split, "images")
        lbl = os.path.join(source, src_split, "labels")
        if os.path.isdir(img) and os.path.isdir(lbl):
            found.append((dest_split, img, lbl))
    if not found:
        img = os.path.join(source, "images")
        lbl = os.path.join(source, "labels")
        if os.path.isdir(img) and os.path.isdir(lbl):
            found.append(("__flat__", img, lbl))
    return found


def _poly_to_bbox(coords: list[str]) -> list[str] | None:
    """Convert a normalised YOLO polygon (x1 y1 x2 y2 ...) to a box cx cy w h."""
    try:
        vals = [float(c) for c in coords]
    except ValueError:
        return None
    xs, ys = vals[0::2], vals[1::2]
    if not xs or not ys:
        return None
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return None
    return [f"{cx:.6f}", f"{cy:.6f}", f"{w:.6f}", f"{h:.6f}"]


def _remap_label_file(src_txt: str, id_remap: dict[int, int]) -> list[str]:
    """Rewrite a label file's class ids; drop lines whose class isn't mapped.

    Handles both detection labels (class cx cy w h) and segmentation labels
    (class x1 y1 x2 y2 ...), converting polygons to bounding boxes. Some Roboflow
    datasets mix both formats in one file.
    """
    out = []
    with open(src_txt, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 5:
                continue
            sid = int(float(parts[0]))
            if sid not in id_remap:
                continue  # class we don't want -> drop this box
            coords = parts[1:]
            if len(coords) == 4:
                box = coords  # already a detection box
            elif len(coords) >= 6 and len(coords) % 2 == 0:
                box = _poly_to_bbox(coords)  # polygon -> bbox
                if box is None:
                    continue
            else:
                continue  # malformed line -> skip
            out.append(" ".join([str(id_remap[sid])] + box))
    return out


def prepare(source: str, member: str, mapping_path: str,
            keep_empty: bool = False, val_ratio: float = 0.2, seed: int = 0,
            mix_split: bool = False):
    # --- build source-id -> target-local-id remap ---
    with open(mapping_path, "r", encoding="utf-8") as f:
        mp = yaml.safe_load(f)
    src_names_yaml = mp.get("source_names_yaml")
    if src_names_yaml:
        if not os.path.isabs(src_names_yaml):
            src_names_yaml = os.path.join(source, src_names_yaml)
    else:
        src_names_yaml = os.path.join(source, "data.yaml")
    src_id_to_name = _load_names(src_names_yaml)
    target_name_to_id = _target_name_to_id(member)

    # normalise the user's map keys for tolerant matching
    user_map = {_norm(k): v for k, v in (mp.get("map") or {}).items()}

    id_remap: dict[int, int] = {}
    report = []
    for sid, sname in src_id_to_name.items():
        target = user_map.get(_norm(sname), "MISSING")
        if target in (None, "", "null"):
            report.append(f"  drop   '{sname}'")
        elif target == "MISSING":
            report.append(f"  IGNORED '{sname}' (not in mapping -> dropped)")
        elif target not in target_name_to_id:
            raise KeyError(
                f"Mapping target '{target}' is not a {member} class. "
                f"Valid: {sorted(target_name_to_id)}"
            )
        else:
            id_remap[sid] = target_name_to_id[target]
            report.append(f"  keep   '{sname}' -> {target} (id {id_remap[sid]})")
    print(f"Class remap for {member}:")
    print("\n".join(report))
    if not id_remap:
        raise SystemExit("No classes mapped; nothing to do.")

    # --- copy + remap ---
    splits = _discover_splits(source)
    if not splits:
        raise SystemExit(f"No images/labels layout found under {source}")

    random.seed(seed)
    counts = {"train": 0, "val": 0, "dropped_empty": 0}
    for dest_split, img_dir, lbl_dir in splits:
        for lbl_name in os.listdir(lbl_dir):
            if not lbl_name.endswith(".txt"):
                continue
            stem = os.path.splitext(lbl_name)[0]
            src_img = _find_image(img_dir, stem)
            if src_img is None:
                continue
            lines = _remap_label_file(os.path.join(lbl_dir, lbl_name), id_remap)
            if not lines and not keep_empty:
                counts["dropped_empty"] += 1
                continue
            ds = dest_split
            if ds == "__flat__" or mix_split:
                ds = "val" if random.random() < val_ratio else "train"
            _write_pair(member, ds, stem, src_img, lines)
            counts[ds] += 1

    print(f"\nDone. train={counts['train']} val={counts['val']} "
          f"(skipped {counts['dropped_empty']} images with no target classes)")
    print(f"Output: data/{member}/")


def _find_image(img_dir: str, stem: str) -> str | None:
    for ext in (".jpg", ".jpeg", ".png", ".JPG", ".PNG"):
        p = os.path.join(img_dir, stem + ext)
        if os.path.exists(p):
            return p
    return None


def _write_pair(member: str, split: str, stem: str, src_img: str, lines: list[str]):
    img_out = os.path.join(_ROOT, "data", member, "images", split)
    lbl_out = os.path.join(_ROOT, "data", member, "labels", split)
    os.makedirs(img_out, exist_ok=True)
    os.makedirs(lbl_out, exist_ok=True)
    ext = os.path.splitext(src_img)[1].lower()
    shutil.copy2(src_img, os.path.join(img_out, stem + ext))
    with open(os.path.join(lbl_out, stem + ".txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="downloaded dataset folder")
    ap.add_argument("--list", action="store_true",
                    help="just print the source dataset's class names and exit")
    ap.add_argument("--member",
                    choices=["member1", "member2", "member3", "member4"])
    ap.add_argument("--mapping", help="mapping YAML path")
    ap.add_argument("--keep-empty", action="store_true",
                    help="keep images that end up with no target boxes (as background)")
    ap.add_argument("--val-ratio", type=float, default=0.2,
                    help="val fraction when the source has no train/val split")
    ap.add_argument("--mix-split", action="store_true",
                    help="ignore the source's train/valid folders and re-split ALL "
                         "images randomly by --val-ratio (use when sources have "
                         "missing or inconsistent splits, e.g. train-only or valid-only)")
    args = ap.parse_args()
    if args.list:
        names = _load_names(os.path.join(args.source, "data.yaml"))
        print(f"Source classes in {args.source}/data.yaml:")
        for i, n in names.items():
            print(f"  {i}: {n}")
        raise SystemExit(0)
    if not (args.member and args.mapping):
        ap.error("--member and --mapping are required (unless --list)")
    prepare(args.source, args.member, args.mapping,
            keep_empty=args.keep_empty, val_ratio=args.val_ratio,
            mix_split=args.mix_split)
