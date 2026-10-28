import numpy as np
import pytest

from chayalab import point_ops as po
from chayalab.validation import ImageError, ensure_image, ensure_odd, to_uint8


def test_to_uint8_clips_and_rounds_instead_of_wrapping():
    assert to_uint8([-3.0, 0.4, 0.5, 254.6, 300.0]).tolist() == [0, 0, 1, 255, 255]


@pytest.mark.parametrize("bad", [None, [1, 2], np.zeros((0, 4), np.uint8), np.zeros((4, 4), np.float64),
                                 np.zeros((4, 4, 4), np.uint8), np.zeros((2, 2, 2, 3), np.uint8)])
def test_ensure_image_rejects_bad_input(bad):
    with pytest.raises(ImageError):
        ensure_image(bad)


@pytest.mark.parametrize("v", [0, 2, 4, -1, 1.5, "x", True, 1000])
def test_ensure_odd_rejects(v):
    with pytest.raises(ImageError):
        ensure_odd(v)


def test_negative_known_values_and_dtype():
    a = np.array([[0, 100, 255]], np.uint8)
    out = po.negative(a)
    assert out.tolist() == [[255, 155, 0]] and out.dtype == np.uint8
    assert np.array_equal(po.negative(po.negative(a)), a)


def test_brightness_clips_without_wraparound():
    a = np.array([[0, 100, 250]], np.uint8)
    assert po.adjust_brightness(a, 10).tolist() == [[10, 110, 255]]
    assert po.adjust_brightness(a, -50).tolist() == [[0, 50, 200]]


def test_contrast_identity_and_pivot():
    a = np.array([[0, 100, 255]], np.uint8)
    assert np.array_equal(po.adjust_contrast(a, 1.0), a)
    assert po.adjust_contrast(np.full((2, 2), 128, np.uint8), 3.0, pivot=128).tolist() == [[128, 128], [128, 128]]
    # default pivot 127.5: 128 -> 127.5 + 3*0.5 = 129
    assert po.adjust_contrast(np.array([[128]], np.uint8), 3.0).tolist() == [[129]]


def test_threshold_strictly_greater():
    a = np.array([[126, 127, 128]], np.uint8)
    assert po.threshold(a, 127).tolist() == [[0, 0, 255]]


def test_gamma_formula_and_identity():
    a = np.array([[0, 64, 128, 255]], np.uint8)
    assert np.array_equal(po.gamma_correct(a, 1.0), a)
    expected = np.round(255 * (a / 255.0) ** 0.5).astype(np.uint8)
    assert np.array_equal(po.gamma_correct(a, 0.5), expected)
    assert po.gamma_correct(a, 0.5)[0, 1] > 64 > po.gamma_correct(a, 2.0)[0, 1]


def test_log_maps_endpoints():
    a = np.array([[0, 255]], np.uint8)
    assert po.log_transform(a).tolist() == [[0, 255]]


@pytest.mark.parametrize("fn,arg", [(po.gamma_correct, 0), (po.gamma_correct, -1), (po.gamma_correct, float("nan")),
                                    (po.adjust_brightness, 999), (po.threshold, 300), (po.adjust_contrast, -1)])
def test_invalid_parameters(fn, arg, gray):
    with pytest.raises(ImageError):
        fn(gray, arg)


def test_color_and_gray_shapes_preserved(gray, color):
    for fn in (po.negative, lambda x: po.gamma_correct(x, 0.7), lambda x: po.adjust_brightness(x, 5)):
        assert fn(gray).shape == gray.shape and fn(color).shape == color.shape
        assert fn(color).dtype == np.uint8


def test_combine_images_no_wraparound_and_shape_check():
    a = np.array([[200, 10]], np.uint8)
    b = np.array([[100, 20]], np.uint8)
    assert po.combine_images(a, b, "add").tolist() == [[255, 30]]
    assert po.combine_images(a, b, "subtract").tolist() == [[100, 0]]
    assert po.combine_images(a, b, "absdiff").tolist() == [[100, 10]]
    assert po.combine_images(a, b, "blend", 0.5).tolist() == [[150, 15]]
    with pytest.raises(ImageError):
        po.combine_images(a, np.zeros((2, 2), np.uint8))


def test_single_pixel_and_input_not_modified(gray):
    one = np.array([[7]], np.uint8)
    assert po.negative(one).tolist() == [[248]]
    before = gray.copy()
    po.negative(gray); po.gamma_correct(gray, 0.5)
    assert np.array_equal(gray, before)
