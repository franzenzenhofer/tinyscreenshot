"""Tests for the platform.mac_ver() empty-string workaround."""

from __future__ import annotations

import platform

import tinyscreenshot._macos_compat as compat


def _reset() -> None:
    compat._PATCHED = False


def test_patches_empty_mac_ver(monkeypatch):
    _reset()
    monkeypatch.setattr(compat.sys, "platform", "darwin")
    monkeypatch.setattr(platform, "mac_ver", lambda: ("", ("", "", ""), "arm64"))
    monkeypatch.setattr(compat, "_product_version", lambda: "26.1")

    compat.ensure_mac_ver()

    assert platform.mac_ver()[0] == "26.1"
    # float() no longer raises, which is the actual crash mss hit
    assert float(".".join(platform.mac_ver()[0].split(".")[:2])) == 26.1


def test_noop_when_mac_ver_works(monkeypatch):
    _reset()
    monkeypatch.setattr(compat.sys, "platform", "darwin")
    sentinel = ("15.0", ("", "", ""), "arm64")
    monkeypatch.setattr(platform, "mac_ver", lambda: sentinel)

    compat.ensure_mac_ver()

    assert platform.mac_ver() is sentinel


def test_noop_off_darwin(monkeypatch):
    _reset()
    monkeypatch.setattr(compat.sys, "platform", "linux")
    called = {"n": 0}

    def broken():
        called["n"] += 1
        return ("", ("", "", ""), "")

    monkeypatch.setattr(platform, "mac_ver", broken)

    compat.ensure_mac_ver()

    assert called["n"] == 0
