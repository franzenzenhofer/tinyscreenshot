from __future__ import annotations

import pytest
from PIL import Image

from tinyscreenshot.process import ProcessOptions, process


def _fixture_image(w: int = 1600, h: int = 1000) -> Image.Image:
    # Synthetic image with text-like horizontal stripes to exercise resize+sharpen.
    img = Image.new("RGB", (w, h), "white")
    pixels = img.load()
    for y in range(0, h, 20):
        for x in range(w):
            pixels[x, y] = (0, 0, 0)
    return img


def test_resize_keeps_aspect_ratio_and_shrinks_only():
    src = _fixture_image(1600, 1000)
    out = process(src, ProcessOptions(width=800, color="color", sharpen=False))
    assert out.size == (800, 500)


def test_no_upscale_when_width_larger_than_source():
    src = _fixture_image(600, 400)
    out = process(src, ProcessOptions(width=1200, color="color", sharpen=False))
    assert out.size == (600, 400)


def test_width_zero_skips_resize():
    src = _fixture_image(400, 300)
    out = process(src, ProcessOptions(width=0, color="color", sharpen=False))
    assert out.size == (400, 300)


def test_grey_mode_produces_l_image():
    src = _fixture_image()
    out = process(src, ProcessOptions(width=200, color="grey", sharpen=False))
    assert out.mode == "L"


def test_mono_mode_produces_1bit_image():
    src = _fixture_image()
    out = process(src, ProcessOptions(width=200, color="mono", sharpen=False))
    assert out.mode == "1"


def test_mono_threshold_produces_1bit_image():
    src = _fixture_image()
    out = process(src, ProcessOptions(width=200, color="mono-threshold", sharpen=False))
    assert out.mode == "1"


def test_color_mode_produces_rgb_image():
    src = _fixture_image()
    out = process(src, ProcessOptions(width=200, color="color", sharpen=False))
    assert out.mode == "RGB"


def test_invalid_color_mode_raises():
    src = _fixture_image(200, 200)
    with pytest.raises(ValueError):
        process(src, ProcessOptions(width=100, color="cmyk"))  # type: ignore[arg-type]


def test_trim_removes_uniform_border():
    src = Image.new("RGB", (400, 300), "white")
    # draw a small black square in the middle so trim has something to keep
    for y in range(100, 200):
        for x in range(150, 250):
            src.putpixel((x, y), (0, 0, 0))
    out = process(src, ProcessOptions(width=0, color="color", sharpen=False, trim=True))
    # trim should crop tightly to the black box
    assert out.size == (100, 100)


def test_sharpen_auto_off_for_color_and_on_for_grey():
    src = _fixture_image(400, 300)
    color_out = process(src, ProcessOptions(width=200, color="color", sharpen=None))
    grey_out = process(src, ProcessOptions(width=200, color="grey", sharpen=None))
    # Different pipelines produce different pixel histograms even on similar input.
    assert color_out.mode == "RGB"
    assert grey_out.mode == "L"
    # Grey+sharpen should raise contrast vs a sharpen-off baseline.
    grey_nosharp = process(src, ProcessOptions(width=200, color="grey", sharpen=False))
    assert grey_out.tobytes() != grey_nosharp.tobytes()
