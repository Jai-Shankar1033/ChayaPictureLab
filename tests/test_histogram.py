import numpy as np
import pytest

from chayalab import histogram as H
from chayalab import reference as ref
from chayalab.validation import ImageError


def test_histogram_counts_pdf_cdf():
    a = np.array([[0, 0, 1], [1, 1, 255]], np.uint8)
    h = H.compute_histogram(a)
    assert h.shape == (256,) and h[0] == 2 and h[1] == 3 and h[255] == 1 and h.sum() == 6
    assert H.probability_distribution(a).sum() == pytest.approx(1.0)
    c = H.cumulative_distribution(a)
    assert np.all(np.diff(c) >= 0) and c[-1] == pytest.approx(1.0) and c[1] == pytest.approx(5 / 6)


def test_equalization_known_example():
    # levels 10,20,30,40 each equally frequent -> CDF 0.25,.5,.75,1 -> mapping 0, 85, 170, 255
    a = np.array([[10, 20], [30, 40]], np.uint8)
    assert H.equalize(a).tolist() == [[0, 85], [170, 255]]


def test_equalization_constant_image_unchanged_not_crashing():
    a = np.full((5, 5), 77, np.uint8)
    assert np.array_equal(H.equalize(a), a)


def test_equalization_narrow_range_expands_to_full_range():
    a = np.array([[100, 101], [102, 103]], np.uint8)
    out = H.equalize(a)
    assert out.min() == 0 and out.max() == 255


def test_equalization_monotonic_mapping(gray):
    lut = H.equalization_mapping(gray)
    present = np.unique(gray)
    assert np.all(np.diff(lut[present].astype(int)) >= 0)


def test_equalization_vs_opencv_max_difference(gray):
    cv_out = ref.opencv_equalize(gray)
    if cv_out is None:
        pytest.skip("OpenCV not installed")
    assert np.abs(cv_out.astype(int) - H.equalize(gray).astype(int)).max() <= 1


def test_equalization_vs_opencv_on_gradient_image():
    cv_out = ref.opencv_equalize(np.tile(np.arange(40, 200, dtype=np.uint8), (30, 1)))
    if cv_out is None:
        pytest.skip("OpenCV not installed")
    g = np.tile(np.arange(40, 200, dtype=np.uint8), (30, 1))
    assert np.abs(cv_out.astype(int) - H.equalize(g).astype(int)).max() <= 1


def test_stretch_known_values_and_constant():
    a = np.array([[50, 100, 150]], np.uint8)
    assert H.stretch(a).tolist() == [[0, 128, 255]]
    c = np.full((3, 3), 9, np.uint8)
    assert np.array_equal(H.stretch(c), c)
    with pytest.raises(ImageError):
        H.stretch(a, 60, 40)


def test_stretch_percentile_clips_outliers():
    a = np.concatenate([np.full(98, 100), [0, 255]]).astype(np.uint8).reshape(10, 10)
    out = H.stretch(a, 2, 98)
    assert out.dtype == np.uint8 and out.min() == 0 and out.max() == 255


def test_global_threshold():
    a = np.array([[10, 127, 128, 200]], np.uint8)
    assert H.global_threshold(a, 127).tolist() == [[0, 0, 255, 255]]


def test_otsu_bimodal_between_the_modes():
    a = np.concatenate([np.full(500, 40), np.full(500, 200)]).astype(np.uint8).reshape(25, 40)
    out, t = H.otsu(a)
    assert 40 <= t < 200
    assert set(np.unique(out)) == {0, 255}


def test_otsu_constant_image_does_not_crash():
    out, t = H.otsu(np.full((4, 4), 50, np.uint8))
    assert t == 0 and out.shape == (4, 4)


def test_otsu_matches_opencv(rng):
    img = np.clip(np.concatenate([rng.normal(70, 15, 4000), rng.normal(180, 20, 4000)]), 0, 255).astype(np.uint8).reshape(80, 100)
    cv_t = ref.opencv_otsu_threshold(img)
    if cv_t is None:
        pytest.skip("OpenCV not installed")
    assert abs(cv_t - H.otsu_threshold(img)) <= 1


def test_adaptive_threshold_uniform_background_and_bright_dot():
    a = np.full((21, 21), 100, np.uint8)
    a[10, 10] = 200
    out = H.adaptive_threshold(a, 5, 2.0)
    assert out[10, 10] == 255
    assert out[0, 0] == 255   # f > mean - C  (100 > 98) in a flat area


def test_adaptive_threshold_agrees_with_opencv_interior(rng):
    cv2 = pytest.importorskip("cv2")
    img = rng.integers(0, 256, (60, 60), dtype=np.uint8)
    ours = H.adaptive_threshold(img, 11, 2.0)
    theirs = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    inner = (slice(5, -5), slice(5, -5))
    assert (ours[inner] == theirs[inner]).mean() >= 0.98


def test_adaptive_threshold_invalid_params(gray):
    for kw in ({"block_size": 4}, {"block_size": 1}, {"method": "x"}):
        with pytest.raises(ImageError):
            H.adaptive_threshold(gray, **kw)


def test_histogram_functions_reject_colour(color):
    with pytest.raises(ImageError):
        H.compute_histogram(color)


def test_adaptive_threshold_differences_from_opencv_are_explained_by_integer_rounding():
    """OpenCV rounds the local mean to an integer; our exact float mean differs slightly.
    Emulating that rounding must reproduce OpenCV's output exactly on a real-looking image."""
    cv2 = pytest.importorskip("cv2")
    from pathlib import Path
    from chayalab._windows import separable_correlate
    from chayalab.colorspace import to_grayscale
    from chayalab.io_utils import load_image
    sample = Path(__file__).resolve().parents[1] / "samples" / "scene.png"
    g = to_grayscale(load_image(sample.read_bytes())[0])
    theirs = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    rounded_mean = np.floor(separable_correlate(g, np.full(11, 1 / 11)) + 0.5)
    emulated = np.where(g.astype(float) > rounded_mean - 2, 255, 0).astype(np.uint8)
    inner = (slice(5, -5), slice(5, -5))
    assert np.array_equal(emulated[inner], theirs[inner])
