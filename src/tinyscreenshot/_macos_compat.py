"""Work around ``platform.mac_ver()`` returning an empty version string.

On some macOS builds (seen on macOS 26 / Python 3.14 in sandboxed runners)
``platform.mac_ver()`` returns ``('', ('', '', ''), '')`` even though
``sw_vers -productVersion`` reports the version correctly. The ``mss`` backend
does ``float(".".join(mac_ver()[0].split(".")[:2]))`` at capture time, which
then raises ``ValueError: could not convert string to float: ''`` and breaks
every display/region capture.

We patch ``platform.mac_ver`` once, only when it is actually broken, so mss
(and anything else that relies on it) gets a real version. Idempotent and a
no-op on non-macOS or when ``mac_ver`` already works.
"""

from __future__ import annotations

import platform
import subprocess
import sys

_PATCHED = False


def _product_version() -> str:
    """Return the macOS product version via ``sw_vers``, or '' on failure."""
    try:
        return subprocess.run(
            ["/usr/bin/sw_vers", "-productVersion"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:
        return ""


def ensure_mac_ver() -> None:
    """Patch ``platform.mac_ver`` if it returns an empty version on macOS."""
    global _PATCHED
    if _PATCHED or sys.platform != "darwin":
        return
    if platform.mac_ver()[0]:
        _PATCHED = True
        return
    version = _product_version()
    if not version:
        return  # nothing better to offer; let the original behaviour stand
    original = platform.mac_ver

    def mac_ver_patched(*args, **kwargs):
        release, versioninfo, machine = original(*args, **kwargs)
        if release:
            return release, versioninfo, machine
        return version, versioninfo, machine

    platform.mac_ver = mac_ver_patched  # type: ignore[assignment]
    _PATCHED = True
