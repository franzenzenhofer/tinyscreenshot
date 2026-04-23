"""Generate the resolution × color-mode Pareto matrix for a source image.

Usage:
  python run_matrix.py <source.png>       # process existing capture
  python run_matrix.py --capture          # capture main display first

Outputs:
  experiments/out/W<width>-<color>.png    # one file per cell
  experiments/out/results.csv             # row per cell with dims/tokens/bytes
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from PIL import Image

from tinyscreenshot.process import ProcessOptions, process
from tinyscreenshot.tokens import estimate_tokens

WIDTHS = (1280, 1024, 800, 640, 512, 400, 320, 200)
COLORS = ("color", "grey", "mono", "mono-threshold")
OUT_DIR = Path(__file__).parent / "out"


def _save(img: Image.Image, path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=True, compress_level=9)
    return path.stat().st_size


def _source(args: argparse.Namespace) -> Image.Image:
    if args.capture:
        from tinyscreenshot.capture import capture_main
        return capture_main().image
    path = Path(args.source).expanduser()
    if not path.exists():
        sys.exit(f"source not found: {path}")
    with Image.open(path) as im:
        im.load()
        return im.copy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("source", nargs="?", help="path to a source PNG")
    parser.add_argument("--capture", action="store_true", help="capture main display as source")
    args = parser.parse_args()
    if not args.source and not args.capture:
        parser.print_help()
        return 2

    src = _source(args)
    src_w, src_h = src.size
    print(f"source: {src_w}x{src_h}  (~{estimate_tokens(src_w, src_h)} tokens full-res)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "results.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["width_target", "color", "out_w", "out_h", "tokens", "bytes", "file"])

        for w in WIDTHS:
            for c in COLORS:
                opts = ProcessOptions(width=w, color=c)  # type: ignore[arg-type]
                img = process(src, opts)
                name = f"W{w:04d}-{c}.png"
                path = OUT_DIR / name
                size = _save(img, path)
                tokens = estimate_tokens(img.width, img.height)
                writer.writerow([w, c, img.width, img.height, tokens, size, name])
                print(f"  {name:<28}  {img.width}x{img.height:<4}  ~{tokens:4d}t  {size/1024:6.1f} KB")

    print(f"\nwrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
