"""Noise generators. Pass ``seed`` to make an experiment reproducible."""
from __future__ import annotations

import numpy as np

from .validation import ensure_image, ensure_number, to_uint8


def gaussian_noise(img: np.ndarray, sigma: float = 20.0, mean: float = 0.0, seed: int | None = None) -> np.ndarray:
    """g = clip(f + n), n ~ N(mean, sigma^2), drawn independently for every sample.

    The addition happens in float64 BEFORE clipping. (Converting negative noise to
    uint8 first would wrap -5 to 251 and bias the image brighter - a bug in the
    earlier version of this project.)"""
    img = ensure_image(img)
    sigma = ensure_number(sigma, "sigma", 0, 255)
    mean = ensure_number(mean, "mean", -255, 255)
    rng = np.random.default_rng(seed)
    return to_uint8(img.astype(np.float64) + rng.normal(mean, sigma, img.shape))


def salt_pepper_noise(img: np.ndarray, density: float = 0.05, salt_fraction: float = 0.5,
                      seed: int | None = None) -> np.ndarray:
    """A fraction ``density`` of PIXELS is corrupted; of those, ``salt_fraction`` become
    white (255) and the rest black (0). In colour images the same pixel positions are
    corrupted in all three channels."""
    img = ensure_image(img)
    density = ensure_number(density, "density", 0, 1)
    salt_fraction = ensure_number(salt_fraction, "salt fraction", 0, 1)
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    hit = rng.random((h, w)) < density
    salt = rng.random((h, w)) < salt_fraction
    out = img.copy()
    out[hit & salt] = 255
    out[hit & ~salt] = 0
    return out


def average_noisy_copies(img: np.ndarray, n: int = 10, sigma: float = 20.0, seed: int | None = None) -> np.ndarray:
    """Image averaging: add independent Gaussian noise n times, average the copies.
    The noise standard deviation drops roughly by 1/sqrt(n)."""
    img = ensure_image(img)
    n = int(ensure_number(n, "number of images", 1, 500))
    rng = np.random.default_rng(seed)
    acc = np.zeros(img.shape, dtype=np.float64)
    for _ in range(n):
        acc += to_uint8(img.astype(np.float64) + rng.normal(0.0, sigma, img.shape))
    return to_uint8(acc / n)
