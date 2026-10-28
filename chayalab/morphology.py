"""Morphological processing with flat structuring elements (SE).

Erosion  : g(x,y) = min of f over the SE placed at (x,y)    - shrinks bright objects
Dilation : g(x,y) = max of f over the (reflected) SE        - grows bright objects
Opening  : erosion then dilation   - removes small bright specks, keeps big shapes
Closing  : dilation then erosion   - fills small dark holes and gaps
Boundary : internal = f - erode(f);  external = dilate(f) - f;  gradient = dilate - erode

Works on binary images (values 0/255) and on grayscale images. Border rule: pixels
outside the image are ignored (erosion pads with 255, dilation with 0), so objects
touching the border are not artificially eaten away.
"""
from __future__ import annotations

import numpy as np

from ._windows import pad2d, per_channel
from .validation import ImageError, ensure_image, ensure_number, ensure_odd, to_uint8

SHAPES = ("rect", "cross", "ellipse")


def structuring_element(shape: str = "rect", size: int = 3) -> np.ndarray:
    """Boolean (size x size) SE. rect = all True, cross = centre row+column,
    ellipse = {(x, y): (x/r)^2 + (y/r)^2 <= 1}, r = size/2 (a disc for odd sizes)."""
    size = ensure_odd(size, "structuring element size", maximum=61)
    if shape == "rect":
        return np.ones((size, size), dtype=bool)
    c = size // 2
    if shape == "cross":
        se = np.zeros((size, size), dtype=bool)
        se[c, :] = True
        se[:, c] = True
        return se
    if shape == "ellipse":
        y, x = np.ogrid[-c:c + 1, -c:c + 1]
        r = size / 2.0
        return (x / r) ** 2 + (y / r) ** 2 <= 1.0
    raise ImageError(f"shape must be one of {SHAPES}; got {shape!r}.")


def _check_se(se) -> np.ndarray:
    se = np.asarray(se)
    if se.ndim != 2 or se.size == 0 or se.shape[0] % 2 == 0 or se.shape[1] % 2 == 0:
        raise ImageError("Structuring element must be a 2-D array with odd height and width.")
    se = se.astype(bool)
    if not se.any():
        raise ImageError("Structuring element must contain at least one True element.")
    return se


def _slide(ch: np.ndarray, se: np.ndarray, reducer, pad_value: int) -> np.ndarray:
    h, w = ch.shape
    ph, pw = se.shape[0] // 2, se.shape[1] // 2
    padded = pad2d(ch, (ph, pw), (ph, pw), "constant", pad_value)
    out = None
    for i, j in zip(*np.nonzero(se)):
        part = padded[i:i + h, j:j + w]
        out = part.copy() if out is None else reducer(out, part)
    return out


def erode(img: np.ndarray, se: np.ndarray) -> np.ndarray:
    img, se = ensure_image(img), _check_se(se)
    return per_channel(img, lambda ch: _slide(ch, se, np.minimum, 255))


def dilate(img: np.ndarray, se: np.ndarray) -> np.ndarray:
    img, se = ensure_image(img), _check_se(se)
    se_r = se[::-1, ::-1]        # dilation uses the reflected SE
    return per_channel(img, lambda ch: _slide(ch, se_r, np.maximum, 0))


def opening(img: np.ndarray, se: np.ndarray) -> np.ndarray:
    return dilate(erode(img, se), se)


def closing(img: np.ndarray, se: np.ndarray) -> np.ndarray:
    return erode(dilate(img, se), se)


def _sub(a, b):
    """a - b in int16, clipped to [0, 255] (a custom SE without its centre could give negatives)."""
    return to_uint8(a.astype(np.int16) - b.astype(np.int16))


def boundary(img: np.ndarray, se: np.ndarray, kind: str = "internal") -> np.ndarray:
    """Boundary extraction: 'internal', 'external' or 'gradient'."""
    img = ensure_image(img)
    if kind == "internal":
        return _sub(img, erode(img, se))
    if kind == "external":
        return _sub(dilate(img, se), img)
    if kind == "gradient":
        return _sub(dilate(img, se), erode(img, se))
    raise ImageError("kind must be 'internal', 'external' or 'gradient'.")


def binarize(img: np.ndarray, t: float = 127) -> np.ndarray:
    """0/255 image: 255 where f > t (convenience for morphology on binary images)."""
    t = ensure_number(t, "threshold", 0, 255)
    return np.where(ensure_image(img) > t, 255, 0).astype(np.uint8)
