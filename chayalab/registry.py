"""Operation registry: one place that describes every operation the app offers.

The Streamlit pages build their widgets from this table and the Algorithm
Comparison lab runs operations through ``run_operation``, so a parameter set
shown on screen is exactly the one that was executed (reproducible results).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from . import colorspace as cs
from . import edges, filters, histogram, morphology, point_ops
from .validation import ImageError, ensure_image

CATEGORIES = ["Point & colour", "Histogram & enhancement", "Filtering", "Edge detection", "Morphology"]


@dataclass
class Param:
    key: str
    label: str
    kind: str                      # 'int' | 'float' | 'choice' | 'bool'
    default: object
    min: float | None = None
    max: float | None = None
    step: float | None = None
    options: list | None = None
    help: str = ""


@dataclass
class Operation:
    key: str
    category: str
    func: Callable
    params: list[Param] = field(default_factory=list)
    needs_gray: bool = False
    purpose: str = ""
    formula: str = ""              # LaTeX
    impl: str = "Manual NumPy implementation"


OPERATIONS: dict[str, Operation] = {}


def _add(key, category, func, params=(), needs_gray=False, purpose="", formula="", impl="Manual NumPy implementation"):
    OPERATIONS[key] = Operation(key, category, func, list(params), needs_gray, purpose, formula, impl)


def P(key, label, kind, default, lo=None, hi=None, step=None, options=None, help=""):
    return Param(key, label, kind, default, lo, hi, step, options, help)


KS = lambda d=3, hi=15: P("ksize", "Window size (odd)", "int", d, 1, hi, 2, help="Odd window width/height k.")  # noqa: E731
CH = P("channel", "Channel", "choice", "R", options=["R", "G", "B"])

# ---------------------------------------------------------------- Point & colour
_add("Negative", "Point & colour", point_ops.negative,
     purpose="Inverts intensities: bright becomes dark.", formula=r"g = 255 - f")
_add("Brightness", "Point & colour", point_ops.adjust_brightness,
     [P("offset", "Offset", "int", 50, -255, 255, 1)],
     purpose="Adds a constant to every pixel (negative values darken). Results are clipped to 0..255.",
     formula=r"g = \mathrm{clip}(f + b,\,0,\,255)")
_add("Intensity scaling", "Point & colour", point_ops.scale_intensity,
     [P("factor", "Factor", "float", 0.5, 0.0, 4.0, 0.05, help="0.5 = divide by 2")],
     purpose="Multiplies intensities (factor < 1 divides). Replaces the old 'Division' operation.",
     formula=r"g = \mathrm{clip}(a\,f,\,0,\,255)")
_add("Contrast", "Point & colour", point_ops.adjust_contrast,
     [P("factor", "Contrast factor", "float", 1.5, 0.0, 4.0, 0.05)],
     purpose="Stretches (factor>1) or compresses (factor<1) intensities around mid-grey.",
     formula=r"g = \mathrm{clip}(127.5 + a\,(f-127.5))")
_add("Threshold", "Point & colour", point_ops.threshold, [P("t", "Threshold T", "int", 127, 0, 255, 1)],
     purpose="Binary image: white where intensity exceeds T.",
     formula=r"g=\begin{cases}255 & f>T\\0 & \text{otherwise}\end{cases}")
_add("Gamma correction", "Point & colour", point_ops.gamma_correct,
     [P("gamma", "Gamma", "float", 0.5, 0.1, 5.0, 0.05, help="<1 brightens, >1 darkens")],
     purpose="Power-law transform of normalised intensities; changes mid-tones most.",
     formula=r"g = 255\,c\left(\frac{f}{255}\right)^{\gamma}")
_add("Log transform", "Point & colour", point_ops.log_transform,
     purpose="Expands dark values, compresses bright ones.",
     formula=r"g = c\,\ln(1+f),\quad c=\frac{255}{\ln 256}")
_add("Grayscale", "Point & colour", cs.to_grayscale,
     [P("method", "Weights", "choice", "bt601", options=list(cs.GRAY_WEIGHTS))],
     purpose="Weighted sum of R, G, B.", formula=r"Y = 0.299R + 0.587G + 0.114B \;(\text{BT.601})")
_add("Extract channel (gray)", "Point & colour", cs.extract_channel, [CH],
     purpose="Shows one colour channel as a grayscale image.", formula=r"g = C(x,y),\; C\in\{R,G,B\}")
_add("Isolate channel (colour)", "Point & colour", cs.isolate_channel, [CH],
     purpose="Keeps one channel and zeroes the others.", formula=r"g = (C,0,0)\ \text{etc.}")
_add("Swap channels", "Point & colour", cs.swap_channels,
     [P("order", "Output order", "choice", "GRB", options=["GRB", "BGR", "RBG", "GBR", "BRG"],
        help="'GRB' = swap red and green")],
     purpose="Re-orders colour channels (false-colour image).", formula=r"(R',G',B') = \text{permutation of }(R,G,B)")
_add("Adjust channel", "Point & colour", cs.adjust_channel,
     [CH, P("offset", "Offset", "int", 40, -255, 255, 1), P("gain", "Gain", "float", 1.0, 0.0, 3.0, 0.05)],
     purpose="Changes the intensity of one colour channel only.", formula=r"C' = \mathrm{clip}(a\,C + b)")
_add("Eliminate channel", "Point & colour", cs.eliminate_channel, [CH],
     purpose="Sets one colour channel to zero.", formula=r"C' = 0")


def _hsv_op(img):
    parts = cs.hsv_channel_images(img)
    names = list(parts)
    return parts[names[0]], {n: parts[n] for n in names[1:]}


_add("HSV decomposition", "Point & colour", _hsv_op,
     purpose="Output is the Hue image; Saturation and Value are shown as extras.",
     formula=r"V=\max(R,G,B),\; S=\frac{V-\min}{V}")

# ---------------------------------------------------------------- Histogram & enhancement
_add("Histogram stretching", "Histogram & enhancement", histogram.stretch,
     [P("low_percent", "Low percentile", "float", 0.0, 0.0, 49.0, 0.5),
      P("high_percent", "High percentile", "float", 100.0, 51.0, 100.0, 0.5)], needs_gray=True,
     purpose="Linearly maps [lo, hi] to [0, 255]. Constant images are returned unchanged.",
     formula=r"g=\frac{f-f_{lo}}{f_{hi}-f_{lo}}\cdot 255")
_add("Histogram equalization", "Histogram & enhancement", histogram.equalize, needs_gray=True,
     purpose="Flattens the histogram using the cumulative distribution function.",
     formula=r"s_k=\mathrm{round}\!\left(255\,\frac{c_k-c_{min}}{1-c_{min}}\right),\; c_k=\sum_{j\le k}p_j")


def _otsu(img):
    out, t = histogram.otsu(img)
    return out, {f"Otsu chose T = {t}": out}


_add("Otsu threshold", "Histogram & enhancement", _otsu, needs_gray=True,
     purpose="Picks T that maximises the between-class variance.",
     formula=r"T^*=\arg\max_T \sigma_B^2(T)")
_add("Global threshold", "Histogram & enhancement", histogram.global_threshold,
     [P("t", "Threshold T", "int", 127, 0, 255, 1)], needs_gray=True,
     purpose="Binary segmentation with one fixed T.", formula=r"g=255\ \text{if}\ f>T")
_add("Adaptive threshold", "Histogram & enhancement", histogram.adaptive_threshold,
     [P("block_size", "Block size (odd)", "int", 11, 3, 101, 2), P("c", "C", "float", 2.0, -30.0, 30.0, 0.5),
      P("method", "Local statistic", "choice", "mean", options=["mean", "gaussian"])], needs_gray=True,
     purpose="Compares each pixel with its local mean; copes with uneven lighting.",
     formula=r"g=255\ \text{if}\ f>\mu_{local}-C")

# ---------------------------------------------------------------- Filtering
_add("Mean filter", "Filtering", filters.mean_filter, [KS(3)], purpose="Replaces each pixel by the window average.",
     formula=r"g=\frac1{k^2}\sum_{W}f")
_add("Gaussian filter", "Filtering", filters.gaussian_filter,
     [P("sigma", "Sigma", "float", 1.5, 0.1, 10.0, 0.1)], purpose="Weighted average with Gaussian weights.",
     formula=r"w(x,y)\propto e^{-(x^2+y^2)/2\sigma^2}")
_add("Median filter", "Filtering", filters.median_filter, [KS(3)],
     purpose="Middle value of the sorted window; excellent against salt-and-pepper noise.",
     formula=r"g=\mathrm{median}_{W}(f)")
_add("Mode filter", "Filtering", filters.mode_filter, [KS(3, 11)],
     purpose="Most frequent value in the window (ties -> smallest value). Different from the median. Slow on large colour images (seconds); best on images with few grey levels.",
     formula=r"g=\arg\max_v \#\{(i,j)\in W: f(i,j)=v\}")
_add("Minimum filter", "Filtering", filters.min_filter, [KS(3)], purpose="Smallest value in the window.",
     formula=r"g=\min_W f")
_add("Maximum filter", "Filtering", filters.max_filter, [KS(3)], purpose="Largest value in the window.",
     formula=r"g=\max_W f")
_add("Laplacian (response)", "Filtering", filters.laplacian_response, purpose="Absolute second derivative: highlights detail.",
     formula=r"|\nabla^2 f|=|4f-f_{N}-f_{S}-f_{E}-f_{W}|")
_add("Laplacian sharpening", "Filtering", filters.laplacian_sharpen, [P("amount", "Amount", "float", 1.0, 0.0, 5.0, 0.1)],
     purpose="Adds the Laplacian back to the image.", formula=r"g=f+a\,\nabla^2 f")
_add("Unsharp mask", "Filtering", filters.unsharp_mask,
     [P("sigma", "Blur sigma", "float", 1.5, 0.3, 10.0, 0.1), P("amount", "Amount", "float", 1.0, 0.0, 5.0, 0.1)],
     purpose="Amplifies the difference between the image and its blurred copy.", formula=r"g=f+a\,(f-G_\sigma * f)")
_add("Outlier filter", "Filtering", filters.outlier_filter,
     [P("threshold", "Threshold", "float", 30.0, 0.0, 255.0, 1.0), KS(3, 11)],
     purpose="Replaces a pixel with its window mean only if it differs by more than T.",
     formula=r"g=\bar f_W\ \text{if}\ |f-\bar f_W|>T,\ \text{else}\ f")

# ---------------------------------------------------------------- Edge detection
for _op, _txt in (("sobel", "Sobel"), ("prewitt", "Prewitt"), ("roberts", "Roberts")):
    _add(f"{_txt} edges", "Edge detection",
         (lambda o: (lambda img, threshold=0.0: edges.edge_map(img, o, threshold)))(_op),
         [P("threshold", "Binarise at (fraction of max, 0 = off)", "float", 0.0, 0.0, 1.0, 0.01)], needs_gray=True,
         purpose=f"{_txt} gradient magnitude (kernels applied manually).",
         formula=r"G=\sqrt{G_x^2+G_y^2},\ \theta=\mathrm{atan2}(G_y,G_x)")


def _canny(img, sigma=1.4, low=0.05, high=0.15):
    r = edges.canny(img, sigma, low, high)
    return r["edges"], {"Smoothed": r["smoothed"], "Gradient magnitude": r["magnitude"],
                        "After non-max suppression": r["suppressed"]}


_add("Canny edges", "Edge detection", _canny,
     [P("sigma", "Sigma", "float", 1.4, 0.3, 5.0, 0.1), P("low", "Low threshold", "float", 0.05, 0.0, 1.0, 0.01),
      P("high", "High threshold", "float", 0.15, 0.0, 1.0, 0.01)], needs_gray=True,
     purpose="Smooth -> gradient -> thin -> double threshold -> hysteresis (all stages manual).",
     formula=r"\text{NMS}+\text{hysteresis}(T_{low},T_{high})")
_add("Gradient direction (Sobel)", "Edge detection",
     lambda img: edges.direction_image(img, "sobel"), needs_gray=True,
     purpose="Hue encodes edge direction, brightness encodes strength.", formula=r"\theta=\mathrm{atan2}(G_y,G_x)")

# ---------------------------------------------------------------- Morphology
_SE = [P("shape", "Structuring element", "choice", "rect", options=list(morphology.SHAPES)),
       P("size", "SE size (odd)", "int", 3, 1, 15, 2),
       P("binarize", "Binarise first", "bool", False, help="Threshold at T before the operation"),
       P("t", "Binarise threshold T", "int", 127, 0, 255, 1)]


def _morph(fn):
    def run(img, shape="rect", size=3, binarize=False, t=127, **kw):
        if binarize:
            img = morphology.binarize(img, t)
        return fn(img, morphology.structuring_element(shape, size), **kw)
    return run


for _name, _fn, _txt, _f in (
        ("Erosion", morphology.erode, "Shrinks bright objects; removes small bright specks.", r"(f\ominus B)=\min_B f"),
        ("Dilation", morphology.dilate, "Grows bright objects; fills small gaps.", r"(f\oplus B)=\max_B f"),
        ("Opening", morphology.opening, "Erosion then dilation: removes small bright noise, keeps shape.", r"f\circ B=(f\ominus B)\oplus B"),
        ("Closing", morphology.closing, "Dilation then erosion: fills small dark holes.", r"f\bullet B=(f\oplus B)\ominus B")):
    _add(_name, "Morphology", _morph(_fn), list(_SE), needs_gray=True, purpose=_txt, formula=_f)

_add("Boundary extraction", "Morphology", _morph(morphology.boundary),
     list(_SE) + [P("kind", "Boundary type", "choice", "internal", options=["internal", "external", "gradient"])],
     needs_gray=True, purpose="Outlines objects: internal = f - erosion, external = dilation - f.",
     formula=r"\beta(f)=f-(f\ominus B)")


def operations_in(category: str) -> list[str]:
    return [k for k, o in OPERATIONS.items() if o.category == category]


def default_params(key: str) -> dict:
    return {p.key: p.default for p in OPERATIONS[key].params}


def run_operation(key: str, image: np.ndarray, params: dict | None = None) -> dict:
    """Run a registered operation. Returns {'image', 'extras', 'notes', 'params'}.

    Grayscale-only operations convert colour input with BT.601 and say so in 'notes'."""
    if key not in OPERATIONS:
        raise ImageError(f"Unknown operation {key!r}.")
    op = OPERATIONS[key]
    image = ensure_image(image)
    p = default_params(key)
    p.update(params or {})
    unknown = set(p) - {q.key for q in op.params}
    if unknown:
        raise ImageError(f"Unknown parameter(s) for {key}: {sorted(unknown)}")
    notes = []
    src = image
    if op.needs_gray and image.ndim == 3:
        src = cs.to_grayscale(image)
        notes.append("Colour input was converted to grayscale (BT.601) first.")
    if key in ("Extract channel (gray)", "Isolate channel (colour)", "Swap channels", "Adjust channel",
               "Eliminate channel", "HSV decomposition") and image.ndim == 2:
        raise ImageError(f"'{key}' needs a colour image.")
    res = op.func(src, **p)
    extras = {}
    if isinstance(res, tuple):
        res, extras = res
    return {"image": res, "extras": extras, "notes": notes, "params": p}
