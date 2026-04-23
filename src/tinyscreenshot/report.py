"""Stderr report shown after each capture."""

from __future__ import annotations

import sys
from pathlib import Path

from tinyscreenshot.tokens import estimate_tokens


def format_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if num_bytes < 1024 or unit == "MB":
            return f"{num_bytes:.1f} {unit}" if unit != "B" else f"{num_bytes} B"
        num_bytes /= 1024
    return f"{num_bytes:.1f} MB"


def print_report(
    *,
    out_path: Path,
    source_desc: str,
    src_w: int,
    src_h: int,
    out_w: int,
    out_h: int,
    color: str,
    sharpened: bool,
    fmt: str,
) -> None:
    tokens = estimate_tokens(out_w, out_h)
    src_tokens = estimate_tokens(src_w, src_h)
    size = out_path.stat().st_size if out_path.exists() else 0
    sharp = " +sharpen" if sharpened else ""
    saved = src_tokens - tokens
    savings = f" (saved ~{saved}t vs full source)" if saved > 0 else ""

    lines = [
        f"captured: {out_path}",
        f"  source: {src_w}x{src_h}  ({source_desc})",
        f"  output: {out_w}x{out_h}  {color}{sharp}  [{fmt}]",
        f"  tokens: ~{tokens}{savings}",
        f"  size:   {format_size(size)}",
    ]
    sys.stderr.write("\n".join(lines) + "\n")
