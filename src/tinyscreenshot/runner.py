"""Orchestrates: capture → process → save → report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from PIL import Image

from tinyscreenshot.capture import Capture
from tinyscreenshot.process import ProcessOptions, process
from tinyscreenshot.report import print_report

DEFAULT_OUT_DIR = Path("/tmp/tiny-shots")
VALID_EXTS = ("png", "jpg", "jpeg", "webp")


@dataclass
class RunSpec:
    capture_fn: Callable[[], Capture]
    slug: str
    process_opts: ProcessOptions
    out: Path | None = None
    fmt: str | None = None
    quiet: bool = False


def _resolve_out_path(spec: RunSpec) -> tuple[Path, str]:
    if spec.out is not None:
        suffix = spec.out.suffix.lstrip(".").lower() or "png"
        if suffix not in VALID_EXTS:
            raise ValueError(f"output extension must be one of {VALID_EXTS}, got {suffix!r}")
        return spec.out, "jpeg" if suffix == "jpg" else suffix
    fmt = (spec.fmt or "png").lower()
    if fmt not in VALID_EXTS:
        raise ValueError(f"format must be one of {VALID_EXTS}, got {fmt!r}")
    DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = "jpg" if fmt == "jpeg" else fmt
    return DEFAULT_OUT_DIR / f"{ts}-{spec.slug}.{ext}", "jpeg" if fmt == "jpeg" else fmt


def _save(img: Image.Image, path: Path, fmt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs: dict = {}
    save_fmt = fmt.upper()
    if save_fmt == "JPEG":
        save_kwargs.update(quality=82, optimize=True, progressive=True)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    elif save_fmt == "WEBP":
        save_kwargs.update(quality=80, method=6)
    elif save_fmt == "PNG":
        save_kwargs.update(optimize=True, compress_level=9)
    img.save(path, format=save_fmt, **save_kwargs)


def run(spec: RunSpec) -> Path:
    capture = spec.capture_fn()
    src_w, src_h = capture.image.size
    out_img = process(capture.image, spec.process_opts)
    out_path, save_fmt = _resolve_out_path(spec)
    _save(out_img, out_path, save_fmt)
    if not spec.quiet:
        from tinyscreenshot.process import _auto_sharpen
        sharpened = _auto_sharpen(spec.process_opts.color, spec.process_opts.sharpen)
        print_report(
            out_path=out_path,
            source_desc=capture.description,
            src_w=src_w,
            src_h=src_h,
            out_w=out_img.width,
            out_h=out_img.height,
            color=spec.process_opts.color,
            sharpened=sharpened,
            fmt=save_fmt,
        )
    return out_path
