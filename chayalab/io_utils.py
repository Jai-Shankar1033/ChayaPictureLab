"""Image loading / saving (Pillow). Everything inside the app is RGB uint8."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from .validation import ImageError, ensure_image

SUPPORTED_EXTENSIONS = ["jpg", "jpeg", "png", "bmp", "webp"]
OUTPUT_FORMATS = {"PNG": ("png", "image/png"), "JPEG": ("jpg", "image/jpeg"), "BMP": ("bmp", "image/bmp")}


def load_image(data: bytes, max_side: int | None = 1024) -> tuple[np.ndarray, dict]:
    """Decode bytes -> (RGB uint8 array, info). Applies EXIF rotation, composites
    transparency over white, and shrinks (never enlarges) so the longest side <= max_side.

    Raises ImageError with a friendly message if the data is not a readable image."""
    if not data:
        raise ImageError("The file is empty.")
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt = (im.format or "?").upper()
            im = ImageOps.exif_transpose(im)
            original_size = im.size
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                rgba = im.convert("RGBA")
                bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                im = Image.alpha_composite(bg, rgba).convert("RGB")
            else:
                im = im.convert("RGB")
            resized = False
            if max_side and max(im.size) > max_side:
                scale = max_side / max(im.size)
                im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))),
                               Image.LANCZOS)
                resized = True
            arr = np.array(im, dtype=np.uint8)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageError("Could not read this file as an image (it may be corrupted or an "
                         f"unsupported type). Details: {type(exc).__name__}") from exc
    return arr, {"format": fmt, "original_size": original_size, "resized": resized,
                 "bytes": len(data)}


def encode_image(img: np.ndarray, fmt: str = "PNG") -> bytes:
    """Encode an RGB/gray array to PNG, JPEG or BMP bytes."""
    img = ensure_image(img)
    if fmt not in OUTPUT_FORMATS:
        raise ImageError(f"Unsupported output format {fmt!r}.")
    buf = io.BytesIO()
    kwargs = {"quality": 95} if fmt == "JPEG" else {}
    Image.fromarray(img).save(buf, format=fmt, **kwargs)
    return buf.getvalue()


def resize_to(img: np.ndarray, shape_hw: tuple[int, int]) -> np.ndarray:
    """Resize (bilinear) to (height, width); used to match a second image."""
    img = ensure_image(img)
    h, w = shape_hw
    return np.array(Image.fromarray(img).resize((w, h), Image.BILINEAR), dtype=np.uint8)
