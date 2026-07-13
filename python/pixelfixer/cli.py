"""Command-line interface for the pixelfixer detector.

  python -m pixelfixer.cli input.png                 # print detection JSON
  python -m pixelfixer.cli input.png --overlay g.png # save grid overlay
  python -m pixelfixer.cli input.png --extract e.png # save reconstruction
  python -m pixelfixer.cli somefolder --json out.json
"""
import argparse
import glob
import json
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pixelfixer import detect


def _overlay(rgba, r):
    out = rgba[:, :, :3].astype(np.float32).copy()
    h, w = out.shape[:2]
    col = np.array([255, 40, 220], np.float32)
    xs = np.arange(0, w, r["step_x"]).astype(int)
    ys = np.arange(0, h, r["step_y"]).astype(int)
    out[:, np.clip(xs, 0, w - 1)] = 0.75 * col + 0.25 * out[:, np.clip(xs, 0, w - 1)]
    out[np.clip(ys, 0, h - 1), :] = 0.75 * col + 0.25 * out[np.clip(ys, 0, h - 1), :]
    return out.astype(np.uint8)


def _extract(rgba, r, dark_stroke=False):
    from pixelfixer.reconstruct import reconstruct
    return reconstruct(rgba, r["step_x"], r["step_y"], r["cols"], r["rows"],
                       color="mode", palette_snap=False,
                       dark_stroke=dark_stroke)


def main():
    ap = argparse.ArgumentParser(description="pixelfixer grid detector")
    ap.add_argument("input", help="image file or folder")
    ap.add_argument("--overlay", help="save grid overlay PNG")
    ap.add_argument("--extract", help="save reconstruction PNG")
    ap.add_argument("--json", help="save results JSON (folder mode)")
    args = ap.parse_args()

    if os.path.isdir(args.input):
        results = []
        files = sorted(sum((glob.glob(os.path.join(args.input, ext))
                            for ext in ("*.png", "*.jpg", "*.jpeg")), []))
        for p in files:
            rgba = np.array(Image.open(p).convert("RGBA"))
            t0 = time.time()
            r = detect(rgba)
            r["file"] = os.path.basename(p)
            r["dt"] = round(time.time() - t0, 2)
            results.append(r)
            print(f"{r['file'][:46]:48s} {r['cols']}x{r['rows']}  {r['dt']}s")
        if args.json:
            with open(args.json, "w") as f:
                json.dump(results, f, indent=1)
            print("saved", args.json)
        return

    rgba = np.array(Image.open(args.input).convert("RGBA"))
    t0 = time.time()
    r = detect(rgba)
    r["dt"] = round(time.time() - t0, 2)
    print(json.dumps(r, indent=1))
    if args.overlay:
        Image.fromarray(_overlay(rgba, r)).save(args.overlay)
        print("overlay ->", args.overlay)
    if args.extract:
        Image.fromarray(_extract(rgba, r)).save(args.extract)
        print("extract ->", args.extract)


if __name__ == "__main__":
    main()
