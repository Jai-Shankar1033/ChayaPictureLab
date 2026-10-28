"""Input validation shared by every processing module."""
from __future__ import annotations

import numpy as np


class ImageError(ValueError):
    """Raised when an image or a parameter is invalid (message is user-readable)."""


def ensure_image(img, name: str = "image", allow_color: bool = True) -> np.ndarray:
    """Check that ``img`` is a non-empty uint8 grayscale (H,W) or RGB (H,W,3) array."""
    if not isinstance(img, np.ndarray):
        raise ImageError(f"{name} must be a NumPy array, got {type(img).__name__}.")
    if img.size == 0:
        raise ImageError(f"{name} is empty.")
    if img.dtype != np.uint8:
        raise ImageError(f"{name} must have dtype uint8, got {img.dtype}. "
                         "Convert explicitly (e.g. with to_uint8) so no silent rescaling happens.")
    if img.ndim == 2:
        return img
    if img.ndim == 3 and img.shape[2] == 3:
        if not allow_color:
            raise ImageError(f"{name} must be grayscale (H, W); got a colour image. Convert it first.")
        return img
    raise ImageError(f"{name} must have shape (H, W) or (H, W, 3); got {img.shape}.")


def ensure_gray(img, name: str = "image") -> np.ndarray:
    return ensure_image(img, name, allow_color=False)


def ensure_odd(value, name: str = "kernel size", minimum: int = 1, maximum: int = 99) -> int:
    """Validate an odd integer window size."""
    try:
        ok = not isinstance(value, bool) and float(value).is_integer()
    except (TypeError, ValueError):
        ok = False
    if not ok:
        raise ImageError(f"{name} must be an integer, got {value!r}.")
    value = int(value)
    if value < minimum or value > maximum:
        raise ImageError(f"{name} must be between {minimum} and {maximum}, got {value}.")
    if value % 2 == 0:
        raise ImageError(f"{name} must be odd, got {value}.")
    return value


def ensure_number(value, name: str, lo: float | None = None, hi: float | None = None,
                  lo_open: bool = False) -> float:
    """Validate a finite number inside [lo, hi] (or (lo, hi] when ``lo_open``)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ImageError(f"{name} must be a number, got {value!r}.") from None
    if not np.isfinite(v):
        raise ImageError(f"{name} must be finite, got {value!r}.")
    if lo is not None and (v <= lo if lo_open else v < lo):
        raise ImageError(f"{name} must be {'>' if lo_open else '>='} {lo}, got {v}.")
    if hi is not None and v > hi:
        raise ImageError(f"{name} must be <= {hi}, got {v}.")
    return v


def to_uint8(x) -> np.ndarray:
    """Round to nearest (half up), clip to [0, 255] and convert to uint8.

    Always call this on a float array instead of ``astype(np.uint8)``, which
    *wraps around* out-of-range values (e.g. -3 becomes 253) and truncates.
    """
    return np.clip(np.floor(np.asarray(x, dtype=np.float64) + 0.5), 0, 255).astype(np.uint8)
