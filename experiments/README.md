# Resolution × color-mode experiment

This experiment answers one question: **what's the smallest screenshot Claude can still read, and what color mode helps most?**

## How to run

```bash
# from the repo root, with the package installed (pip install -e .)
python experiments/run_matrix.py /path/to/source.png
#   or:
python experiments/run_matrix.py --capture         # captures main display first
```

Writes `experiments/out/W<width>-<color>.png` and `experiments/out/results.csv`.

## Method

- **Source**: one 800×520 captured Gmail/Chrome screen (dense anti-aliased UI with lots of prose and symbols — harder than pure terminal text).
- **Matrix**: 8 target widths × 4 color modes = 32 variants.
- **Scoring**: read each variant as Claude vision input and judge:
  - **Full text legibility** — can all body prose be read?
  - **Structural legibility** — can layout / UI elements still be identified?
  - **Presence checks** — can you tell if a specific thing is on screen?

Token cost is the Anthropic formula `(W × H) / 750` and is identical across color modes at a given resolution. So **picking a width is the only decision that affects token cost**; color mode only affects *readability* at a given cost.

## Findings

| Width | Tokens | color | grey | mono | mono-threshold |
|---|---|---|---|---|---|
| 800 | ~554 | full | **full** | structural | presence-only |
| 640 | ~354 | full | **full** | structural | presence-only |
| 512 | ~227 | full | **full (tight)** | structural | presence-only |
| 400 | ~138 | structural+ | **structural+** | structural | presence-only |
| 320 | ~88  | structural | structural | patchy | presence-only |
| 200 | ~34  | layout | layout | layout | layout-only |

- **`grey` beats `color` at every size** for UI content: same tokens, no chroma fringing on thin text after downscale.
- **`mono` (Floyd-Steinberg dither)** is noisy on anti-aliased GUIs like Gmail — dots obscure glyphs below ~800 px. It shines on **pure terminal / monospace content** where glyphs are bitmap-sharp; avoid it for screenshots of modern apps.
- **`mono-threshold`** is only useful for presence/layout checks ("is the modal open?"). Don't use it to read text.
- **Diminishing returns below 400 px** for general UI: the 200 px variant at ~34 tokens is 16× cheaper than full but only useful for answering "is X on the screen at all?".

## Recommended defaults

| Use case | Recommended flags | Tokens |
|---|---|---|
| Default screenshot for Claude | `-w 800 -c grey` | ~540 |
| Compact (still fully readable) | `-w 640 -c grey` | ~340 |
| Dense text / detail inspection | `-w 1024 -c grey` (or `color`) | ~870 |
| Terminal-only capture | `-w 640 -c mono` | ~340 |
| Layout presence check | `-w 320 -c grey` | ~85 |
| Minimum "is it there" | `-w 200 -c mono-threshold` | ~33 |

The CLI's default (`-w 800 -c grey`) deliberately lands in the top row — safe, readable, cheap.

## Why file size varies so much across modes (but tokens don't)

PNG compresses `mono-threshold` images into tiny files (~1-10 KB) because they're 1-bit and highly compressible. `color` PNGs of the same scene are 10-30× larger. **This does not affect Claude's token cost** — Anthropic rasterizes to pixels before metering. File size only matters for upload bandwidth and disk. Token cost is a function of `width × height` alone.

## Caveats

- Measurements are eyeball-based on one scene. A rigorous version would run OCR against each variant and compute word-recall vs the full-resolution baseline, then repeat over 10+ scenes (terminal, IDE, map, photo). That's a natural v0.2 upgrade.
- The source was already downscaled by mss on a Retina display, so the "1280" and "1024" rows in the CSV output the same 800×520 variant (no upscale). Capture a true-high-res source to exercise those cells.
