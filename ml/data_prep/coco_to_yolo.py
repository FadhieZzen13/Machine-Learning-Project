"""
Convert a Roboflow COCO export into a YOLO-format dataset.

Some Roboflow projects only offer "COCO" / "COCO Segmentation" exports (no
YOLOv8 option). COCO annotations still carry an axis-aligned `bbox`
[x, y, w, h] in absolute pixels, so we can convert them to YOLO detection
labels (class cx cy w h, normalised 0-1) and then feed the result through
`prepare_dataset.py` exactly like any other YOLO dataset.

Input layout (Roboflow COCO):  <source>/<split>/_annotations.coco.json
                               <source>/<split>/<image>.jpg ...
Output layout (YOLO):          <dest>/data.yaml
                               <dest>/<split>/images/<image>.jpg
                               <dest>/<split>/labels/<image>.txt

Usage:
  python coco_to_yolo.py --source "D:/ML dataset/wires" --dest "D:/ML dataset/wires_yolo"
  # then:
  python prepare_dataset.py --source "D:/ML dataset/wires_yolo" --member member3 \
      --mapping mappings/wire.yaml
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

import yaml

_COCO_NAME = "_annotations.coco.json"
_SPLITS = ("train", "valid", "test")


def _find_splits(source: str) -> list[str]:
    """Return split subfolders that contain a COCO json (train/valid/test or flat)."""
    found = [s for s in _SPLITS
             if os.path.isfile(os.path.join(source, s, _COCO_NAME))]
    if found:
        return found
    if os.path.isfile(os.path.join(source, _COCO_NAME)):
        return ["."]  # flat: json sits directly in source
    return []


def _build_category_index(coco: dict) -> tuple[dict[int, int], list[str]]:
    """Map COCO category_id -> contiguous YOLO id; keep only categories that are
    actually used by annotations. Returns (remap, ordered_names)."""
    id_to_name = {c["id"]: c["name"] for c in coco["categories"]}
    used = sorted({a["category_id"] for a in coco["annotations"]})
    remap = {cid: i for i, cid in enumerate(used)}
    names = [id_to_name[cid] for cid in used]
    return remap, names


def _convert_split(source: str, dest: str, split: str,
                   remap: dict[int, int]) -> tuple[int, int]:
    coco_path = os.path.join(source, split, _COCO_NAME) if split != "." \
        else os.path.join(source, _COCO_NAME)
    with open(coco_path, "r", encoding="utf-8") as f:
        coco = json.load(f)

    images = {im["id"]: im for im in coco["images"]}
    # group annotations by image
    by_img: dict[int, list] = {}
    for a in coco["annotations"]:
        by_img.setdefault(a["image_id"], []).append(a)

    out_split = "train" if split == "." else split
    img_out = os.path.join(dest, out_split, "images")
    lbl_out = os.path.join(dest, out_split, "labels")
    os.makedirs(img_out, exist_ok=True)
    os.makedirs(lbl_out, exist_ok=True)

    src_dir = source if split == "." else os.path.join(source, split)
    n_img = n_box = 0
    for img_id, im in images.items():
        fname = im["file_name"]
        src_img = os.path.join(src_dir, fname)
        if not os.path.isfile(src_img):
            continue
        w, h = float(im["width"]), float(im["height"])
        lines = []
        for a in by_img.get(img_id, []):
            cid = a["category_id"]
            if cid not in remap:
                continue
            x, y, bw, bh = a["bbox"]
            cx = (x + bw / 2) / w
            cy = (y + bh / 2) / h
            nw, nh = bw / w, bh / h
            # clamp to [0,1] (COCO boxes occasionally spill past the edge)
            cx, cy = min(max(cx, 0), 1), min(max(cy, 0), 1)
            nw, nh = min(max(nw, 0), 1), min(max(nh, 0), 1)
            if nw <= 0 or nh <= 0:
                continue
            lines.append(f"{remap[cid]} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")
            n_box += 1
        stem = os.path.splitext(fname)[0]
        shutil.copy2(src_img, os.path.join(img_out, fname))
        with open(os.path.join(lbl_out, stem + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        n_img += 1
    return n_img, n_box


def convert(source: str, dest: str) -> None:
    splits = _find_splits(source)
    if not splits:
        raise SystemExit(
            f"No '{_COCO_NAME}' found under {source} (looked in train/valid/test "
            f"and the folder root)."
        )

    # category index comes from the first split's json (Roboflow keeps them
    # consistent across splits)
    first = os.path.join(source, splits[0], _COCO_NAME) if splits[0] != "." \
        else os.path.join(source, _COCO_NAME)
    with open(first, "r", encoding="utf-8") as f:
        remap, names = _build_category_index(json.load(f))

    os.makedirs(dest, exist_ok=True)
    total_img = total_box = 0
    for s in splits:
        ni, nb = _convert_split(source, dest, s, remap)
        out_split = "train" if s == "." else s
        print(f"  {s:6s} -> {out_split:6s}: {ni} images, {nb} boxes")
        total_img += ni
        total_box += nb

    with open(os.path.join(dest, "data.yaml"), "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {"train": "train/images", "val": "valid/images",
             "test": "test/images", "nc": len(names), "names": names},
            f, sort_keys=False,
        )

    print(f"\nClasses kept (YOLO id -> name): "
          f"{ {i: n for i, n in enumerate(names)} }")
    print(f"Total: {total_img} images, {total_box} boxes")
    print(f"Output: {dest}")
    print("Next: run prepare_dataset.py on this --source with a name mapping.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    help="Roboflow COCO export folder (has train/valid/test/_annotations.coco.json)")
    ap.add_argument("--dest", required=True, help="output YOLO dataset folder")
    args = ap.parse_args()
    convert(args.source, args.dest)
