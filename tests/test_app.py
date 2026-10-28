"""UI smoke tests using Streamlit's AppTest (runs main.py headlessly, no browser)."""
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

MAIN = str(Path(__file__).resolve().parents[1] / "main.py")
SECTIONS = ["1. Image input", "2. Point & colour", "3. Histogram & enhancement", "4. Filtering & restoration",
            "5. Edge detection", "6. Morphology", "7. Algorithm comparison", "8. Analysis & reports"]


def fresh():
    at = AppTest.from_file(MAIN, default_timeout=60)
    at.run()
    assert not at.exception
    return at


def load_sample(at, label="Scene (colour)"):
    at.selectbox[0].select(label) if label in at.selectbox[0].options else None
    next(b for b in at.button if b.label == "Load sample").click().run()
    assert not at.exception
    return at


def goto(at, section):
    at.sidebar.radio[0].set_value(section).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_app_starts_without_image_and_every_section_guides_user():
    at = fresh()
    for s in SECTIONS[1:]:
        goto(at, s)
        assert any("Load an image first" in i.value for i in at.info), s


def test_load_sample_and_apply_default_operation_on_each_workbench_page():
    at = load_sample(fresh())
    assert any("Loaded" in s.value for s in at.success)
    for s in ["2. Point & colour", "3. Histogram & enhancement", "5. Edge detection", "6. Morphology"]:
        goto(at, s)
        next(b for b in at.button if b.label == "Apply").click().run()
        assert not at.exception and not at.error, (s, [e.value for e in at.error])
        assert any(m.label == "Time" for m in at.metric), s


def test_filter_page_apply_and_noise_experiment_runs():
    at = load_sample(fresh())
    goto(at, "4. Filtering & restoration")
    next(b for b in at.button if b.label == "Apply").click().run()
    assert not at.exception and not at.error
    next(b for b in at.button if b.label == "Run experiment").click().run()
    assert not at.exception and not at.error
    assert at.dataframe, "expected a MSE/PSNR table"


def test_comparison_and_report_flow():
    at = load_sample(fresh())
    goto(at, "7. Algorithm comparison")
    next(b for b in at.button if b.label == "Run comparison").click().run()
    assert not at.exception and not at.error
    assert len(at.session_state["compare"]) == 3
    goto(at, "8. Analysis & reports")
    assert any(m.label == "Entropy (bits)" for m in at.metric)
    assert len(at.session_state["log"].records) >= 3


def test_invalid_state_is_reported_not_crashed():
    at = load_sample(fresh())
    goto(at, "7. Algorithm comparison")
    at.multiselect[0].set_value(["Mean filter"]).run()
    assert not at.exception
    assert next(b for b in at.button if b.label == "Run comparison").disabled
