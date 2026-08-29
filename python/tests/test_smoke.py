"""Smoke tests: detect + reconstruct on a real example image.

These run the full pipeline once per mode (full + fast) so they double as
release checks in CI before publishing to PyPI.
"""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pixelfixer import detect
from pixelfixer.api import process
from pixelfixer.reconstruct import reconstruct

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"

# Expected native sizes of the example images, from the reference detector.
# Tight margins (±2): a drift here means a detection regression.
EXPECTED = {
    "dragon.png": (359, 268),
    "frog.png": (121, 120),
    "koi-pond.png": (115, 116),
    "lighthouse.png": (104, 138),
}


def _load(name):
    path = EXAMPLES / name
    if not path.exists():
        pytest.skip(f"example image not found: {path}")
    return np.array(Image.open(path).convert("RGBA"))


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_detect_finds_the_grid(name):
    rgba = _load(name)
    r = detect(rgba)
    cols, rows = EXPECTED[name]
    assert abs(r["cols"] - cols) <= 2
    assert abs(r["rows"] - rows) <= 2
    assert r["step_x"] > 1 and r["step_y"] > 1


def test_reconstruct_outputs_native_size():
    rgba = _load("frog.png")
    r = detect(rgba)
    out = reconstruct(rgba, r["step_x"], r["step_y"], r["cols"], r["rows"])
    assert out.shape[0] == r["rows"]
    assert out.shape[1] == r["cols"]


def test_api_process_fast():
    result = process(_load("frog.png"), mode="fast")
    assert result["cols"] >= 8 and result["rows"] >= 8
    assert result["png"][:8] == b"\x89PNG\r\n\x1a\n"
