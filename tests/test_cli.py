from __future__ import annotations

from unittest.mock import patch

import pytest
from PIL import Image

from tinyscreenshot.capture import Capture
from tinyscreenshot.cli import main


def _fake_capture() -> Capture:
    return Capture(Image.new("RGB", (1600, 1000), "white"), "fake main")


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "tinyscreenshot" in out


def test_missing_mode_exits_error(capsys):
    with pytest.raises(SystemExit):
        main([])


def test_region_parses_and_runs(tmp_path, capsys):
    out_file = tmp_path / "region.png"
    with patch("tinyscreenshot.cli.capture_region", return_value=_fake_capture()):
        rc = main(["region", "0,0,800,500", "-w", "400", "-c", "grey",
                   "-o", str(out_file), "--quiet"])
    assert rc == 0
    assert out_file.exists()


def test_malformed_region_reports_error(capsys):
    rc = main(["region", "bad", "--quiet"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "region must be x,y,w,h" in err


def test_list_prints_monitors(capsys):
    fake_monitors = [
        {"left": 0, "top": 0, "width": 3024, "height": 1964},
        {"left": 0, "top": 0, "width": 3024, "height": 1964},
    ]
    with patch("tinyscreenshot.cli.list_displays", return_value=fake_monitors):
        rc = main(["list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "display 1" in out
    assert "3024x1964" in out


def test_main_mode_writes_file(tmp_path):
    out_file = tmp_path / "shot.png"
    with patch("tinyscreenshot.cli.capture_main", return_value=_fake_capture()):
        rc = main(["main", "-w", "800", "-o", str(out_file), "--quiet"])
    assert rc == 0
    assert out_file.exists()
    with Image.open(out_file) as im:
        assert im.size == (800, 500)


def test_unknown_format_rejected(tmp_path):
    # .xyz is not valid
    with patch("tinyscreenshot.cli.capture_main", return_value=_fake_capture()):
        rc = main(["main", "-o", str(tmp_path / "x.xyz"), "--quiet"])
    assert rc == 1
