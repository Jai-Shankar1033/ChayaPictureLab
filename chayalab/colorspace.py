"""Colour operations. All colour images are RGB (H, W, 3) uint8 unless stated."""
from __future__ import annotations

import numpy as np

from .validation import ImageError, ensure_image, ensure_number, to_uint8

CHANNELS = {"R": 0, "G": 1, "B": 2}
GRAY_WEIGHTS = {
    "bt601": (0.299, 0.587, 0.114),   # classic "luma" used by OpenCV / Pillow
    "bt709": (0.2126, 0.7152, 0.0722),
    "mean": (1 / 3, 1 / 3, 1 / 3),
}


def _require_color(img, name="image") -> np.ndarray:
    img = ensure_image(img, name)
    if img.ndim != 3:
        raise ImageError(f"{name} must be a colour (RGB) image for this operation.")
    return img


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    """Reverse the channel axis (BGR <-> RGB are the same operation)."""
    return _require_color(img)[:, :, ::-1].copy()


rgb_to_bgr = bgr_to_rgb


def to_grayscale(img: np.ndarray, method: str = "bt601") -> np.ndarray:
    """Weighted sum of channels: Y = wR*R + wG*G + wB*B. Gray input is returned as a copy."""
    img = ensure_image(img)
    if img.ndim == 2:
        return img.copy()
    if method not in GRAY_WEIGHTS:
        raise ImageError(f"Unknown grayscale method {method!r}; choose from {sorted(GRAY_WEIGHTS)}.")
    w = np.array(GRAY_WEIGHTS[method])
    return to_uint8(img.astype(np.float64) @ w)


def gray_to_rgb(img: np.ndarray) -> np.ndarray:
    img = ensure_image(img)
    return np.repeat(img[:, :, None], 3, axis=2) if img.ndim == 2 else img.copy()


def extract_channel(img: np.ndarray, channel: str) -> np.ndarray:
    """Return one channel as a grayscale (H, W) image."""
    img = _require_color(img)
    if channel not in CHANNELS:
        raise ImageError(f"channel must be one of R, G, B; got {channel!r}.")
    return img[:, :, CHANNELS[channel]].copy()


def isolate_channel(img: np.ndarray, channel: str) -> np.ndarray:
    """Keep one channel and set the other two to zero (a 'tinted' view)."""
    out = np.zeros_like(_require_color(img))
    c = CHANNELS[channel] if channel in CHANNELS else None
    if c is None:
        raise ImageError(f"channel must be one of R, G, B; got {channel!r}.")
    out[:, :, c] = img[:, :, c]
    return out


def swap_channels(img: np.ndarray, order: str = "GRB") -> np.ndarray:
    """Re-order channels. ``order`` is a permutation of 'RGB', e.g. 'GRB' swaps R and G:
    output channel k is taken from input channel order[k]."""
    img = _require_color(img)
    order = order.upper()
    if sorted(order) != ["B", "G", "R"]:
        raise ImageError(f"order must be a permutation of 'RGB', got {order!r}.")
    return img[:, :, [CHANNELS[c] for c in order]].copy()


def adjust_channel(img: np.ndarray, channel: str, offset: float = 0, gain: float = 1.0) -> np.ndarray:
    """channel' = clip(gain * channel + offset); other channels unchanged."""
    img = _require_color(img)
    if channel not in CHANNELS:
        raise ImageError(f"channel must be one of R, G, B; got {channel!r}.")
    offset = ensure_number(offset, "offset", -255, 255)
    gain = ensure_number(gain, "gain", 0, 10)
    out = img.copy()
    c = CHANNELS[channel]
    out[:, :, c] = to_uint8(gain * img[:, :, c].astype(np.float64) + offset)
    return out


def eliminate_channel(img: np.ndarray, channel: str) -> np.ndarray:
    """Set one channel to 0."""
    img = _require_color(img)
    if channel not in CHANNELS:
        raise ImageError(f"channel must be one of R, G, B; got {channel!r}.")
    out = img.copy()
    out[:, :, CHANNELS[channel]] = 0
    return out


def rgb_to_hsv(img: np.ndarray) -> np.ndarray:
    """Convert RGB uint8 to float HSV: H in [0, 360), S and V in [0, 1].

    V = max(R,G,B); S = (max-min)/max (0 if max=0); H from which channel is max."""
    x = _require_color(img).astype(np.float64) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    mx, mn = x.max(axis=2), x.min(axis=2)
    d = mx - mn
    safe = np.where(d == 0, 1.0, d)
    h = np.zeros_like(mx)
    h = np.where(mx == r, ((g - b) / safe) % 6, h)
    h = np.where((mx == g) & (mx != r), (b - r) / safe + 2, h)
    h = np.where((mx == b) & (mx != r) & (mx != g), (r - g) / safe + 4, h)
    h = np.where(d == 0, 0.0, h) * 60.0
    s = np.where(mx == 0, 0.0, d / np.where(mx == 0, 1.0, mx))
    return np.stack([h % 360.0, s, mx], axis=2)


def hsv_to_rgb(hsv: np.ndarray) -> np.ndarray:
    """Inverse of rgb_to_hsv (H in degrees, S,V in [0,1]) -> RGB uint8."""
    hsv = np.asarray(hsv, dtype=np.float64)
    if hsv.ndim != 3 or hsv.shape[2] != 3:
        raise ImageError("hsv must have shape (H, W, 3).")
    h, s, v = hsv[..., 0] % 360.0 / 60.0, hsv[..., 1], hsv[..., 2]
    c = v * s
    x = c * (1 - np.abs(h % 2 - 1))
    m = v - c
    sector = np.floor(h).astype(int) % 6
    zeros = np.zeros_like(c)
    table = [(c, x, zeros), (x, c, zeros), (zeros, c, x), (zeros, x, c), (x, zeros, c), (c, zeros, x)]
    r = np.choose(sector, [t[0] for t in table])
    g = np.choose(sector, [t[1] for t in table])
    b = np.choose(sector, [t[2] for t in table])
    return to_uint8(np.stack([r + m, g + m, b + m], axis=2) * 255.0)


def hsv_channel_images(img: np.ndarray) -> dict[str, np.ndarray]:
    """Hue, Saturation and Value rendered as 8-bit grayscale images for display."""
    hsv = rgb_to_hsv(img)
    return {"Hue (0-360 deg -> 0-255)": to_uint8(hsv[..., 0] / 360.0 * 255.0),
            "Saturation": to_uint8(hsv[..., 1] * 255.0),
            "Value": to_uint8(hsv[..., 2] * 255.0)}
