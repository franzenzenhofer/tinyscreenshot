"""Image post-processing pipeline: trim → resize → sharpen → color-mode quantize."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PIL import Image, ImageFilter

ColorMode = Literal["color", "grey", "mono", "mono-threshold"]
VALID_COLOR_MODES: tuple[ColorMode, ...] = ("color", "grey", "mono", "mono-threshold")


@dataclass(frozen=True)
class ProcessOptions:
    width: int = 800            # 0 = no resize
    color: ColorMode = "grey"
    sharpen: bool | None = None  # None = auto (on for grey/mono, off for color)
    trim: bool = False


def _auto_sharpen(color: ColorMode, user_choice: bool | None) -> bool:
    if user_choice is not None:
        return user_choice
    return color != "color"


def _resize(img: Image.Image, target_w: int) -> Image.Image:
    if target_w <= 0 or img.width <= target_w:
        return img
    ratio = target_w / img.width
    target_h = max(1, round(img.height * ratio))
    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def _sharpen(img: Image.Image) -> Image.Image:
    # UnsharpMask requires RGB/RGBA/L. Safe at this stage because we sharpen
    # before any 1-bit quantization.
    return img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=75, threshold=2))


def _trim_borders(img: Image.Image) -> Image.Image:
    """Crop uniform edges (like ImageMagick -trim). Returns original if no border."""
    grey = img.convert("L") if img.mode != "L" else img
    bbox = grey.point(lambda p: 0 if 240 <= p <= 255 else 255).getbbox()
    return img.crop(bbox) if bbox else img


def _to_intermediate(img: Image.Image, color: ColorMode) -> Image.Image:
    # RGB for color; L for grey / mono / mono-threshold (1-bit comes after sharpen).
    return img.convert("RGB") if color == "color" else img.convert("L")


def _final_quantize(img: Image.Image, color: ColorMode) -> Image.Image:
    if color in ("color", "grey"):
        return img
    if color == "mono":
        return img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    if color == "mono-threshold":
        return img.point(lambda p: 255 if p >= 128 else 0, mode="1")
    raise ValueError(f"unknown color mode: {color}")


def process(img: Image.Image, opts: ProcessOptions) -> Image.Image:
    """Run the full pipeline and return the processed image."""
    if opts.color not in VALID_COLOR_MODES:
        raise ValueError(f"color must be one of {VALID_COLOR_MODES}, got {opts.color!r}")
    work = img
    if opts.trim:
        work = _trim_borders(work)
    work = _resize(work, opts.width)
    work = _to_intermediate(work, opts.color)
    if _auto_sharpen(opts.color, opts.sharpen):
        work = _sharpen(work)
    return _final_quantize(work, opts.color)
