import io
import json

import numpy as np
import pytest
from PIL import Image

from chayalab import registry as R
from chayalab.history import ExperimentLog, fingerprint
from chayalab.io_utils import encode_image, load_image, resize_to
from chayalab.report import build_html_report
from chayalab.validation import ImageError


def png_bytes(arr, mode=None):
    buf = io.BytesIO(); Image.fromarray(arr, mode).save(buf, "PNG"); return buf.getvalue()


def test_load_roundtrip_png_is_lossless(color):
    out, info = load_image(png_bytes(color))
    assert np.array_equal(out, color) and info["format"] == "PNG" and not info["resized"]


def test_load_gray_and_rgba_become_rgb(gray):
    out, _ = load_image(png_bytes(gray))
    assert out.shape == gray.shape + (3,) and np.array_equal(out[..., 0], gray)
    rgba = np.zeros((4, 4, 4), np.uint8)                    # fully transparent -> white background
    out, _ = load_image(png_bytes(rgba))
    assert (out == 255).all()


def test_large_images_are_shrunk_not_enlarged(color):
    big = np.zeros((300, 600, 3), np.uint8)
    out, info = load_image(png_bytes(big), max_side=100)
    assert max(out.shape[:2]) == 100 and info["resized"] and info["original_size"] == (600, 300)
    small, info = load_image(png_bytes(color), max_side=1000)
    assert small.shape == color.shape and not info["resized"]


@pytest.mark.parametrize("data", [b"", b"not an image", b"\x89PNG\r\n\x1a\n" + b"junk" * 10])
def test_unreadable_files_give_friendly_error(data):
    with pytest.raises(ImageError):
        load_image(data)


@pytest.mark.parametrize("fmt", ["PNG", "BMP"])
def test_encode_lossless_formats_roundtrip(fmt, color):
    assert np.array_equal(load_image(encode_image(color, fmt))[0], color)


def test_encode_jpeg_and_bad_format(color, gray):
    data = encode_image(color, "JPEG")
    assert data[:2] == b"\xff\xd8"
    assert load_image(encode_image(gray, "PNG"))[0].shape[2] == 3
    with pytest.raises(ImageError):
        encode_image(color, "GIF")


def test_resize_to(color):
    assert resize_to(color, (10, 12)).shape == (10, 12, 3)


def test_history_stores_metadata_not_images(gray):
    log = ExperimentLog(max_records=3)
    out = (255 - gray).astype(np.uint8)
    for i in range(5):
        log.add("Negative", "Point & colour", {"k": i}, 0.01, gray, out, {"mse": 1.5})
    assert len(log.records) == 3 and log.records[0].number == 3          # oldest dropped
    rec = log.records[-1]
    assert rec.input_info["id"] == fingerprint(gray)
    assert len(log.to_json()) < 5000            # metadata only: no pixel data is stored
    row = log.rows()[0]
    assert row["operation"] == "Negative" and "time" in row and "seconds" in row
    json.loads(log.to_json())
    log.clear(); assert log.records == []


def test_fingerprint_changes_with_content(gray):
    other = gray.copy(); other[0, 0] ^= 1
    assert fingerprint(gray) != fingerprint(other) and fingerprint(gray) == fingerprint(gray.copy())


def test_report_contains_parameters_and_escapes_html(gray):
    log = ExperimentLog()
    log.add("<script>x</script>", "c", {"sigma": 2.5}, 0.123, gray, gray, {"psnr": float("inf")})
    html = build_html_report("My <b>report</b>", log.records, {"Original": gray}, {"mean": 12.5}, "note <i>")
    assert "<script>x</script>" not in html and "&lt;script&gt;" in html
    assert "sigma" in html and "2.5" in html and "data:image/png;base64," in html and "inf" in html
    assert "no statistical significance" in html.lower()
    assert "No experiments were recorded" in build_html_report("t", [])


# ---------------------------------------------------------------- registry
def test_every_operation_runs_on_gray_and_colour_with_defaults(gray, color):
    for key, op in R.OPERATIONS.items():
        for img in (gray, color):
            if img.ndim == 2 and key in ("Extract channel (gray)", "Isolate channel (colour)", "Swap channels",
                                          "Adjust channel", "Eliminate channel", "HSV decomposition"):
                with pytest.raises(ImageError):
                    R.run_operation(key, img)
                continue
            r = R.run_operation(key, img)
            assert r["image"].dtype == np.uint8 and r["image"].ndim in (2, 3), key
            assert r["image"].shape[:2] == img.shape[:2], key


def test_registry_covers_every_category_and_documents_ops():
    assert {o.category for o in R.OPERATIONS.values()} == set(R.CATEGORIES)
    for k, o in R.OPERATIONS.items():
        assert o.purpose and o.formula, k


def test_registry_rejects_unknown_operation_and_params(gray):
    with pytest.raises(ImageError):
        R.run_operation("Nope", gray)
    with pytest.raises(ImageError):
        R.run_operation("Negative", gray, {"bogus": 1})


def test_registry_marks_gray_conversion(color):
    r = R.run_operation("Histogram equalization", color)
    assert r["image"].ndim == 2 and any("grayscale" in n for n in r["notes"])


def test_registry_is_reproducible_with_same_params(gray):
    a = R.run_operation("Gaussian filter", gray, {"sigma": 2.0})
    b = R.run_operation("Gaussian filter", gray, {"sigma": 2.0})
    assert np.array_equal(a["image"], b["image"]) and a["params"] == {"sigma": 2.0}


def test_registry_params_have_valid_defaults():
    for key, op in R.OPERATIONS.items():
        for p in op.params:
            if p.kind in ("int", "float"):
                assert p.min <= p.default <= p.max, (key, p.key)
            if p.kind == "choice":
                assert p.default in p.options, (key, p.key)
