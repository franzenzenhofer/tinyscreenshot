from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import tinyscreenshot.skill_install as si


def test_install_skill_writes_file(tmp_path: Path):
    target_dir = tmp_path / ".claude" / "skills" / "tiny-screenshot"
    with patch.object(si, "SKILL_DIR", target_dir):
        path = si.install_skill()
    assert path.exists()
    assert path.read_text().startswith("---")
    assert "tiny-screenshot" in path.read_text()


def test_install_skill_no_overwrite_without_force(tmp_path: Path):
    target_dir = tmp_path / ".claude" / "skills" / "tiny-screenshot"
    target_dir.mkdir(parents=True)
    (target_dir / "SKILL.md").write_text("custom content")
    with patch.object(si, "SKILL_DIR", target_dir):
        si.install_skill(force=False)
    assert (target_dir / "SKILL.md").read_text() == "custom content"


def test_install_skill_force_overwrites(tmp_path: Path):
    target_dir = tmp_path / ".claude" / "skills" / "tiny-screenshot"
    target_dir.mkdir(parents=True)
    (target_dir / "SKILL.md").write_text("stale content")
    with patch.object(si, "SKILL_DIR", target_dir):
        si.install_skill(force=True)
    assert (target_dir / "SKILL.md").read_text() != "stale content"
    assert "tinyscreenshot" in (target_dir / "SKILL.md").read_text()


def test_uninstall_removes_dir(tmp_path: Path):
    target_dir = tmp_path / ".claude" / "skills" / "tiny-screenshot"
    target_dir.mkdir(parents=True)
    (target_dir / "SKILL.md").write_text("x")
    with patch.object(si, "SKILL_DIR", target_dir):
        si.uninstall_skill()
    assert not target_dir.exists()
