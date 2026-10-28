"""Histogram laboratory: histogram, PDF, CDF, stretching, equalization, thresholding."""
from __future__ import annotations

import numpy as np

from ._windows import separable_correlate
from .validation import ImageError, ensure_gray, ensure_number, ensure_odd, to_uint8

L = 256  # number of grey levels for 8-bit images


def compute_histogram(gray: np.ndarray) -> np.ndarray:
    """h[k] = number of pixels with intensity k (length-256 int64 array)."""
    return np.bincount(ensure_gray(gray).ravel(), minlength=L).astype(np.int64)


def probability_distribution(gray: np.ndarray) -> np.ndarray:
    """p[k] = h[k] / N  (sums to 1)."""
    h = compute_histogram(gray)
    return h / h.sum()


def cumulative_distribution(gray: np.ndarray) -> np.ndarray:
    """c[k] = sum_{j<=k} p[j]  (non-decreasing, ends at 1)."""
    return np.cumsum(probability_distribution(gray))


def equalization_mapping(gray: np.ndarray) -> np.ndarray:
    """Look-up table for histogram equalization.

        s_k = round( (L-1) * (c[k] - c_min) / (1 - c_min) )

    where c is the CDF and c_min its first non-zero value. Subtracting c_min makes the
    darkest *occurring* level map to 0 (the standard textbook refinement).
    For a constant image 1 - c_min = 0, the mapping is undefined and the identity is returned."""
    c = cumulative_distribution(gray)
    c_min = c[c > 0][0]
    if 1.0 - c_min <= 0.0:
        return np.arange(L, dtype=np.uint8)
    return to_uint8((L - 1) * (c - c_min) / (1.0 - c_min))


def equalize(gray: np.ndarray) -> np.ndarray:
    """Histogram equalization (grayscale). Constant images are returned unchanged."""
    gray = ensure_gray(gray)
    return equalization_mapping(gray)[gray]


def stretch(gray: np.ndarray, low_percent: float = 0.0, high_percent: float = 100.0) -> np.ndarray:
    """Linear contrast stretching:  g = (f - lo) / (hi - lo) * 255, clipped.

    lo/hi are the given percentiles of the pixel values (0 and 100 = plain min-max).
    A constant image (hi == lo) has no contrast to stretch and is returned unchanged."""
    gray = ensure_gray(gray)
    lp = ensure_number(low_percent, "low percentile", 0, 100)
    hp = ensure_number(high_percent, "high percentile", 0, 100)
    if lp >= hp:
        raise ImageError("low percentile must be smaller than high percentile.")
    lo, hi = np.percentile(gray, [lp, hp])
    if hi <= lo:
        return gray.copy()
    return to_uint8((gray.astype(np.float64) - lo) / (hi - lo) * 255.0)


def global_threshold(gray: np.ndarray, t: float = 127) -> np.ndarray:
    """g = 255 if f > t else 0."""
    t = ensure_number(t, "threshold", 0, 255)
    return np.where(ensure_gray(gray) > t, 255, 0).astype(np.uint8)


def otsu_threshold(gray: np.ndarray) -> int:
    """Otsu's method: choose t maximising the between-class variance

        sigma_B^2(t) = (mu_T * w0(t) - mu(t))^2 / ( w0(t) * (1 - w0(t)) )

    w0(t) = sum_{k<=t} p_k, mu(t) = sum_{k<=t} k p_k, mu_T = total mean.
    A constant image has a single class, so 0 is returned (first level)."""
    p = probability_distribution(gray)
    k = np.arange(L)
    w0 = np.cumsum(p)
    mu = np.cumsum(k * p)
    mu_t = mu[-1]
    denom = w0 * (1.0 - w0)
    valid = denom > 1e-12
    sigma_b = np.zeros(L)
    sigma_b[valid] = (mu_t * w0[valid] - mu[valid]) ** 2 / denom[valid]
    return int(np.argmax(sigma_b))


def otsu(gray: np.ndarray) -> tuple[np.ndarray, int]:
    """Return (binary image, threshold)."""
    t = otsu_threshold(gray)
    return global_threshold(gray, t), t


def adaptive_threshold(gray: np.ndarray, block_size: int = 11, c: float = 2.0,
                       method: str = "mean") -> np.ndarray:
    """Local threshold: g = 255 if f > local_mean(x, y) - c else 0.

    method 'mean' uses a box window; 'gaussian' weights the window with a Gaussian
    (sigma = 0.3*((k-1)*0.5-1)+0.8, the usual rule of thumb). Borders are mirrored."""
    gray = ensure_gray(gray)
    k = ensure_odd(block_size, "block size", minimum=3, maximum=201)
    c = ensure_number(c, "C", -255, 255)
    if method == "mean":
        k1 = np.full(k, 1.0 / k)
    elif method == "gaussian":
        sigma = 0.3 * ((k - 1) * 0.5 - 1) + 0.8
        x = np.arange(k) - k // 2
        k1 = np.exp(-(x ** 2) / (2 * sigma ** 2))
        k1 /= k1.sum()
    else:
        raise ImageError("method must be 'mean' or 'gaussian'.")
    local = separable_correlate(gray, k1)
    return np.where(gray.astype(np.float64) > local - c, 255, 0).astype(np.uint8)
