"""tinyscreenshot command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tinyscreenshot import __version__
from tinyscreenshot.capture import (
    Capture,
    capture_all,
    capture_app_by_name,
    capture_display,
    capture_interactive_selection,
    capture_main,
    capture_region,
    capture_window_interactive,
    list_displays,
)
from tinyscreenshot.process import ProcessOptions
from tinyscreenshot.runner import RunSpec, run
from tinyscreenshot.skill_install import install_skill, uninstall_skill
from tinyscreenshot.tokens import estimate_tokens

CAPTURE_MODES = ("all", "main", "display", "region", "window", "app", "interactive")


def _add_common_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("-w", "--width", type=int, default=800,
                   help="target output width in px (0 = no resize, default 800)")
    p.add_argument("-c", "--color", choices=("color", "grey", "mono", "mono-threshold"),
                   default="grey", help="color mode (default grey — same tokens, crisper text)")
    p.add_argument("-o", "--out", type=Path, default=None,
                   help="output file (default /tmp/tiny-shots/<ts>-<mode>.<ext>)")
    p.add_argument("-f", "--format", choices=("png", "jpg", "jpeg", "webp"), default=None,
                   help="output format when --out is not given (default png)")
    p.add_argument("--sharpen", dest="sharpen", action="store_true", default=None,
                   help="force unsharp mask on (default: auto-on for grey/mono)")
    p.add_argument("--no-sharpen", dest="sharpen", action="store_false",
                   help="disable unsharp mask")
    p.add_argument("--trim", action="store_true",
                   help="trim uniform borders before resize")
    p.add_argument("--no-shadow", action="store_true",
                   help="window/app modes only: drop window shadow")
    p.add_argument("--quiet", action="store_true", help="suppress stderr report")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tinyscreenshot",
        description="Token-saving screenshots for Claude Code. "
                    "Outputs a small, readable image and prints ~N tokens it costs.",
    )
    p.add_argument("--version", action="version", version=f"tinyscreenshot {__version__}")
    sub = p.add_subparsers(dest="mode", required=True, metavar="MODE")

    for mode in ("all", "main", "window", "interactive"):
        sp = sub.add_parser(mode, help=f"capture {mode}")
        _add_common_options(sp)

    sp = sub.add_parser("display", help="capture a specific display")
    sp.add_argument("index", type=int, help="display index (1 = primary)")
    _add_common_options(sp)

    sp = sub.add_parser("region", help="capture a pixel rectangle")
    sp.add_argument("rect", help="x,y,w,h in screen pixels")
    _add_common_options(sp)

    sp = sub.add_parser("app", help="capture the frontmost window of a named app")
    sp.add_argument("name", help="app name (e.g. Ghostty, 'Google Chrome')")
    _add_common_options(sp)

    sp = sub.add_parser("list", help="list available displays")

    sp = sub.add_parser("install-skill",
                        help="install the bundled Claude Code skill into ~/.claude/skills/")
    sp.add_argument("--force", action="store_true", help="overwrite existing skill")

    sub.add_parser("uninstall-skill", help="remove ~/.claude/skills/tiny-screenshot/")
    return p


def _parse_rect(spec: str) -> tuple[int, int, int, int]:
    parts = spec.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(f"region must be x,y,w,h (got {spec!r})")
    try:
        x, y, w, h = (int(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"region values must be integers: {spec!r}") from exc
    return x, y, w, h


def _dispatch_list() -> int:
    monitors = list_displays()
    for i, m in enumerate(monitors):
        label = "all displays (bounding box)" if i == 0 else f"display {i}"
        w, h = m.get("width"), m.get("height")
        tokens = estimate_tokens(w, h) if w and h else 0
        sys.stdout.write(
            f"  [{i}] {label}: {w}x{h} @ ({m.get('left')},{m.get('top')}) "
            f"— full-res ~{tokens}t\n"
        )
    return 0


def _run_capture(args: argparse.Namespace) -> int:
    opts = ProcessOptions(
        width=args.width, color=args.color,
        sharpen=args.sharpen, trim=args.trim,
    )
    slug = args.mode
    if args.mode == "all":
        capture_fn = capture_all
    elif args.mode == "main":
        capture_fn = capture_main
    elif args.mode == "display":
        idx = args.index
        def capture_fn() -> Capture:
            return capture_display(idx)
        slug = f"display-{idx}"
    elif args.mode == "region":
        x, y, w, h = _parse_rect(args.rect)
        def capture_fn() -> Capture:
            return capture_region(x, y, w, h)
        slug = f"region-{x}-{y}-{w}-{h}"
    elif args.mode == "window":
        ns = args.no_shadow
        def capture_fn() -> Capture:
            return capture_window_interactive(no_shadow=ns)
    elif args.mode == "app":
        name, ns = args.name, args.no_shadow
        def capture_fn() -> Capture:
            return capture_app_by_name(name, no_shadow=ns)
        safe = "".join(ch if ch.isalnum() else "-" for ch in name).strip("-")
        slug = f"app-{safe or 'unknown'}"
    elif args.mode == "interactive":
        capture_fn = capture_interactive_selection
    else:
        raise AssertionError(f"unreachable mode: {args.mode}")

    spec = RunSpec(
        capture_fn=capture_fn, slug=slug, process_opts=opts,
        out=args.out, fmt=args.format, quiet=args.quiet,
    )
    path = run(spec)
    sys.stdout.write(f"{path}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.mode == "list":
            return _dispatch_list()
        if args.mode == "install-skill":
            install_skill(force=getattr(args, "force", False))
            return 0
        if args.mode == "uninstall-skill":
            uninstall_skill()
            return 0
        return _run_capture(args)
    except Exception as exc:
        sys.stderr.write(f"tinyscreenshot: {exc}\n")
        return 1
