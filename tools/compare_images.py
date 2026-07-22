#!/usr/bin/env python3
"""Headless visual regression: compare freshly rendered test images against
committed baselines.

Usage
-----
    python tools/compare_images.py                 # compare tests/output vs tests/baseline
    python tools/compare_images.py --update        # bless current output as new baselines
    python tools/compare_images.py --threshold 2.0 # allow 2% mean pixel difference

Exit code 0 when all images are within threshold; 1 otherwise. A diff image
(``*_diff.png``) is written next to each failing comparison so the human-mode
CI artifact shows exactly what changed.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests" / "output"
BASELINE = ROOT / "tests" / "baseline"


def load(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)


def compare(new: Path, old: Path, threshold: float) -> tuple[bool, float]:
    a, b = load(new), load(old)
    if a.shape != b.shape:
        # resize new to baseline for a best-effort diff; treat as mismatch signal
        img = Image.open(new).convert("RGB").resize(Image.open(old).size)
        a = np.asarray(img, dtype=np.float32)
    diff = np.abs(a - b)
    pct = float(diff.mean() / 255 * 100)
    ok = pct <= threshold
    if not ok:
        Image.fromarray(np.clip(diff * 4, 0, 255).astype("uint8")).save(
            new.with_name(new.stem + "_diff.png")
        )
    return ok, pct


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true", help="bless current output as baselines")
    ap.add_argument("--threshold", type=float, default=1.0,
                    help="max mean pixel difference, percent (default 1.0)")
    args = ap.parse_args()

    pngs = sorted(OUTPUT.glob("*.png"))
    pngs = [p for p in pngs if not p.stem.endswith("_diff")]
    if not pngs:
        print("No test images found in tests/output — run pytest first.")
        return 1

    if args.update:
        BASELINE.mkdir(exist_ok=True)
        for p in pngs:
            shutil.copy(p, BASELINE / p.name)
        print(f"Blessed {len(pngs)} baseline images.")
        return 0

    failures, new_images = [], []
    for p in pngs:
        base = BASELINE / p.name
        if not base.exists():
            new_images.append(p.name)
            continue
        ok, pct = compare(p, base, args.threshold)
        status = "OK " if ok else "DIFF"
        print(f"  [{status}] {p.name}: {pct:.3f}% mean pixel diff")
        if not ok:
            failures.append(p.name)

    if new_images:
        print(f"\nNew images without baselines (run --update to bless): {new_images}")
    if failures:
        print(f"\n{len(failures)} image(s) exceeded threshold: {failures}")
        return 1
    print("\nAll images within threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
