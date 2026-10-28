"""Low-level neighbourhood helpers (private).

``correlate2d`` slides a kernel over an image using shifted array slices, which
keeps memory small and the arithmetic explicit:

    out[i, j] = sum_{a, b} kernel[a, b] * padded[i + a, j + b]
"""
from __future__ import annotations

from typing import Callable

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def per_channel(img: np.ndarray, fn: Callable[[np.ndarray], np.ndarray]) -> np.ndarray:
    """Apply a 2-D function to a gray image, or to each channel of a colour image."""
    if img.ndim == 2:
        return fn(img)
    return np.stack([fn(img[:, :, c]) for c in range(img.shape[2])], axis=2)


def pad2d(a: np.ndarray, before: tuple[int, int], after: tuple[int, int], mode: str = "reflect",
          constant: float = 0) -> np.ndarray:
    """Pad rows/columns. 'reflect' mirrors without repeating the edge pixel; an axis
    of length 1 cannot be mirrored, so it falls back to edge replication."""
    kw = {}
    if mode == "reflect" and (a.shape[0] < 2 or a.shape[1] < 2):
        mode = "edge"
    if mode == "constant":
        kw["constant_values"] = constant
    pads = ((before[0], after[0]), (before[1], after[1]))
    return np.pad(a, pads, mode=mode, **kw)


def correlate2d(a: np.ndarray, kernel, mode: str = "reflect") -> np.ndarray:
    """2-D correlation in float64.

    Kernel anchor is index (k-1)//2: the centre for odd k, and the top-left
    element for k=2 (which the 2x2 Roberts kernels need)."""
    kernel = np.asarray(kernel, dtype=np.float64)
    kh, kw = kernel.shape
    bh, bw = (kh - 1) // 2, (kw - 1) // 2
    padded = pad2d(a.astype(np.float64), (bh, bw), (kh - 1 - bh, kw - 1 - bw), mode)
    h, w = a.shape
    out = np.zeros((h, w), dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            if kernel[i, j] != 0.0:
                out += kernel[i, j] * padded[i:i + h, j:j + w]
    return out


def separable_correlate(a: np.ndarray, k1d, mode: str = "reflect") -> np.ndarray:
    """Correlate with the outer product of ``k1d`` with itself (rows, then columns)."""
    k1d = np.asarray(k1d, dtype=np.float64)
    return correlate2d(correlate2d(a, k1d.reshape(1, -1), mode), k1d.reshape(-1, 1), mode)


def reduce_windows(a: np.ndarray, kh: int, kw: int, reducer: Callable[[np.ndarray], np.ndarray],
                   mode: str = "reflect", max_elems: int = 4_000_000) -> np.ndarray:
    """Apply ``reducer`` (array (rows, W, kh*kw) -> (rows, W)) to every kh x kw window.

    Rows are processed in chunks so memory stays bounded on large images."""
    h, w = a.shape
    padded = pad2d(a, (kh // 2, kw // 2), (kh // 2, kw // 2), mode)
    view = sliding_window_view(padded, (kh, kw))          # (H, W, kh, kw), no copy
    rows = max(1, max_elems // max(1, w * kh * kw))
    out = np.empty((h, w), dtype=a.dtype)
    for r0 in range(0, h, rows):
        chunk = view[r0:r0 + rows].reshape(-1, w, kh * kw)  # copies only this chunk
        out[r0:r0 + rows] = reducer(chunk)
    return out
