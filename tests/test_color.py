import numpy as np
import pytest

from chayalab import colorspace as cs
from chayalab.validation import ImageError


def test_channel_order_is_rgb():
    red = np.zeros((2, 2, 3), np.uint8); red[..., 0] = 200
    assert cs.extract_channel(red, "R").max() == 200
    assert cs.extract_channel(red, "B").max() == 0
    assert np.array_equal(cs.eliminate_channel(red, "R"), np.zeros_like(red))


def test_bgr_rgb_roundtrip_and_cv2_agreement(color):
    cv2 = pytest.importorskip("cv2")
    assert np.array_equal(cs.rgb_to_bgr(cs.bgr_to_rgb(color)), color)
    assert np.array_equal(cs.rgb_to_bgr(color), cv2.cvtColor(color, cv2.COLOR_RGB2BGR))


def test_swap_channels_swaps_red_and_green():
    px = np.array([[[10, 20, 30]]], np.uint8)
    assert cs.swap_channels(px, "GRB").tolist() == [[[20, 10, 30]]]
    with pytest.raises(ImageError):
        cs.swap_channels(px, "RRB")


def test_grayscale_weights_known_values():
    px = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 255, 255]]], np.uint8)
    assert cs.to_grayscale(px).tolist() == [[76, 150, 29, 255]]   # 0.299*255=76.2, 0.587*255=149.7, 0.114*255=29.07


def test_grayscale_matches_opencv_within_one(color):
    cv2 = pytest.importorskip("cv2")
    ref = cv2.cvtColor(color, cv2.COLOR_RGB2GRAY).astype(int)
    assert np.abs(ref - cs.to_grayscale(color).astype(int)).max() <= 1


def test_adjust_channel_clips_and_only_touches_one_channel():
    px = np.array([[[250, 100, 5]]], np.uint8)
    out = cs.adjust_channel(px, "R", offset=50)
    assert out.tolist() == [[[255, 100, 5]]]
    assert cs.adjust_channel(px, "B", offset=-50).tolist() == [[[250, 100, 0]]]


def test_color_ops_reject_gray(gray):
    with pytest.raises(ImageError):
        cs.swap_channels(gray)


def test_hsv_known_colours_and_roundtrip(color):
    px = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255], [0, 0, 0], [128, 128, 128]]], np.uint8)
    hsv = cs.rgb_to_hsv(px)[0]
    assert hsv[:3, 0].tolist() == [0.0, 120.0, 240.0]
    assert hsv[3].tolist() == [0.0, 0.0, 0.0] and hsv[4, 1] == 0.0
    assert np.abs(cs.hsv_to_rgb(cs.rgb_to_hsv(color)).astype(int) - color.astype(int)).max() <= 1


def test_hsv_matches_opencv_hue(color):
    cv2 = pytest.importorskip("cv2")
    ref = cv2.cvtColor(color, cv2.COLOR_RGB2HSV_FULL)   # H scaled to 0..255
    ours = cs.rgb_to_hsv(color)
    diff = np.abs(ours[..., 0] / 360 * 255 - ref[..., 0])
    diff = np.minimum(diff, 255 - diff)
    mask = ours[..., 1] > 0.1
    assert diff[mask].max() <= 1.5
