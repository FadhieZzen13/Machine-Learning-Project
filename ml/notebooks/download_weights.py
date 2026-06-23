"""
Download pretrained YOLO weights reliably on machines where ultralytics'
auto-download fails with an SSL error (e.g. CRYPT_E_NO_REVOCATION_CHECK from
Windows schannel, common with antivirus/proxy SSL inspection).

It shells out to `curl --ssl-no-revoke -L`, which is the method verified to work
on this project's setup. Files are saved into the repo root so that
`YOLO("yolov8n.pt")` finds them locally and never needs to auto-download.

Usage:
  python ml/notebooks/download_weights.py            # gets yolov8n.pt
  python ml/notebooks/download_weights.py n s        # gets yolov8n.pt + yolov8s.pt
"""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0"


def fetch(name: str) -> bool:
    dest = os.path.join(ROOT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 100_000:
        print(f"  {name} already present, skipping")
        return True
    url = f"{BASE_URL}/{name}"
    print(f"  downloading {name} ...")
    r = subprocess.run(
        ["curl", "-L", "--ssl-no-revoke", "-o", dest, url],
        capture_output=True, text=True,
    )
    ok = os.path.exists(dest) and os.path.getsize(dest) > 100_000
    if not ok:
        print(f"  FAILED ({name}): {r.stderr.strip()[:200]}")
    else:
        print(f"  OK: {name} ({os.path.getsize(dest) / 1e6:.1f} MB)")
    return ok


def main():
    sizes = sys.argv[1:] or ["n"]          # default: nano
    names = [f"yolov8{s}.pt" for s in sizes]
    print(f"Fetching into {ROOT}:")
    results = {n: fetch(n) for n in names}
    if all(results.values()):
        print("All weights ready.")
    else:
        sys.exit("Some downloads failed; see messages above.")


if __name__ == "__main__":
    main()
