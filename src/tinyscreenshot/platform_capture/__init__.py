"""Platform-specific window / app / interactive capture.

mss handles displays and regions. For per-window capture we shell out to native
tools: macOS `screencapture`, Linux `maim`/`grim`. Windows is planned but not
yet supported.
"""

from __future__ import annotations

import platform

from PIL import Image

from tinyscreenshot.platform_capture._base import CaptureError


def capture_window(no_shadow: bool = False) -> Image.Image:
    system = platform.system()
    if system == "Darwin":
        from tinyscreenshot.platform_capture import _mac
        return _mac.window(no_shadow=no_shadow)
    if system == "Linux":
        from tinyscreenshot.platform_capture import _linux
        return _linux.window()
    raise CaptureError(f"window capture not yet supported on {system}")


def capture_app(name: str, no_shadow: bool = False) -> Image.Image:
    system = platform.system()
    if system == "Darwin":
        from tinyscreenshot.platform_capture import _mac
        return _mac.app(name, no_shadow=no_shadow)
    if system == "Linux":
        from tinyscreenshot.platform_capture import _linux
        return _linux.app(name)
    raise CaptureError(f"app capture not yet supported on {system}")


def capture_interactive() -> Image.Image:
    system = platform.system()
    if system == "Darwin":
        from tinyscreenshot.platform_capture import _mac
        return _mac.interactive()
    if system == "Linux":
        from tinyscreenshot.platform_capture import _linux
        return _linux.window()  # slurp/maim -s both draw a rectangle
    raise CaptureError(f"interactive capture not yet supported on {system}")


__all__ = ["CaptureError", "capture_app", "capture_interactive", "capture_window"]
