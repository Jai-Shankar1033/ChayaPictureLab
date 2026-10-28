"""Optional OpenCV reference implementations, used ONLY to validate our own code.

OpenCV is imported lazily; when it is not installed the functions return None."""
from __future__ import annotations

import numpy as np


def _cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        return None


def opencv_equalize(gray: np.ndarray):
    cv2 = _cv2()
    return None if cv2 is None else cv2.equalizeHist(gray)


def opencv_otsu_threshold(gray: np.ndarray):
    cv2 = _cv2()
    return None if cv2 is None else int(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0])


def opencv_canny(gray: np.ndarray, low: int, high: int):
    cv2 = _cv2()
    return None if cv2 is None else cv2.Canny(gray, low, high)
