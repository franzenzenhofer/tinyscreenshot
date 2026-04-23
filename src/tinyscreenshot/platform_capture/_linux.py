"""Linux capture: Wayland (grim+slurp) or X11 (maim / scrot / ImageMagick import)."""

from __future__ import annotations

import os
import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image

from tinyscreenshot.platform_capture._base import CaptureError, load_png, run


def _is_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def _from_stdout(cmd: list[str], what: str) -> Image.Image:
    result = run(cmd)
    if result.returncode != 0 or not result.stdout:
        err = result.stderr.decode(errors="replace").strip()
        raise CaptureError(f"{what} failed: {err or 'no output'}")
    return Image.open(BytesIO(result.stdout)).copy()


def _from_tempfile(cmd_builder, what: str) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        path = Path(tmp.name)
    try:
        cmd = cmd_builder(str(path))
        result = run(cmd)
        if result.returncode != 0:
            raise CaptureError(f"{what} failed or was cancelled")
        return load_png(path)
    finally:
        path.unlink(missing_ok=True)


def window() -> Image.Image:
    if _is_wayland():
        if not (shutil.which("grim") and shutil.which("slurp")):
            raise CaptureError("Wayland window capture needs 'grim' and 'slurp' installed")
        sel = run(["slurp"]).stdout.decode().strip()
        if not sel:
            raise CaptureError("window selection cancelled")
        return _from_stdout(["grim", "-g", sel, "-"], "grim")
    if shutil.which("maim"):
        return _from_stdout(["maim", "-s"], "maim -s")
    if shutil.which("scrot"):
        return _from_tempfile(lambda p: ["scrot", "-s", p], "scrot -s")
    raise CaptureError("install 'maim' or 'scrot' for X11 window capture")


def app(name: str) -> Image.Image:
    if not shutil.which("xdotool"):
        raise CaptureError("'xdotool' is required to find Linux windows by app name")
    result = run(["xdotool", "search", "--onlyvisible", "--name", name])
    wids = [w for w in result.stdout.decode().split() if w]
    if not wids:
        raise CaptureError(f"no visible windows match name {name!r}")
    wid = wids[0]
    if shutil.which("maim"):
        return _from_stdout(["maim", "-i", wid], f"maim -i {wid}")
    if shutil.which("import"):
        return _from_tempfile(lambda p: ["import", "-window", wid, p], "import -window")
    raise CaptureError("install 'maim' (preferred) or ImageMagick's 'import'")
