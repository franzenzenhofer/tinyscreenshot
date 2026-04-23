"""Install the bundled Claude Code skill into ~/.claude/skills/tiny-screenshot/."""

from __future__ import annotations

import shutil
import sys
from importlib.resources import files
from pathlib import Path

SKILL_DIR = Path.home() / ".claude" / "skills" / "tiny-screenshot"


def install_skill(force: bool = False) -> Path:
    src = files("tinyscreenshot").joinpath("skill", "SKILL.md")
    dst = SKILL_DIR / "SKILL.md"
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        sys.stderr.write(f"exists (use --force to overwrite): {dst}\n")
        return dst
    with src.open("rb") as fh:
        data = fh.read()
    dst.write_bytes(data)
    sys.stderr.write(f"installed skill: {dst}\n")
    return dst


def uninstall_skill() -> None:
    if SKILL_DIR.exists():
        shutil.rmtree(SKILL_DIR)
        sys.stderr.write(f"removed: {SKILL_DIR}\n")
    else:
        sys.stderr.write(f"not installed: {SKILL_DIR}\n")
