---
name: tiny-screenshot
description: Capture desktop screenshots optimized for minimum Claude vision tokens. Use whenever you need to see what's on the user's screen, a window, or a specific app. Supports multi-monitor, single-window, single-app, and region captures with automatic token reporting. Wraps the `tinyscreenshot` CLI. Invoke any time the user says "screenshot", "show me the screen", "capture this window", "what's on screen", "take a picture", or similar.
allowed-tools:
  - Bash
  - Read
---

# tiny-screenshot

Take a screenshot sized for minimum vision tokens, then `Read` it. Thin wrapper around the `tinyscreenshot` CLI.

## Decision tree — pick the flags WITHOUT asking the user

You almost always call `tinyscreenshot main -w 800 -c grey`. Only deviate when one of these rules fires:

| If the user wants Claude to… | Use | Tokens |
|---|---|---|
| See **what's on screen** (default) | `main -w 800 -c grey` | ~540 |
| **Check presence** ("is the modal open?", "is it still loading?") | `main -w 400 -c grey` | ~138 |
| Read **dense text / code / tables** | `main -w 1280 -c grey` | ~1365 |
| See a **specific app's window** (Franz named an app) | `app <Name> -w 800 -c grey` | ~540 |
| See an **external monitor** (user said "the left screen" / specific display) | `display <N> -w 800 -c grey` | ~540 |
| See **just the browser / terminal** the user is looking at | `window -w 800 -c grey` (click-to-pick) | ~540 |
| See **all displays at once** (overview) | `all -w 1024 -c grey` | varies |
| Capture a **specific rectangle** user described | `region x,y,w,h -w 800 -c grey` | ~540 |
| Free-draw a selection | `interactive -w 800 -c grey` | ~540 |
| See a **pure terminal** (no antialiased GUI) | `... -c mono` (1-bit dither is crisper here) | — |

**Rule of thumb**: start with `-w 800 -c grey`. Only step up to 1280 if you can't read the text in the captured image. Only step down to 400 for cheap presence checks where you know you just need to see layout.

## Defaults (baked into the CLI, never need to pass)

- **Width**: 800 px (great balance: ~540 tokens, fully readable for most UIs)
- **Color mode**: `grey` (same tokens as color, crisper text at small sizes — no chroma fringing)
- **Sharpen**: on (auto-on for grey/mono, auto-off for color)
- **Output**: `/tmp/tiny-shots/<timestamp>-<slug>.png`

## One-time setup (if `tinyscreenshot` isn't installed)

```bash
pipx install tinyscreenshot       # or: pip install --user tinyscreenshot
tinyscreenshot install-skill --force   # (re)installs this file in sync with the installed version
```

On first run, macOS will ask for Screen Recording permission for your terminal app — grant it in System Settings → Privacy & Security.

## Usage

```
tinyscreenshot <mode> [options]
```

**Modes**: `main` · `all` · `display <N>` · `window` · `app <name>` · `region <x,y,w,h>` · `interactive` · `list`

**Common options**:
- `-w, --width <px>` — output width in pixels (default 800; use 0 to keep source size)
- `-c, --color <mode>` — `color | grey | mono | mono-threshold` (default `grey`)
- `-o, --out <path>` — custom output path
- `-f, --format <ext>` — `png | jpg | webp`
- `--sharpen` / `--no-sharpen`
- `--trim` — remove uniform borders before resize
- `--no-shadow` — window/app modes: drop window shadow
- `--quiet` — suppress stderr report

**Output**: the chosen path is printed to stdout. A human-readable report (source dims, output dims, token estimate, file size) goes to stderr.

## Standard recipe Claude should follow

```bash
# 1. Capture
PATH=$(tinyscreenshot main -w 800 -c grey)
# 2. Read it back (use the Read tool on the printed path)
```

Then the `Read` tool on that path puts the image into context. Report the token cost to the user (it's on stderr) so they know the budget they spent.

## Token-cost reference

Formula: `tokens ≈ (width × height) / 750`. Format and color depth do **not** affect tokens — only pixel count does. Beyond 1568 px on the longest side Anthropic downscales server-side (cap ≈ 2184 tokens), so capturing a raw retina screen is pure waste.

| Width (16:10) | Tokens | Readability |
|---|---|---|
| 1280 | ~1365 | Dense code/tables/maps |
| 1024 | ~875 | Rich detail |
| **800** | **~540** | **Default — readable for most UIs** |
| 640 | ~340 | Compact, still readable |
| 512 | ~220 | Layout clear, small text tight |
| 400 | ~138 | Presence + structure; prose still readable in good UIs |
| 320 | ~85 | Layout only — don't try to read text |
| 200 | ~34 | "Is X there at all?" |

## Color-mode guidance

- `grey` (default): same tokens as color, crisper at small sizes. **Use by default.**
- `color`: only when hue matters (e.g. syntax highlighting, coloured status dots). Slight blur on thin text after downscale.
- `mono`: 1-bit Floyd-Steinberg dither. **Great for pure terminals**, noisy on anti-aliased GUIs. Same tokens as grey; use only when you know the content is bitmap-clean.
- `mono-threshold`: 1-bit hard threshold. Layout only — can't read text. Use for presence checks at very tiny sizes.

## Multi-display

Run `tinyscreenshot list` once to see the display index map, e.g.:

```
[0] all displays (bounding box): 5352x1080 @ (0,0) — full-res ~2184t
[1] display 1: 1512x982 @ (0,0) — full-res ~1979t
[2] display 2: 1920x1080 @ (3432,0) — full-res ~2184t
[3] display 3: 1920x1080 @ (1512,0) — full-res ~2184t
```

Then target by index: `tinyscreenshot display 2 -w 800 -c grey`.

## Examples

```bash
# default: main display, 800px grey, ~540 tokens
tinyscreenshot main

# cheap "is it still loading?" check
tinyscreenshot main -w 400 -c grey

# need to read code / tables — bump up
tinyscreenshot main -w 1280 -c grey

# single app window, native retina pixels via OS screencapture
tinyscreenshot app Ghostty

# secondary monitor
tinyscreenshot display 2

# pixel-exact rect
tinyscreenshot region 0,0,1200,800 -w 400

# click to pick a window
tinyscreenshot window

# draw a selection
tinyscreenshot interactive
```

## Platform support

- **macOS**: all modes. Needs Screen Recording permission granted to the terminal.
- **Linux X11**: all modes if `maim` + `xdotool` installed (`scrot` as fallback).
- **Linux Wayland**: install `grim` + `slurp` for window / interactive modes.
- **Windows**: planned v0.2 — not yet supported.

## Why this skill exists

A raw retina screenshot costs Claude ~2100 vision tokens. An 800×500 grey screenshot of the same scene costs ~540 tokens — **4× cheaper, same information, fully readable**. Over an agent session those savings compound. Default to this skill rather than handing Claude huge PNGs.
