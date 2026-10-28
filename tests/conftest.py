import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def rng():
    return np.random.default_rng(12345)


@pytest.fixture
def gray(rng):
    return rng.integers(0, 256, (24, 31), dtype=np.uint8)


@pytest.fixture
def color(rng):
    return rng.integers(0, 256, (24, 31, 3), dtype=np.uint8)
