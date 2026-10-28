"""ChayaPictureLab - a Digital Image Processing laboratory.

All core algorithms are implemented with NumPy so the mathematics is visible.
Pillow is used only for image file I/O, OpenCV only as an optional *reference*
implementation for validation (see chayalab/reference.py and tests/).

Conventions used everywhere in this package
-------------------------------------------
* Images are NumPy arrays of dtype uint8.
* Grayscale: shape (H, W).  Colour: shape (H, W, 3) in **RGB** channel order.
  (OpenCV's native order is BGR; use colorspace.bgr_to_rgb / rgb_to_bgr when
  talking to OpenCV.)
* Every function returns a new array and never modifies its input.
"""

__version__ = "1.0.0"
