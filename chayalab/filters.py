"""Spatial filters (gray or per-channel colour).

Border rule (all filters): the image is *mirrored* across its edges ("reflect"
padding, edge pixel not repeated) so every output pixel sees a full window.
Window sizes must be odd so the window has a centre pixel.
"""
from __future__ import annotations

import numpy as np

from ._windows import correlate2d, per_channel, reduce_windows, pad2d, separable_correlate
from .validation import ImageError, ensure_image, ensure_number, ensure_odd, to_uint8

LAPLACIAN_KERNEL = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float64)


def mean_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """g = (1/k^2) * sum of the k x k window. Linear; blurs noise and edges alike."""
    img = ensure_image(img)
    k = ensure_odd(ksize)
    k1 = np.full(k, 1.0 / k)
    return per_channel(img, lambda ch: to_uint8(separable_correlate(ch, k1)))


def gaussian_kernel_1d(sigma: float, ksize: int | None = None) -> np.ndarray:
    """Normalised 1-D Gaussian  w(x) = exp(-x^2 / (2 sigma^2)) / sum.
    Default size is 2*ceil(3 sigma)+1, which covers 99.7 % of the curve."""
    sigma = ensure_number(sigma, "sigma", 0, 50, lo_open=True)
    if ksize is None:
        ksize = 2 * int(np.ceil(3 * sigma)) + 1
    ksize = ensure_odd(ksize, maximum=301)
    x = np.arange(ksize) - ksize // 2
    w = np.exp(-(x.astype(np.float64) ** 2) / (2.0 * sigma ** 2))
    return w / w.sum()


def gaussian_filter(img: np.ndarray, sigma: float = 1.0, ksize: int | None = None) -> np.ndarray:
    """Gaussian smoothing (separable: one 1-D pass along rows, one along columns)."""
    img = ensure_image(img)
    k1 = gaussian_kernel_1d(sigma, ksize)
    return per_channel(img, lambda ch: to_uint8(separable_correlate(ch, k1)))


def median_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """g = the MIDDLE value of the sorted window (window has k*k, an odd count).
    Removes impulse (salt-and-pepper) noise while keeping edges fairly sharp."""
    img = ensure_image(img)
    k = ensure_odd(ksize)
    mid = (k * k) // 2

    def reducer(win):
        return np.partition(win, mid, axis=-1)[..., mid]

    return per_channel(img, lambda ch: reduce_windows(ch, k, k, reducer))


def min_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """g = minimum of the window (grows dark regions)."""
    img = ensure_image(img)
    k = ensure_odd(ksize)
    return per_channel(img, lambda ch: reduce_windows(ch, k, k, lambda w: w.min(axis=-1)))


def max_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """g = maximum of the window (grows bright regions)."""
    img = ensure_image(img)
    k = ensure_odd(ksize)
    return per_channel(img, lambda ch: reduce_windows(ch, k, k, lambda w: w.max(axis=-1)))


def _mode_2d(ch: np.ndarray, k: int) -> np.ndarray:
    """Most frequent value in each k x k window, counted with integral images.

    For every intensity v that occurs in the image we build the indicator image
    (f == v), take its running window sum (summed-area table) and keep the value
    with the highest count. Values are visited in ascending order and an update
    needs a STRICTLY larger count, so **ties go to the smallest intensity**."""
    r = k // 2
    padded = pad2d(ch, (r, r), (r, r), "reflect")
    h, w = ch.shape
    best_count = np.zeros((h, w), dtype=np.int32)
    best_val = np.zeros((h, w), dtype=np.uint8)
    for v in np.unique(padded):
        ind = (padded == v).astype(np.int32)
        sat = np.zeros((ind.shape[0] + 1, ind.shape[1] + 1), dtype=np.int32)
        sat[1:, 1:] = ind.cumsum(axis=0).cumsum(axis=1)
        count = sat[k:k + h, k:k + w] - sat[:h, k:k + w] - sat[k:k + h, :w] + sat[:h, :w]
        better = count > best_count
        best_count[better] = count[better]
        best_val[better] = v
    return best_val


def mode_filter(img: np.ndarray, ksize: int = 3) -> np.ndarray:
    """A genuine MODE filter: each pixel becomes the most frequent value in its window.

    Rules: borders mirrored; ties -> smallest intensity; colour images are processed
    channel by channel. NOT the same as the median filter (see tests)."""
    img = ensure_image(img)
    k = ensure_odd(ksize)
    return per_channel(img, lambda ch: _mode_2d(ch, k))


def laplacian_response(img: np.ndarray) -> np.ndarray:
    """Absolute Laplacian  |4 f(x,y) - f(x-1,y) - f(x+1,y) - f(x,y-1) - f(x,y+1)|, clipped."""
    img = ensure_image(img)
    return per_channel(img, lambda ch: to_uint8(np.abs(correlate2d(ch, LAPLACIAN_KERNEL))))


def laplacian_sharpen(img: np.ndarray, amount: float = 1.0) -> np.ndarray:
    """g = f + amount * Laplacian(f)  (adds back the detail the Laplacian finds)."""
    img = ensure_image(img)
    amount = ensure_number(amount, "amount", 0, 10)
    return per_channel(img, lambda ch: to_uint8(ch + amount * correlate2d(ch, LAPLACIAN_KERNEL)))


def unsharp_mask(img: np.ndarray, sigma: float = 1.5, amount: float = 1.0) -> np.ndarray:
    """g = f + amount * (f - GaussianBlur(f)). The blurred copy holds the low
    frequencies, so (f - blur) is the detail that gets amplified."""
    img = ensure_image(img)
    amount = ensure_number(amount, "amount", 0, 10)
    k1 = gaussian_kernel_1d(sigma)
    return per_channel(img, lambda ch: to_uint8(
        ch + amount * (ch.astype(np.float64) - separable_correlate(ch, k1))))


def outlier_filter(img: np.ndarray, threshold: float = 30.0, ksize: int = 3) -> np.ndarray:
    """Replace a pixel by its window mean only when |f - mean| > threshold.
    Keeps good pixels untouched; useful against isolated impulse noise."""
    img = ensure_image(img)
    threshold = ensure_number(threshold, "threshold", 0, 255)
    k = ensure_odd(ksize)
    k1 = np.full(k, 1.0 / k)

    def one(ch):
        m = separable_correlate(ch, k1)
        return np.where(np.abs(ch - m) > threshold, to_uint8(m), ch).astype(np.uint8)

    return per_channel(img, one)
