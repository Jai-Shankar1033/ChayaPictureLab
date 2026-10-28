"""Image quality metrics and analysis measurements."""
from __future__ import annotations

import numpy as np

from .histogram import compute_histogram
from .validation import ImageError, ensure_image


def _check_pair(reference, test):
    reference = ensure_image(reference, "reference image")
    test = ensure_image(test, "test image")
    if reference.shape != test.shape:
        raise ImageError(f"Images must have the same shape to be compared; got {reference.shape} "
                         f"and {test.shape}. A score against an image of a different size or "
                         "content would be meaningless.")
    return reference, test


def mse(reference: np.ndarray, test: np.ndarray) -> float:
    """Mean Squared Error = (1/N) * sum (ref - test)^2 .  0 means identical images.
    Computed in float64 so uint8 subtraction cannot wrap around."""
    reference, test = _check_pair(reference, test)
    d = reference.astype(np.float64) - test.astype(np.float64)
    return float(np.mean(d * d))


def psnr(reference: np.ndarray, test: np.ndarray, peak: float = 255.0) -> float:
    """Peak Signal-to-Noise Ratio = 10 * log10(peak^2 / MSE)  in dB (higher = closer).

    Edge case: identical images give MSE = 0, so PSNR is mathematically infinite and
    ``float('inf')`` is returned (never a huge made-up number)."""
    m = mse(reference, test)
    if m == 0.0:
        return float("inf")
    return float(10.0 * np.log10(peak * peak / m))


def entropy(gray: np.ndarray) -> float:
    """Shannon entropy in bits: -sum p log2 p  (0 for a constant image, max 8)."""
    h = compute_histogram(gray if gray.ndim == 2 else gray.mean(axis=2).round().astype(np.uint8))
    p = h[h > 0] / h.sum()
    return float(-(p * np.log2(p)).sum())


def image_stats(img: np.ndarray) -> dict:
    """Descriptive measurements shown on the analysis dashboard.

    * mean intensity       = (1/N) sum f
    * standard deviation   = sqrt( (1/N) sum (f - mean)^2 )   (population std)
    * RMS contrast         = std / 255   (std of normalised intensities)
    * Michelson contrast   = (max - min) / (max + min)   (0 if max + min = 0)
    * dynamic range        = max - min
    Statistics are over all samples (all channels together for colour images)."""
    img = ensure_image(img)
    f = img.astype(np.float64)
    mx, mn = float(f.max()), float(f.min())
    out = {
        "height": int(img.shape[0]), "width": int(img.shape[1]),
        "channels": 1 if img.ndim == 2 else int(img.shape[2]),
        "dtype": str(img.dtype),
        "mean": float(f.mean()), "std": float(f.std()),
        "min": mn, "max": mx, "dynamic_range": mx - mn,
        "rms_contrast": float(f.std() / 255.0),
        "michelson_contrast": 0.0 if mx + mn == 0 else (mx - mn) / (mx + mn),
        "entropy_bits": entropy(img),
    }
    if img.ndim == 3:
        out["channel_means"] = {c: float(f[:, :, i].mean()) for i, c in enumerate("RGB")}
    return out
