"""Shared helpers for platform-specific capture backends."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image


class CaptureError(RuntimeError):
    """Raised when a platform-specific capture cannot be performed."""


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=False)


def load_png(path: Path) -> Image.Image:
    if not path.exists() or path.stat().st_size == 0:
        raise CaptureError(f"capture produced no output at {path}")
    with Image.open(path) as im:
        im.load()
        return im.copy()
