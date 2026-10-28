import numpy as np
import pytest

from chayalab import edges as E
from chayalab import morphology as MO
from chayalab import reference as ref
from chayalab.validation import ImageError


@pytest.fixture
def step():
    a = np.zeros((10, 10), np.uint8); a[:, 5:] = 100
    return a


@pytest.mark.parametrize("op", ["sobel", "prewitt", "roberts"])
def test_vertical_step_gives_horizontal_gradient(op, step):
    g = E.gradients(step, op)
    assert np.abs(g["gx"]).max() > 0
    if op != "roberts":      # Roberts kernels are DIAGONAL derivatives, so Gy is non-zero for a vertical step
        assert np.abs(g["gy"]).max() == 0
        assert np.allclose(g["direction_deg"][g["magnitude"] > 0], 0)
    assert np.all(g["magnitude"][:, :3] == 0) and np.all(g["magnitude"][:, 7:] == 0)   # flat regions


def test_sobel_known_response(step):
    assert E.gradients(step, "sobel")["gx"][5, 4] == 400   # (1+2+1) * 100
    assert E.gradients(step, "prewitt")["gx"][5, 4] == 300  # (1+1+1) * 100


def test_gradient_direction_for_horizontal_edge():
    a = np.zeros((10, 10), np.uint8); a[5:, :] = 100        # brightness grows downward
    g = E.gradients(a, "sobel")
    assert np.allclose(g["direction_deg"][4, 5], 90)


def test_constant_image_has_no_edges():
    flat = np.full((8, 8), 33, np.uint8)
    for op in E.KERNELS:
        assert E.edge_map(flat, op).max() == 0
    assert E.canny(flat)["edges"].max() == 0


def test_edge_map_threshold_binarises(step):
    out = E.edge_map(step, "sobel", 0.5)
    assert set(np.unique(out)) <= {0, 255} and out.max() == 255


def test_sobel_matches_opencv_interior(gray):
    cv2 = pytest.importorskip("cv2")
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3, borderType=cv2.BORDER_REPLICATE)
    assert np.allclose(E.gradients(gray, "sobel")["gx"], gx)


def test_edge_invalid_inputs(gray, color):
    with pytest.raises(ImageError):
        E.gradients(gray, "nope")
    with pytest.raises(ImageError):
        E.gradients(color)
    with pytest.raises(ImageError):
        E.canny(gray, low=0.5, high=0.1)


def test_canny_finds_thin_edge_on_step(step):
    r = E.canny(step, 1.0, 0.1, 0.3)
    cols = np.where(r["edges"].any(axis=0))[0]
    assert len(cols) <= 3 and all(3 <= c <= 6 for c in cols)       # thin line near column 4-5


def test_canny_hysteresis_keeps_connected_weak_edges_only():
    a = np.zeros((40, 40), np.uint8)
    a[:, 20:] = 200
    a[:20, 20:] = 120                                    # upper half of the edge is weaker
    out = E.canny(a, 1.0, 0.2, 0.9)["edges"]
    assert out[30, 19:22].any() and out[5, 19:22].any()   # weak part kept because it touches the strong part


def test_canny_close_to_opencv_on_shapes():
    cv_c = ref.opencv_canny(np.zeros((8, 8), np.uint8), 50, 150)
    if cv_c is None:
        pytest.skip("OpenCV not installed")
    img = np.zeros((80, 80), np.uint8)
    img[20:60, 20:60] = 200
    ours = E.canny(img, 1.4, 0.1, 0.3)["edges"] > 0
    theirs = ref.opencv_canny(img, 40, 120) > 0
    # both should trace the square outline: compare with a 2-pixel tolerance
    from chayalab.morphology import dilate, structuring_element
    tol = dilate((theirs * 255).astype(np.uint8), structuring_element("rect", 5)) > 0
    assert ours.sum() > 100 and (ours & tol).sum() / ours.sum() > 0.95


# ------------------------------------------------------------------ morphology
def square(n=9, lo=3, hi=6):
    a = np.zeros((n, n), np.uint8); a[lo:hi, lo:hi] = 255
    return a


def test_structuring_elements():
    assert MO.structuring_element("rect", 3).all()
    cross = MO.structuring_element("cross", 3)
    assert cross.sum() == 5 and not cross[0, 0] and cross[1, 1]
    el = MO.structuring_element("ellipse", 5)
    assert el[2, 2] and not el[0, 0] and el.sum() == 21
    for bad in (("rect", 4), ("blob", 3), ("rect", 0)):
        with pytest.raises(ImageError):
            MO.structuring_element(*bad)


def test_erode_dilate_square():
    se = MO.structuring_element("rect", 3)
    s = square()                                           # 3x3 block
    assert (MO.erode(s, se) == 255).sum() == 1 and MO.erode(s, se)[4, 4] == 255
    assert (MO.dilate(s, se) == 255).sum() == 25
    assert set(np.unique(MO.dilate(s, se))) == {0, 255}


def test_erosion_does_not_eat_objects_at_the_border():
    a = np.full((5, 5), 255, np.uint8)
    assert np.array_equal(MO.erode(a, MO.structuring_element("rect", 3)), a)


def test_opening_removes_speck_closing_fills_hole():
    se = MO.structuring_element("rect", 3)
    a = square(15, 4, 11); a[1, 1] = 255                   # big block + single-pixel speck
    op = MO.opening(a, se)
    assert op[1, 1] == 0 and op[7, 7] == 255
    b = square(15, 4, 11); b[7, 7] = 0                     # hole inside
    assert MO.closing(b, se)[7, 7] == 255


def test_boundary_extraction():
    se = MO.structuring_element("rect", 3)
    s = square(11, 3, 8)                                   # 5x5 block
    internal = MO.boundary(s, se, "internal")
    assert (internal == 255).sum() == 16 and internal[5, 5] == 0
    external = MO.boundary(s, se, "external")
    assert (external == 255).sum() == 24 and external[5, 5] == 0
    grad = MO.boundary(s, se, "gradient")
    assert (grad == 255).sum() == 40
    assert internal.dtype == np.uint8


def test_idempotence_and_ordering(gray):
    se = MO.structuring_element("cross", 3)
    o = MO.opening(gray, se)
    assert np.array_equal(MO.opening(o, se), o)            # opening is idempotent
    assert np.all(MO.erode(gray, se) <= gray) and np.all(gray <= MO.dilate(gray, se))
    assert np.all(o <= gray) and np.all(gray <= MO.closing(gray, se))


def test_morphology_vs_opencv(gray):
    cv2 = pytest.importorskip("cv2")
    se = MO.structuring_element("rect", 3).astype(np.uint8)
    assert np.array_equal(MO.erode(gray, MO.structuring_element("rect", 3)),
                          cv2.erode(gray, se, borderType=cv2.BORDER_CONSTANT, borderValue=255))
    assert np.array_equal(MO.dilate(gray, MO.structuring_element("rect", 3)), cv2.dilate(gray, se))


def test_dilation_uses_reflected_se():
    # Dilation = union of the object translated by every SE offset. The SE has offsets (0,0) and (0,+1),
    # so the object must grow to the RIGHT. (Without reflecting the SE it would wrongly grow left.)
    se = np.zeros((3, 3), bool); se[1, 2] = True; se[1, 1] = True
    a = np.zeros((3, 5), np.uint8); a[1, 2] = 255
    out = MO.dilate(a, se)
    assert out[1, 2] == 255 and out[1, 3] == 255 and out[1, 1] == 0


def test_morphology_invalid_inputs(gray):
    with pytest.raises(ImageError):
        MO.erode(gray, np.zeros((3, 3), bool))
    with pytest.raises(ImageError):
        MO.erode(gray, np.ones((2, 2), bool))
    with pytest.raises(ImageError):
        MO.boundary(gray, MO.structuring_element(), "weird")
    with pytest.raises(ImageError):
        MO.erode(np.zeros((0, 3), np.uint8), MO.structuring_element())


def test_single_pixel_morphology():
    one = np.array([[255]], np.uint8)
    assert MO.erode(one, MO.structuring_element("rect", 3)).tolist() == [[255]]
    assert MO.dilate(one, MO.structuring_element("rect", 3)).tolist() == [[255]]
