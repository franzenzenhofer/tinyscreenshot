"""Claude vision-token estimator.

Anthropic's vision models price images at roughly (W*H)/750 tokens, with a
server-side cap at 1.6 megapixels (~2184 tokens). Format and color depth do
not affect token cost — only pixel count does.
"""

from __future__ import annotations

TOKEN_DIVISOR = 750
TOKEN_CAP = 2184  # 1.6 MP / 750, rounded


def estimate_tokens(width: int, height: int) -> int:
    """Return Anthropic vision-token estimate for an image of the given size."""
    if width <= 0 or height <= 0:
        raise ValueError(f"dimensions must be positive, got {width}x{height}")
    raw = (width * height) // TOKEN_DIVISOR
    return min(raw, TOKEN_CAP)


def format_token_report(
    src_w: int, src_h: int, out_w: int, out_h: int
) -> tuple[int, int]:
    """Return (out_tokens, src_tokens_uncapped_if_smaller)."""
    return estimate_tokens(out_w, out_h), estimate_tokens(src_w, src_h)
