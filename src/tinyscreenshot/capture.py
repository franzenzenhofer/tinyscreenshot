"""Screen-capture backends: mss for displays/regions, platform-specific for windows.

mss is imported lazily inside each capture function so that simply importing this
module (e.g. for unit tests that mock the capture functions) does not trigger a
display-backend connection. On Linux without DISPLAY / WAYLAND_DISPLAY, an
import-time mss load would raise at module-load time and break all tests.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from tinyscreenshot.platform_capture import capture_app, capture_interactive, capture_window


@dataclass
class Capture:
    image: Image.Image
    description: str  # human-readable source label for the report


def _mss_to_image(grab) -> Image.Image:
    return Image.frombytes("RGB", grab.size, grab.rgb)


def list_displays() -> list[dict]:
    """Return mss monitor dicts. Index 0 is the 'all monitors' bounding box."""
    import mss
    with mss.mss() as sct:
        return list(sct.monitors)


def capture_all() -> Capture:
    import mss
    with mss.mss() as sct:
        grab = sct.grab(sct.monitors[0])
        n = len(sct.monitors) - 1
    return Capture(_mss_to_image(grab), f"all displays ({n})")


def capture_main() -> Capture:
    import mss
    with mss.mss() as sct:
        if len(sct.monitors) < 2:
            raise RuntimeError("no displays detected")
        grab = sct.grab(sct.monitors[1])
    return Capture(_mss_to_image(grab), "main display")


def capture_display(index: int) -> Capture:
    import mss
    with mss.mss() as sct:
        if index < 1 or index >= len(sct.monitors):
            avail = len(sct.monitors) - 1
            raise ValueError(f"display {index} not found; {avail} display(s) available")
        grab = sct.grab(sct.monitors[index])
    return Capture(_mss_to_image(grab), f"display {index}")


def capture_region(x: int, y: int, w: int, h: int) -> Capture:
    if w <= 0 or h <= 0:
        raise ValueError(f"region width/height must be positive, got {w}x{h}")
    import mss
    with mss.mss() as sct:
        grab = sct.grab({"left": x, "top": y, "width": w, "height": h})
    return Capture(_mss_to_image(grab), f"region {x},{y},{w},{h}")


def capture_window_interactive(no_shadow: bool = False) -> Capture:
    img = capture_window(no_shadow=no_shadow)
    return Capture(img, "window (click-selected)")


def capture_app_by_name(name: str, no_shadow: bool = False) -> Capture:
    img = capture_app(name, no_shadow=no_shadow)
    return Capture(img, f"app {name!r}")


def capture_interactive_selection() -> Capture:
    img = capture_interactive()
    return Capture(img, "interactive selection")
