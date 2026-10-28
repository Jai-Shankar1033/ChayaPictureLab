import numpy as np
import pytest

from chayalab import filters as F
from chayalab.validation import ImageError


def brute(img, k, fn):
    r = k // 2
    p = np.pad(img, r, mode="reflect")
    out = np.empty_like(img)
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            out[i, j] = fn(p[i:i + k, j:j + k].ravel())
    return out


def brute_mode(w):
    vals, counts = np.unique(w, return_counts=True)   # ascending values
    return vals[np.argmax(counts)]                      # argmax -> first max -> smallest value on ties


def test_median_matches_bruteforce(gray):
    for k in (3, 5):
        assert np.array_equal(F.median_filter(gray, k), brute(gray, k, lambda w: np.sort(w)[len(w) // 2]))


def test_mode_matches_bruteforce_including_ties(rng):
    img = rng.integers(0, 4, (20, 23), dtype=np.uint8)   # few levels -> many ties
    for k in (3, 5):
        assert np.array_equal(F.mode_filter(img, k), brute(img, k, brute_mode))


def test_mode_is_not_median():
    # window values {1,1,1,9,9,9,9? } build a 3x3 patch where median != mode
    patch = np.array([[5, 5, 5], [5, 1, 1], [9, 9, 9]], np.uint8)   # sorted 1,1,5,5,5,5,9,9,9 -> median 5, mode 5
    patch2 = np.array([[1, 1, 1], [1, 7, 8], [9, 9, 9]], np.uint8)  # sorted 1,1,1,1,7,8,9,9,9 -> median 7, mode 1
    img = np.pad(patch2, 3, mode="constant", constant_values=7)     # surround so centre window is exactly patch2
    c = (4, 4)
    assert F.median_filter(img, 3)[c] == 7
    assert F.mode_filter(img, 3)[c] == 1
    assert not np.array_equal(F.median_filter(patch2, 3), F.mode_filter(patch2, 3))


def test_mode_tie_rule_smallest_value():
    img = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], np.uint8)   # all different -> every count 1 in centre window
    assert F.mode_filter(img, 3)[1, 1] == 1


def test_mode_keeps_dtype_shape_colour(color):
    out = F.mode_filter(color, 3)
    assert out.shape == color.shape and out.dtype == np.uint8


def test_filters_constant_image_unchanged():
    a = np.full((6, 7), 90, np.uint8)
    for fn in (F.mean_filter, F.median_filter, F.mode_filter, F.min_filter, F.max_filter, F.gaussian_filter):
        assert np.array_equal(fn(a), a), fn.__name__


def test_mean_filter_known_example():
    a = np.zeros((5, 5), np.uint8); a[2, 2] = 90
    out = F.mean_filter(a, 3)
    assert out[2, 2] == 10 and out[1, 1] == 10 and out[0, 0] == 0


def test_min_max_known_example():
    a = np.array([[1, 9, 1], [9, 5, 9], [1, 9, 1]], np.uint8)
    assert F.max_filter(a, 3)[1, 1] == 9 and F.min_filter(a, 3)[1, 1] == 1


def test_min_max_vs_bruteforce(gray):
    assert np.array_equal(F.max_filter(gray, 5), brute(gray, 5, np.max))
    assert np.array_equal(F.min_filter(gray, 5), brute(gray, 5, np.min))


def test_gaussian_kernel_properties():
    k = F.gaussian_kernel_1d(1.5)
    assert k.sum() == pytest.approx(1.0) and len(k) % 2 == 1 and np.argmax(k) == len(k) // 2
    assert np.allclose(k, k[::-1])


def test_gaussian_matches_opencv_closely(gray):
    cv2 = pytest.importorskip("cv2")
    ours = F.gaussian_filter(gray, 1.5, ksize=9)
    theirs = cv2.GaussianBlur(gray, (9, 9), 1.5, borderType=cv2.BORDER_REFLECT_101)
    assert np.abs(ours.astype(int) - theirs.astype(int)).max() <= 1


def test_median_vs_opencv_interior(gray):
    cv2 = pytest.importorskip("cv2")
    assert np.array_equal(F.median_filter(gray, 5)[3:-3, 3:-3], cv2.medianBlur(gray, 5)[3:-3, 3:-3])


def test_median_removes_isolated_impulse_but_mean_does_not():
    a = np.full((9, 9), 100, np.uint8); a[4, 4] = 255
    assert F.median_filter(a, 3)[4, 4] == 100
    assert F.mean_filter(a, 3)[4, 4] > 100


def test_sharpen_increases_edge_contrast():
    a = np.zeros((8, 8), np.uint8); a[:, 4:] = 100
    s = F.unsharp_mask(a, 1.0, 1.5)
    assert s[:, 3].min() < 0 + 1 and s[:, 4].max() > 100
    l = F.laplacian_sharpen(a, 1.0)
    assert l[:, 4].max() > 100 and l.dtype == np.uint8


def test_laplacian_of_constant_is_zero():
    assert F.laplacian_response(np.full((5, 5), 200, np.uint8)).max() == 0


def test_outlier_filter_replaces_only_outliers():
    a = np.full((7, 7), 50, np.uint8); a[3, 3] = 255
    out = F.outlier_filter(a, 30, 3)
    assert out[3, 3] < 255 and out[0, 0] == 50


def test_tiny_images_do_not_crash():
    one = np.array([[42]], np.uint8)
    for fn in (F.mean_filter, F.median_filter, F.mode_filter, F.min_filter, F.max_filter, F.gaussian_filter):
        assert fn(one).tolist() == [[42]], fn.__name__
    two = np.array([[1, 2], [3, 4]], np.uint8)
    assert F.median_filter(two, 5).shape == (2, 2)


@pytest.mark.parametrize("bad", [0, 2, -3, 1.5])
def test_even_or_invalid_kernel_rejected(bad, gray):
    for fn in (F.mean_filter, F.median_filter, F.mode_filter, F.min_filter, F.max_filter):
        with pytest.raises(ImageError):
            fn(gray, bad)


def test_filters_do_not_modify_input(gray):
    before = gray.copy()
    F.median_filter(gray); F.mode_filter(gray); F.gaussian_filter(gray); F.unsharp_mask(gray)
    assert np.array_equal(gray, before)


def test_laplacian_saturates_instead_of_wrapping():
    """Regression: the old code did np.uint8(abs(response)), turning 1020 into 252 (wrap-around)."""
    a = np.zeros((7, 7), np.uint8); a[3, 3] = 255
    assert F.laplacian_response(a)[3, 3] == 255          # true response is 4*255 = 1020 -> clipped to 255
