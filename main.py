"""ChayaPictureLab - Digital Image Processing Laboratory (Streamlit front end).

Run with:   streamlit run main.py

This file only builds the interface. All image processing lives in the
``chayalab`` package (NumPy implementations) and is described in
``chayalab/registry.py``.
"""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import streamlit as st
from matplotlib.figure import Figure

from chayalab import __version__
from chayalab import colorspace as cs
from chayalab import filters, histogram, metrics, noise, reference
from chayalab import registry as R
from chayalab.history import ExperimentLog
from chayalab.io_utils import OUTPUT_FORMATS, SUPPORTED_EXTENSIONS, encode_image, load_image
from chayalab.report import build_html_report
from chayalab.validation import ImageError

APP_NAME = "ChayaPictureLab"
SAMPLES_DIR = Path(__file__).resolve().parent / "samples"
SAMPLES = {"Scene (colour)": "scene.png", "Shapes (binary-like, for morphology)": "shapes.png",
           "Low contrast (for histogram tools)": "low_contrast.png", "Texture (edges / filters)": "texture.png"}
SECTIONS = ["1. Image input", "2. Point & colour", "3. Histogram & enhancement", "4. Filtering & restoration",
            "5. Edge detection", "6. Morphology", "7. Algorithm comparison", "8. Analysis & reports"]

st.set_page_config(page_title=APP_NAME, page_icon="🖼️", layout="wide")
ss = st.session_state
ss.setdefault("src", None)          # RGB uint8 array (never modified)
ss.setdefault("src_name", "")
ss.setdefault("src_info", {})
ss.setdefault("result", None)       # last single-operation result
ss.setdefault("compare", [])        # last comparison run
ss.setdefault("noise_run", None)    # last noise & restoration experiment
ss.setdefault("log", ExperimentLog())
ss.setdefault("max_side", 1024)
ss.setdefault("last_upload", None)


# ------------------------------------------------------------------ helpers
def show(img: np.ndarray, caption: str = "") -> None:
    st.image(img, caption=caption, width="stretch", clamp=True)


def hist_figure(img: np.ndarray, title: str) -> Figure:
    fig = Figure(figsize=(5, 2.4))
    ax = fig.subplots()
    x = np.arange(256)
    if img.ndim == 2:
        ax.fill_between(x, histogram.compute_histogram(img), color="#14b8a6", alpha=0.85, linewidth=0)
    else:
        for c, col in enumerate(("#ef4444", "#22c55e", "#3b82f6")):
            ax.plot(x, np.bincount(img[:, :, c].ravel(), minlength=256), color=col, lw=1, label="RGB"[c])
        ax.legend(frameon=False, fontsize=7)
    ax.set_xlim(0, 255)
    ax.set_title(title, fontsize=9, loc="left")
    ax.set_xlabel("Intensity", fontsize=8)
    ax.set_ylabel("Pixels", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    return fig


def need_image() -> bool:
    if ss.src is None:
        st.info("Load an image first (section **1. Image input**).", icon="ℹ️")
        return False
    return True


def set_source(arr, name, info):
    ss.src, ss.src_name, ss.src_info = arr, name, info
    ss.result, ss.compare, ss.noise_run = None, [], None


def fmt_num(v) -> str:
    return "inf" if v == float("inf") else f"{v:.2f}"


def param_widgets(op: R.Operation, prefix: str) -> dict:
    """Build one Streamlit widget per registry parameter."""
    values = {}
    cols = st.columns(min(3, max(1, len(op.params))))
    for i, p in enumerate(op.params):
        key = f"{prefix}:{p.key}"
        with cols[i % len(cols)]:
            if p.kind == "int":
                values[p.key] = st.slider(p.label, int(p.min), int(p.max), int(p.default), int(p.step or 1), key=key, help=p.help or None)
            elif p.kind == "float":
                values[p.key] = st.slider(p.label, float(p.min), float(p.max), float(p.default), float(p.step or 0.1), key=key, help=p.help or None)
            elif p.kind == "choice":
                values[p.key] = st.selectbox(p.label, p.options, index=p.options.index(p.default), key=key, help=p.help or None)
            else:
                values[p.key] = st.checkbox(p.label, value=bool(p.default), key=key, help=p.help or None)
    return values


def execute(op_key: str, params: dict, image: np.ndarray, category: str) -> dict:
    """Run one operation, time it, and record it in the session history."""
    t0 = time.perf_counter()
    out = R.run_operation(op_key, image, params)
    seconds = time.perf_counter() - t0
    st_out = metrics.image_stats(out["image"])
    ss.log.add(op_key, category, out["params"], seconds, image, out["image"],
               {"mean": st_out["mean"], "std": st_out["std"]})
    return {**out, "op": op_key, "seconds": seconds, "category": category}


def download_button(img: np.ndarray, stem: str, key: str):
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    fmt = c1.selectbox("Download format", list(OUTPUT_FORMATS), key=f"fmt:{key}")
    ext, mime = OUTPUT_FORMATS[fmt]
    c2.download_button("⬇ Download result", encode_image(img, fmt), f"{stem}.{ext}", mime, key=f"dl:{key}")


def result_panel(op: R.Operation, section: str) -> None:
    res = ss.result
    left, right = st.columns(2)
    with left:
        st.markdown("**Original**")
        show(ss.src, f"{ss.src_name} · {ss.src.shape[1]}×{ss.src.shape[0]}")
    with right:
        st.markdown("**Processed**")
        if res is None or res["op"] != op.key or res["category"] != op.category:
            st.info("Choose settings and press **Apply**. The original is never modified.", icon="👈")
            return
        show(res["image"], f"{res['op']} · {res['image'].shape[1]}×{res['image'].shape[0]}")
        for n in res["notes"]:
            st.caption("ℹ️ " + n)
        s = metrics.image_stats(res["image"])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Time", f"{res['seconds'] * 1000:.1f} ms")
        m2.metric("Mean", f"{s['mean']:.1f}")
        m3.metric("Std dev", f"{s['std']:.1f}")
        m4.metric("RMS contrast", f"{s['rms_contrast']:.3f}")
        st.caption("Parameters used: " + (", ".join(f"{k}={v}" for k, v in res["params"].items()) or "none"))
        download_button(res["image"], f"{Path(ss.src_name).stem}_{op.key.lower().replace(' ', '_')}", f"{section}")
    if res["extras"]:
        with st.expander("Intermediate / extra images"):
            cols = st.columns(min(3, len(res["extras"])))
            for i, (name, img) in enumerate(res["extras"].items()):
                with cols[i % len(cols)]:
                    show(img, name)


def workbench(category: str, section: str, show_histograms: bool = False) -> R.Operation:
    op_key = st.selectbox("Operation", R.operations_in(category), key=f"{section}:op")
    op = R.OPERATIONS[op_key]
    st.caption(op.purpose)
    params = param_widgets(op, f"{section}:{op_key}")
    c1, c2, _ = st.columns([1, 1, 4])
    if c2.button("Reset result", key=f"{section}:reset"):
        ss.result = None
    if c1.button("Apply", type="primary", key=f"{section}:apply"):
        try:
            with st.spinner(f"Applying {op_key}…"):
                ss.result = execute(op_key, params, ss.src, category)
        except ImageError as exc:
            ss.result = None
            st.error(str(exc), icon="🚫")
        except Exception as exc:  # never show a raw traceback to the user
            ss.result = None
            st.error(f"{op_key} failed: {type(exc).__name__}: {exc}", icon="🚫")
    result_panel(op, section)
    if show_histograms:
        res = ss.result if (ss.result and ss.result["op"] == op_key) else None
        h1, h2 = st.columns(2)
        base = cs.to_grayscale(ss.src) if op.needs_gray else ss.src
        h1.pyplot(hist_figure(base, "Histogram - input" + (" (grayscale)" if op.needs_gray else "")))
        if res is not None:
            h2.pyplot(hist_figure(res["image"], f"Histogram - {op_key}"))
    with st.expander("Formula, concept and implementation", expanded=False):
        st.latex(op.formula)
        st.write(op.purpose)
        st.caption(f"Implementation: {op.impl}")
    return op


# ------------------------------------------------------------------ sections
def page_input():
    st.header("1. Image input")
    st.session_state.max_side = st.select_slider(
        "Largest side kept when loading (larger images are shrunk for speed)", [256, 512, 768, 1024, 1536, 2048],
        value=ss.max_side)
    up = st.file_uploader("Upload an image", type=SUPPORTED_EXTENSIONS, help="JPG, PNG, BMP or WebP")
    if up is not None and ss.last_upload != (up.name, up.size, ss.max_side):
        try:
            arr, info = load_image(up.getvalue(), ss.max_side)
            set_source(arr, up.name, info)
            ss.last_upload = (up.name, up.size, ss.max_side)
        except ImageError as exc:
            st.error(str(exc), icon="🚫")
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
    pick = c1.selectbox("…or use a bundled sample (synthetic, generated by tools/make_samples.py)", list(SAMPLES))
    if c2.button("Load sample", width="stretch"):
        arr, info = load_image((SAMPLES_DIR / SAMPLES[pick]).read_bytes(), ss.max_side)
        set_source(arr, SAMPLES[pick], info)
        ss.last_upload = None
    if ss.src is not None:
        s = metrics.image_stats(ss.src)
        info = ss.src_info
        st.success(f"Loaded **{ss.src_name}** ({info.get('format', '?')}) – {s['width']}×{s['height']} px, {s['channels']} channels"
                   + (f"; shrunk from {info['original_size'][0]}×{info['original_size'][1]}" if info.get("resized") else ""))
        show(ss.src)
        st.caption("Images are stored internally as RGB. Greyscale files are expanded to three equal channels.")
        if st.button("Clear image and results"):
            ss.src, ss.result, ss.compare, ss.noise_run = None, None, [], None
            st.rerun()


def page_point_color():
    st.header("2. Point & colour operations")
    if need_image():
        workbench("Point & colour", "pc")


def page_histogram():
    st.header("3. Histogram & enhancement")
    if not need_image():
        return
    op = workbench("Histogram & enhancement", "hist", show_histograms=True)
    with st.expander("Validate against OpenCV (reference check)"):
        st.write("Runs our manual equalization and Otsu on the grayscale image and compares them with OpenCV "
                 "(used here only as a trusted reference).")
        if st.button("Run validation", key="hist:validate"):
            g = cs.to_grayscale(ss.src)
            ref_eq = reference.opencv_equalize(g)
            if ref_eq is None:
                st.warning("OpenCV is not installed, so the reference check is unavailable.")
            else:
                d = int(np.abs(ref_eq.astype(int) - histogram.equalize(g).astype(int)).max())
                st.write(f"Equalization: maximum per-pixel difference from `cv2.equalizeHist` = **{d}** grey level(s).")
                st.write(f"Otsu threshold: ours = **{histogram.otsu_threshold(g)}**, OpenCV = **{reference.opencv_otsu_threshold(g)}**.")
    if op.key == "Histogram equalization" and ss.result and ss.result["op"] == op.key:
        g = cs.to_grayscale(ss.src)
        with st.expander("CDF and mapping used by equalization"):
            fig = Figure(figsize=(5, 2.6)); ax = fig.subplots()
            ax.plot(histogram.cumulative_distribution(g), label="CDF"); ax.plot(histogram.equalization_mapping(g) / 255, label="mapping s_k / 255")
            ax.legend(fontsize=7); ax.set_xlabel("Input level k", fontsize=8); fig.tight_layout()
            st.pyplot(fig)
            st.caption("Very narrow histograms get a steep mapping (noise is amplified); a constant image has no valid mapping, so it is returned unchanged.")


def noise_experiment():
    st.subheader("Noise & restoration experiment")
    st.caption("The image you loaded acts as the **clean reference**. MSE/PSNR are only meaningful because the noisy "
               "and restored images are derived from that same reference.")
    c1, c2, c3 = st.columns(3)
    kind = c1.selectbox("Noise type", ["Gaussian", "Salt & pepper"], key="nx:kind")
    if kind == "Gaussian":
        level = c2.slider("Sigma (std. deviation)", 1.0, 100.0, 25.0, 1.0, key="nx:sigma")
    else:
        level = c2.slider("Density (fraction of pixels)", 0.01, 0.5, 0.05, 0.01, key="nx:density")
    seed = int(c3.number_input("Random seed", 0, 10_000_000, 42, key="nx:seed", help="Same seed -> same noise"))
    methods = st.multiselect("Restoration filters", ["Mean filter", "Gaussian filter", "Median filter", "Mode filter", "Outlier filter"],
                             default=["Mean filter", "Median filter", "Gaussian filter"], key="nx:methods")
    k = st.select_slider("Window size for mean / median / mode / outlier", [3, 5, 7], value=3, key="nx:k")
    sigma = st.slider("Sigma for the Gaussian filter", 0.3, 5.0, 1.2, 0.1, key="nx:gs")
    use_gray = st.checkbox("Work on grayscale (faster, recommended for the mode filter)", True, key="nx:gray")
    if st.button("Run experiment", type="primary", key="nx:run"):
        clean = cs.to_grayscale(ss.src) if use_gray else ss.src
        noisy = (noise.gaussian_noise(clean, level, seed=seed) if kind == "Gaussian"
                 else noise.salt_pepper_noise(clean, level, seed=seed))
        rows = [{"Image": "Noisy input", "MSE": metrics.mse(clean, noisy), "PSNR (dB)": metrics.psnr(clean, noisy), "Time (ms)": None}]
        imgs = {"Clean reference": clean, "Noisy input": noisy}
        fns = {"Mean filter": lambda x: filters.mean_filter(x, k), "Gaussian filter": lambda x: filters.gaussian_filter(x, sigma),
               "Median filter": lambda x: filters.median_filter(x, k), "Mode filter": lambda x: filters.mode_filter(x, k),
               "Outlier filter": lambda x: filters.outlier_filter(x, 30.0, k)}
        try:
            with st.spinner("Restoring…"):
                for m in methods:
                    t0 = time.perf_counter()
                    out = fns[m](noisy)
                    sec = time.perf_counter() - t0
                    mse_v, psnr_v = metrics.mse(clean, out), metrics.psnr(clean, out)
                    rows.append({"Image": m, "MSE": mse_v, "PSNR (dB)": psnr_v, "Time (ms)": sec * 1000})
                    imgs[m] = out
                    ss.log.add(f"Restore: {m}", "Noise experiment",
                               {"noise": kind, "level": level, "seed": seed, "k": k, "sigma": sigma}, sec, noisy, out,
                               {"mse": mse_v, "psnr": psnr_v})
            ss.noise_run = {"rows": rows, "images": imgs, "noise": kind, "level": level, "seed": seed}
        except ImageError as exc:
            st.error(str(exc), icon="🚫")
    run = ss.noise_run
    if run:
        st.write(f"**Results** – {run['noise']} noise, level {run['level']}, seed {run['seed']}")
        st.dataframe([{k_: ("–" if v is None else fmt_num(v) if isinstance(v, float) else v) for k_, v in r.items()} for r in run["rows"]], hide_index=True)
        cols = st.columns(3)
        for i, (name, img) in enumerate(run["images"].items()):
            with cols[i % 3]:
                show(img, name)
    with st.expander("What do MSE and PSNR mean?"):
        st.markdown("""
* **MSE** = mean of (reference − test)² over all pixels. 0 means identical; larger is worse.
* **PSNR** = 10·log10(255² / MSE) in decibels. Larger is better. Identical images give MSE = 0, so PSNR is **infinite**.
* Both compare *pixel values* only; they do not measure how good an image looks. They are only valid when the reference
  and the test image show the same scene at the same size (that is why mismatched shapes raise an error).""")


def page_filtering():
    st.header("4. Filtering & restoration")
    if not need_image():
        return
    tab1, tab2 = st.tabs(["Filters", "Noise & restoration experiment"])
    with tab1:
        workbench("Filtering", "flt")
    with tab2:
        noise_experiment()


def page_edges():
    st.header("5. Edge detection")
    if need_image():
        workbench("Edge detection", "edge")
        st.caption("Sobel, Prewitt, Roberts and all stages of Canny are implemented manually with NumPy. "
                   "OpenCV is only used in the automated tests as a reference.")


def page_morphology():
    st.header("6. Morphology")
    if need_image():
        st.caption("Tip: load the *Shapes* sample, or tick *Binarise first* to work on black-and-white objects.")
        workbench("Morphology", "morph")


def page_compare():
    st.header("7. Algorithm comparison")
    if not need_image():
        return
    keys = st.multiselect("Choose 2-6 operations to run on the same input image", list(R.OPERATIONS), max_selections=6,
                          default=["Mean filter", "Median filter", "Gaussian filter"], key="cmp:ops")
    chosen = {}
    for k in keys:
        with st.expander(f"Parameters – {k}", expanded=False):
            chosen[k] = param_widgets(R.OPERATIONS[k], f"cmp:{k}")
    if st.button("Run comparison", type="primary", disabled=len(keys) < 2, key="cmp:run"):
        out, errors = [], []
        for k in keys:
            try:
                out.append(execute(k, chosen[k], ss.src, "Comparison"))
            except ImageError as exc:
                errors.append(f"{k}: {exc}")
        ss.compare = out
        for e in errors:
            st.error(e, icon="🚫")
    if len(keys) < 2:
        st.info("Select at least two operations.")
    if ss.compare:
        cols = st.columns(min(3, len(ss.compare) + 1))
        with cols[0]:
            show(ss.src, "Original")
        for i, r in enumerate(ss.compare, start=1):
            with cols[i % len(cols)]:
                show(r["image"], r["op"])
                st.caption(", ".join(f"{k}={v}" for k, v in r["params"].items()) + f" · {r['seconds'] * 1000:.1f} ms")
        st.dataframe([{"Operation": r["op"], "Parameters": str(r["params"]), "Time (ms)": round(r["seconds"] * 1000, 2),
                       "Mean": round(metrics.image_stats(r["image"])["mean"], 2),
                       "Std dev": round(metrics.image_stats(r["image"])["std"], 2)} for r in ss.compare], hide_index=True)
        st.caption("Outputs are compared visually and by simple statistics only: there is no 'correct' answer image here, "
                   "so no quality score is computed. Use the noise experiment for MSE/PSNR with a known reference.")


def page_analysis():
    st.header("8. Analysis & reports")
    if not need_image():
        return
    stats = metrics.image_stats(ss.src)
    st.subheader("Image analysis dashboard")
    c = st.columns(5)
    c[0].metric("Size", f"{stats['width']}×{stats['height']}")
    c[1].metric("Channels", stats["channels"])
    c[2].metric("Mean", f"{stats['mean']:.1f}")
    c[3].metric("Std dev", f"{stats['std']:.1f}")
    c[4].metric("Entropy (bits)", f"{stats['entropy_bits']:.2f}")
    c = st.columns(4)
    c[0].metric("RMS contrast", f"{stats['rms_contrast']:.3f}")
    c[1].metric("Michelson contrast", f"{stats['michelson_contrast']:.3f}")
    c[2].metric("Min / max", f"{stats['min']:.0f} / {stats['max']:.0f}")
    c[3].metric("Last op. time", f"{ss.log.records[-1].seconds * 1000:.1f} ms" if ss.log.records else "–")
    st.pyplot(hist_figure(ss.src, "Histogram of the loaded image"))
    with st.expander("Definitions of the measurements"):
        st.markdown("""
* **Mean** = average of all samples; **Std dev** = √(mean of (value − mean)²), population form.
* **RMS contrast** = std / 255.  **Michelson contrast** = (max − min)/(max + min) (0 when max + min = 0).
* **Entropy** = −Σ p·log₂ p over the grey-level histogram (colour images are averaged to grey first).""")
    st.subheader("Experiment history (this session)")
    if ss.log.records:
        st.dataframe(ss.log.rows(), hide_index=True)
        if st.button("Clear history"):
            ss.log.clear()
            st.rerun()
    else:
        st.caption("No experiments yet. Apply an operation in sections 2-7.")
    st.subheader("Export report")
    notes = st.text_area("Notes to include (optional)", key="rep:notes")
    images = {f"Original ({ss.src_name})": ss.src}
    if ss.result:
        images[f"Result: {ss.result['op']}"] = ss.result["image"]
    for r in ss.compare:
        images[f"Comparison: {r['op']}"] = r["image"]
    if ss.noise_run:
        images.update({f"Noise experiment: {k}": v for k, v in ss.noise_run["images"].items()})
    flat = {f"original_{k}": v for k, v in stats.items() if not isinstance(v, dict)}
    html = build_html_report(f"{APP_NAME} experiment report", ss.log.records, images, flat, notes)
    d1, d2 = st.columns(2)
    d1.download_button("⬇ Download HTML report", html, "chayapicturelab_report.html", "text/html")
    d2.download_button("⬇ Download history (JSON)", ss.log.to_json(), "chayapicturelab_history.json", "application/json")


PAGES = [page_input, page_point_color, page_histogram, page_filtering, page_edges, page_morphology, page_compare, page_analysis]

with st.sidebar:
    st.title("🖼️ " + APP_NAME)
    st.caption(f"Digital Image Processing Laboratory · v{__version__}")
    section = st.radio("Section", SECTIONS, key="nav")
    if ss.src is not None:
        st.success(f"{ss.src_name}\n\n{ss.src.shape[1]}×{ss.src.shape[0]} px")
    else:
        st.warning("No image loaded")

PAGES[SECTIONS.index(section)]()
