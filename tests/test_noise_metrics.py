import numpy as np
import pytest

from chayalab import filters as F
from chayalab import metrics as M
from chayalab import noise as N
from chayalab.validation import ImageError


def test_gaussian_noise_is_zero_mean_no_brightening():
    """Regression for the old bug: negative noise cast to uint8 wrapped around and brightened the image."""
    base = np.full((200, 200), 128, np.uint8)
    noisy = N.gaussian_noise(base, sigma=20, seed=0)
    assert abs(noisy.astype(float).mean() - 128) < 1.0
    assert noisy.std() == pytest.approx(20, rel=0.05)


def test_gaussian_noise_positive_mean_shifts_by_mean():
    base = np.full((200, 200), 100, np.uint8)
    assert N.gaussian_noise(base, 5, mean=30, seed=1).astype(float).mean() == pytest.approx(130, abs=1)


def test_gaussian_noise_clips_and_reproducible(gray):
    a = N.gaussian_noise(gray, 80, seed=7)
    b = N.gaussian_noise(gray, 80, seed=7)
    assert np.array_equal(a, b) and a.dtype == np.uint8
    assert not np.array_equal(a, N.gaussian_noise(gray, 80, seed=8))


def test_gaussian_sigma_zero_is_identity(gray):
    assert np.array_equal(N.gaussian_noise(gray, 0, seed=1), gray)


def test_salt_pepper_density_and_values():
    base = np.full((300, 300), 100, np.uint8)
    out = N.salt_pepper_noise(base, 0.10, seed=3)
    changed = out != base
    assert changed.mean() == pytest.approx(0.10, abs=0.01)
    assert set(np.unique(out[changed])) <= {0, 255}
    assert (out == 255).sum() == pytest.approx((out == 0).sum(), rel=0.15)


def test_salt_pepper_extremes_and_colour(color):
    assert np.array_equal(N.salt_pepper_noise(color, 0.0, seed=1), color)
    full = N.salt_pepper_noise(color, 1.0, 1.0, seed=1)
    assert (full == 255).all()
    out = N.salt_pepper_noise(color, 0.2, seed=2)
    hit = (out != color).any(axis=2)
    assert (out[hit][:, 0] == out[hit][:, 1]).all()      # same value in all channels at a hit pixel


@pytest.mark.parametrize("bad", [-0.1, 1.5, float("nan")])
def test_salt_pepper_invalid(bad, gray):
    with pytest.raises(ImageError):
        N.salt_pepper_noise(gray, bad)


def test_median_restores_salt_pepper_better_than_mean():
    rng = np.random.default_rng(5)
    clean = np.tile(np.linspace(40, 200, 120).astype(np.uint8), (120, 1))
    noisy = N.salt_pepper_noise(clean, 0.05, seed=5)
    assert M.psnr(clean, F.median_filter(noisy, 3)) > M.psnr(clean, F.mean_filter(noisy, 3)) > M.psnr(clean, noisy) - 10
    assert M.psnr(clean, F.median_filter(noisy, 3)) > M.psnr(clean, noisy)


def test_gaussian_denoising_improves_psnr():
    clean = np.tile(np.linspace(40, 200, 150).astype(np.uint8), (150, 1))
    noisy = N.gaussian_noise(clean, 25, seed=9)
    assert M.psnr(clean, F.gaussian_filter(noisy, 1.2)) > M.psnr(clean, noisy)


def test_image_averaging_reduces_noise_by_about_sqrt_n():
    base = np.full((200, 200), 128, np.uint8)
    one = N.average_noisy_copies(base, 1, 20, seed=1).astype(float).std()
    sixteen = N.average_noisy_copies(base, 16, 20, seed=1).astype(float).std()
    assert sixteen == pytest.approx(one / 4, rel=0.15)
    assert abs(N.average_noisy_copies(base, 16, 20, seed=1).astype(float).mean() - 128) < 1.0


def test_mse_psnr_known_values():
    a = np.zeros((4, 4), np.uint8)
    b = np.full((4, 4), 10, np.uint8)
    assert M.mse(a, b) == 100.0
    assert M.psnr(a, b) == pytest.approx(10 * np.log10(255 ** 2 / 100))
    assert M.mse(b, a) == 100.0


def test_psnr_identical_is_infinite_not_error(gray):
    assert M.mse(gray, gray) == 0.0 and M.psnr(gray, gray) == float("inf")


def test_mse_no_uint8_wraparound():
    a = np.array([[0]], np.uint8); b = np.array([[250]], np.uint8)
    assert M.mse(a, b) == 62500.0 and M.mse(b, a) == 62500.0


def test_metrics_reject_mismatched_shapes(gray, color):
    with pytest.raises(ImageError):
        M.mse(gray, gray[:-1])
    with pytest.raises(ImageError):
        M.psnr(gray, color)


def test_psnr_matches_opencv(gray, rng):
    cv2 = pytest.importorskip("cv2")
    other = rng.integers(0, 256, gray.shape, dtype=np.uint8)
    assert M.psnr(gray, other) == pytest.approx(cv2.PSNR(gray, other), abs=1e-6)


def test_image_stats_known_values():
    a = np.array([[0, 100], [200, 100]], np.uint8)
    s = M.image_stats(a)
    assert (s["height"], s["width"], s["channels"]) == (2, 2, 1)
    assert s["mean"] == 100.0 and s["std"] == pytest.approx(np.sqrt(5000))
    assert s["dynamic_range"] == 200 and s["michelson_contrast"] == 1.0
    assert s["rms_contrast"] == pytest.approx(np.sqrt(5000) / 255)


def test_image_stats_edge_cases(color):
    z = M.image_stats(np.zeros((3, 3), np.uint8))
    assert z["michelson_contrast"] == 0.0 and z["std"] == 0.0 and z["entropy_bits"] == 0.0
    c = M.image_stats(color)
    assert c["channels"] == 3 and set(c["channel_means"]) == {"R", "G", "B"}


def test_entropy_of_two_equal_levels_is_one_bit():
    assert M.entropy(np.array([[0, 255], [0, 255]], np.uint8)) == pytest.approx(1.0)
