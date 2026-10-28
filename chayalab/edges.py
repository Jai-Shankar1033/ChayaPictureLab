"""Edge detection. Every stage below is implemented manually with NumPy
(OpenCV is NOT used here; tests compare Canny against cv2.Canny as a reference only).

Image coordinates: x increases to the right, y increases DOWNWARD.
gradient direction theta = atan2(Gy, Gx).
"""
from __future__ import annotations

import numpy as np

from ._windows import correlate2d, pad2d
from .filters import gaussian_filter
from .validation import ImageError, ensure_gray, ensure_number, to_uint8

KERNELS = {
    "sobel": (np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]), np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])),
    "prewitt": (np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]), np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])),
    "roberts": (np.array([[1, 0], [0, -1]]), np.array([[0, 1], [-1, 0]])),
}


def gradients(gray: np.ndarray, operator: str = "sobel") -> dict:
    """Return Gx, Gy, magnitude sqrt(Gx^2+Gy^2) and direction (degrees, -180..180]."""
    gray = ensure_gray(gray)
    if operator not in KERNELS:
        raise ImageError(f"operator must be one of {sorted(KERNELS)}; got {operator!r}.")
    kx, ky = KERNELS[operator]
    gx = correlate2d(gray, kx, mode="edge")
    gy = correlate2d(gray, ky, mode="edge")
    return {"gx": gx, "gy": gy, "magnitude": np.hypot(gx, gy),
            "direction_deg": np.degrees(np.arctan2(gy, gx))}


def normalise_magnitude(mag: np.ndarray) -> np.ndarray:
    """Scale to 0..255 by the maximum (an all-zero response stays all zero)."""
    m = float(mag.max())
    return np.zeros(mag.shape, dtype=np.uint8) if m == 0 else to_uint8(mag / m * 255.0)


def edge_map(gray: np.ndarray, operator: str = "sobel", threshold: float = 0.0) -> np.ndarray:
    """Normalised gradient magnitude; if threshold (0..1 of the maximum) > 0 the result is
    binarised: 255 where magnitude >= threshold * max."""
    threshold = ensure_number(threshold, "threshold", 0, 1)
    mag = normalise_magnitude(gradients(gray, operator)["magnitude"])
    if threshold > 0:
        return np.where(mag >= threshold * 255.0, 255, 0).astype(np.uint8)
    return mag


def direction_image(gray: np.ndarray, operator: str = "sobel") -> np.ndarray:
    """Direction mapped to RGB: hue = angle, brightness = normalised magnitude (for display)."""
    from .colorspace import hsv_to_rgb
    g = gradients(gray, operator)
    hue = np.mod(g["direction_deg"], 360.0)
    v = normalise_magnitude(g["magnitude"]).astype(np.float64) / 255.0
    return hsv_to_rgb(np.stack([hue, np.ones_like(v), v], axis=2))


def non_max_suppression(mag: np.ndarray, direction_deg: np.ndarray) -> np.ndarray:
    """Keep a pixel only if it is >= both neighbours along the gradient direction.
    Direction is quantised to 0, 45, 90, 135 degrees (rows grow downward)."""
    ang = np.mod(direction_deg, 180.0)
    h, w = mag.shape
    p = pad2d(mag, (1, 1), (1, 1), "constant", 0)

    def nb(dy, dx):
        return p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]

    keep = np.zeros((h, w), dtype=bool)
    bins = [((ang < 22.5) | (ang >= 157.5), (0, 1), (0, -1)),      # horizontal gradient
            ((ang >= 22.5) & (ang < 67.5), (1, 1), (-1, -1)),      # towards down-right
            ((ang >= 67.5) & (ang < 112.5), (1, 0), (-1, 0)),      # vertical gradient
            ((ang >= 112.5) & (ang < 157.5), (1, -1), (-1, 1))]    # towards down-left
    for sel, a, b in bins:
        keep |= sel & (mag >= nb(*a)) & (mag >= nb(*b))
    return np.where(keep, mag, 0.0)


def _grow(seed: np.ndarray, allowed: np.ndarray, max_iter: int = 5000) -> np.ndarray:
    """Hysteresis: repeatedly add 'allowed' pixels that touch (8-neighbourhood) the current set."""
    cur = seed.copy()
    h, w = cur.shape
    for _ in range(max_iter):
        p = np.pad(cur, 1)
        near = np.zeros_like(cur)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                near |= p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        new = cur | (near & allowed)
        if (new == cur).all():
            break
        cur = new
    return cur


def canny(gray: np.ndarray, sigma: float = 1.4, low: float = 0.05, high: float = 0.15) -> dict:
    """Canny edge detector, all five stages manual:

    1. Gaussian smoothing (sigma)      2. Sobel gradient magnitude + direction
    3. Non-maximum suppression         4. Double threshold (fractions of max magnitude)
    5. Hysteresis: weak edges survive only if connected to a strong edge.

    Returns a dict with the intermediate images and the final binary 'edges'."""
    gray = ensure_gray(gray)
    sigma = ensure_number(sigma, "sigma", 0, 20, lo_open=True)
    low = ensure_number(low, "low threshold", 0, 1)
    high = ensure_number(high, "high threshold", 0, 1)
    if low > high:
        raise ImageError("low threshold must not exceed high threshold.")
    smooth = gaussian_filter(gray, sigma)
    g = gradients(smooth, "sobel")
    mag = g["magnitude"]
    thin = non_max_suppression(mag, g["direction_deg"])
    top = float(thin.max())
    if top == 0:
        z = np.zeros(gray.shape, dtype=np.uint8)
        return {"smoothed": smooth, "magnitude": z, "suppressed": z, "edges": z}
    strong = thin >= high * top
    weak = thin >= low * top
    edges = _grow(strong, weak)
    return {"smoothed": smooth, "magnitude": normalise_magnitude(mag),
            "suppressed": normalise_magnitude(thin),
            "edges": np.where(edges, 255, 0).astype(np.uint8)}
