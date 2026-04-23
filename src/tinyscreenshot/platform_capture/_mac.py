"""macOS capture via /usr/sbin/screencapture and AppleScript."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image

from tinyscreenshot.platform_capture._base import CaptureError, load_png, run

SCREENCAPTURE = "/usr/sbin/screencapture"
OSASCRIPT = "/usr/bin/osascript"


def _shot(extra_args: list[str]) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        out = Path(tmp.name)
    try:
        result = run([SCREENCAPTURE, "-x", "-t", "png", *extra_args, str(out)])
        if result.returncode != 0:
            err = result.stderr.decode(errors="replace").strip() or "no stderr"
            raise CaptureError(f"screencapture failed (rc={result.returncode}): {err}")
        return load_png(out)
    finally:
        out.unlink(missing_ok=True)


def _window_id_for_app(name: str) -> str:
    script = (
        'try\n'
        '  tell application "System Events"\n'
        f'    set p to first process whose name is "{name}"\n'
        '    return id of window 1 of p\n'
        '  end tell\n'
        'on error\n'
        '  try\n'
        '    tell application "System Events"\n'
        f'      set p to first process whose displayed name is "{name}"\n'
        '      return id of window 1 of p\n'
        '    end tell\n'
        '  end try\n'
        'end try'
    )
    result = run([OSASCRIPT, "-e", script])
    wid = result.stdout.decode().strip()
    if not wid:
        raise CaptureError(
            f"could not find a window for app {name!r} "
            f"(running? has a frontmost window? is Accessibility granted?)"
        )
    return wid


def window(no_shadow: bool = False) -> Image.Image:
    args = ["-W"] + (["-o"] if no_shadow else [])
    return _shot(args)


def app(name: str, no_shadow: bool = False) -> Image.Image:
    wid = _window_id_for_app(name)
    args = ["-l", wid] + (["-o"] if no_shadow else [])
    return _shot(args)


def interactive() -> Image.Image:
    return _shot(["-i"])
