"""Point (pixel-wise) operations: g(x, y) = T[ f(x, y) ].

Every calculation is done in float64 and converted back with ``to_uint8``
(round half up + clip), so nothing can wrap around like uint8 arithmetic does.
All functions accept gray (H, W) or RGB (H, W, 3) images.
"""
from __future__ import annotations

import numpy as np

from .validation import ImageError, ensure_image, ensure_number, to_uint8


def negative(img: np.ndarray) -> np.ndarray:
    """g = 255 - f"""
    return (255 - ensure_image(img).astype(np.int16)).astype(np.uint8)


def adjust_brightness(img: np.ndarray, offset: float) -> np.ndarray:
    """g = clip(f + offset); offset may be negative."""
    offset = ensure_number(offset, "offset", -255, 255)
    return to_uint8(ensure_image(img).astype(np.float64) + offset)


def scale_intensity(img: np.ndarray, factor: float) -> np.ndarray:
    """g = clip(factor * f). factor < 1 darkens (e.g. 0.5 = divide by 2), > 1 brightens."""
    factor = ensure_number(factor, "factor", 0, 20)
    return to_uint8(ensure_image(img).astype(np.float64) * factor)


def adjust_contrast(img: np.ndarray, factor: float, pivot: float = 127.5) -> np.ndarray:
    """g = clip(pivot + factor * (f - pivot)). factor > 1 increases contrast, < 1 reduces it."""
    factor = ensure_number(factor, "contrast factor", 0, 20)
    pivot = ensure_number(pivot, "pivot", 0, 255)
    return to_uint8(pivot + factor * (ensure_image(img).astype(np.float64) - pivot))


def threshold(img: np.ndarray, t: int = 127) -> np.ndarray:
    """g = 255 where f > t else 0 (applied per channel for colour input)."""
    t = ensure_number(t, "threshold", 0, 255)
    return np.where(ensure_image(img) > t, 255, 0).astype(np.uint8)


def gamma_correct(img: np.ndarray, gamma: float, c: float = 1.0) -> np.ndarray:
    """Power-law transform on *normalised* intensities.

        r = f / 255            (normalise to [0, 1])
        s = c * r ** gamma
        g = round(255 * s)     (clip to [0, 255])

    gamma < 1 brightens dark regions, gamma > 1 darkens the image, gamma = 1 is identity."""
    gamma = ensure_number(gamma, "gamma", 0, 10, lo_open=True)
    c = ensure_number(c, "c", 0, 10, lo_open=True)
    r = ensure_image(img).astype(np.float64) / 255.0
    return to_uint8(255.0 * c * np.power(r, gamma))


def log_transform(img: np.ndarray, c: float | None = None) -> np.ndarray:
    """s = c * log(1 + r). By default c = 255 / log(256), so 255 maps exactly to 255.

    Expands dark values and compresses bright ones (useful for high dynamic range)."""
    if c is None:
        c = 255.0 / np.log(256.0)
    c = ensure_number(c, "c", 0, 1000, lo_open=True)
    return to_uint8(c * np.log1p(ensure_image(img).astype(np.float64)))


def combine_images(a: np.ndarray, b: np.ndarray, mode: str = "add", alpha: float = 0.5) -> np.ndarray:
    """Arithmetic on two same-sized images (clipped, no wrap-around).

    modes: add (a+b), subtract (a-b), absdiff (|a-b|), blend (alpha*a + (1-alpha)*b)."""
    a = ensure_image(a, "first image")
    b = ensure_image(b, "second image")
    if a.shape != b.shape:
        raise ImageError(f"Images must have the same shape; got {a.shape} and {b.shape}.")
    fa, fb = a.astype(np.float64), b.astype(np.float64)
    if mode == "add":
        return to_uint8(fa + fb)
    if mode == "subtract":
        return to_uint8(fa - fb)
    if mode == "absdiff":
        return to_uint8(np.abs(fa - fb))
    if mode == "blend":
        alpha = ensure_number(alpha, "alpha", 0, 1)
        return to_uint8(alpha * fa + (1 - alpha) * fb)
    raise ImageError(f"Unknown mode {mode!r}; use add, subtract, absdiff or blend.")
