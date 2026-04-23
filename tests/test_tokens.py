from __future__ import annotations

import pytest

from tinyscreenshot.tokens import TOKEN_CAP, TOKEN_DIVISOR, estimate_tokens


def test_formula_matches_docstring():
    # Known reference points documented in README.
    assert estimate_tokens(1024, 640) == 873
    assert estimate_tokens(800, 500) == 533
    assert estimate_tokens(640, 400) == 341
    assert estimate_tokens(320, 200) == 85


def test_server_side_cap():
    # Anything over ~1.6 MP clamps to TOKEN_CAP.
    assert estimate_tokens(4000, 3000) == TOKEN_CAP
    assert estimate_tokens(1568, 1568) == TOKEN_CAP


def test_tiny_images_still_count():
    assert estimate_tokens(100, 100) == (100 * 100) // TOKEN_DIVISOR


@pytest.mark.parametrize("w,h", [(0, 100), (100, 0), (-10, 100), (100, -10)])
def test_rejects_non_positive_dims(w: int, h: int):
    with pytest.raises(ValueError):
        estimate_tokens(w, h)
