"""Thin FastAPI adapter for the existing ChayaPictureLab processing modules."""
from __future__ import annotations

import base64
import json
import os
import time
import uuid
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from chayalab import __version__, colorspace as cs, histogram, metrics, noise, registry as R
from chayalab.history import ExperimentLog
from chayalab.io_utils import OUTPUT_FORMATS, encode_image, load_image
from chayalab.report import build_html_report
from chayalab.validation import ImageError

app = FastAPI(title="ChayaPictureLab API", version=__version__)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CHAYA_CORS_ORIGINS", "http://localhost:5173").split(","), allow_methods=["*"], allow_headers=["*"])
SESSIONS: dict[str, dict] = {}
SAMPLES = {"scene.png": "Scene", "shapes.png": "Shapes", "low_contrast.png": "Low contrast", "texture.png": "Texture"}


def session(sid: str):
    return SESSIONS.setdefault(sid, {"log": ExperimentLog(), "source": None, "name": "", "last_image": None, "report_images": {}})


def image_data(image: np.ndarray) -> str:
    return base64.b64encode(encode_image(image, "PNG")).decode("ascii")


def serialize_image(image: np.ndarray) -> dict:
    return {"data": image_data(image), "width": int(image.shape[1]), "height": int(image.shape[0]),
            "channels": 1 if image.ndim == 2 else int(image.shape[2])}


def execute(sid: str, key: str, image: np.ndarray, params: dict):
    started = time.perf_counter()
    result = R.run_operation(key, image, params)
    seconds = time.perf_counter() - started
    stats = metrics.image_stats(result["image"])
    session(sid)["log"].add(key, R.OPERATIONS[key].category, result["params"], seconds, image, result["image"],
                            {k: stats[k] for k in ("mean", "std", "rms_contrast")})
    session(sid)["last_image"] = (key, result["image"])
    session(sid)["report_images"][f"Result: {key}"] = result["image"]
    return {**result, "seconds": seconds, "stats": stats, "op": key}


@app.get("/api/health")
def health():
    return {"ok": True, "version": __version__}


@app.get("/api/operations")
def operations():
    return [{"key": o.key, "category": o.category, "purpose": o.purpose, "formula": o.formula,
             "impl": o.impl, "needs_gray": o.needs_gray,
             "params": [{"key": p.key, "label": p.label, "kind": p.kind, "default": p.default,
                         "min": p.min, "max": p.max, "step": p.step, "options": p.options, "help": p.help}
                        for p in o.params]} for o in R.OPERATIONS.values()]


@app.get("/api/samples")
def samples():
    return [{"name": n, "label": label} for n, label in SAMPLES.items()]


@app.post("/api/image")
async def upload_image(file: UploadFile = File(...), max_side: int = Form(1024), x_session_id: str = Header(default="")):
    try:
        img, info = load_image(await file.read(), max_side)
    except ImageError as exc:
        raise HTTPException(400, str(exc)) from exc
    sid = x_session_id or str(uuid.uuid4())
    state = session(sid); state["source"], state["name"], state["report_images"] = img, file.filename or "upload", {}
    return {"session_id": sid, "name": state["name"], "info": info, "image": serialize_image(img), "stats": metrics.image_stats(img)}


@app.post("/api/sample/{name}")
def load_sample(name: str, x_session_id: str = Header(default=""), max_side: int = 1024):
    if name not in SAMPLES:
        raise HTTPException(404, "Unknown sample")
    try:
        img, info = load_image((Path(__file__).parent / "samples" / name).read_bytes(), max_side)
    except (OSError, ImageError) as exc:
        raise HTTPException(500, f"Sample unavailable: {exc}") from exc
    sid = x_session_id or str(uuid.uuid4())
    state = session(sid); state["source"], state["name"], state["report_images"] = img, name, {}
    return {"session_id": sid, "name": name, "info": info, "image": serialize_image(img), "stats": metrics.image_stats(img)}


@app.post("/api/operation")
def operation(key: str = Form(...), params: str = Form("{}"), x_session_id: str = Header(default="")):
    state = session(x_session_id)
    if state["source"] is None:
        raise HTTPException(400, "Load an image first")
    try:
        result = execute(x_session_id, key, state["source"], json.loads(params))
    except (ImageError, KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    return {**{k: v for k, v in result.items() if k not in ("image", "extras")},
            "image": serialize_image(result["image"]), "extras": {k: serialize_image(v) for k, v in result["extras"].items()}}


@app.post("/api/compare")
def compare(operations: str = Form(...), x_session_id: str = Header(default="")):
    state = session(x_session_id)
    if state["source"] is None: raise HTTPException(400, "Load an image first")
    try:
        items = json.loads(operations)
        if not 2 <= len(items) <= 6: raise ValueError("Choose between 2 and 6 operations")
        results = []
        for item in items:
            result = execute(
                x_session_id,
                item["key"],
                state["source"],
                item.get("params", {}),
            )
            results.append({
                **{
                    k: v
                    for k, v in result.items()
                    if k not in ("image", "extras")
                },
                "image": serialize_image(result["image"]),
            })
        return results
    except (ImageError, KeyError, ValueError) as exc: raise HTTPException(400, str(exc)) from exc


@app.post("/api/noise")
def noise_experiment(kind: str = Form(...), level: float = Form(...), seed: int = Form(42), ksize: int = Form(3), methods: str = Form("[]"), grayscale: bool = Form(True), x_session_id: str = Header(default="")):
    state = session(x_session_id)
    if state["source"] is None: raise HTTPException(400, "Load an image first")
    clean = cs.to_grayscale(state["source"]) if grayscale else state["source"]
    noisy = noise.gaussian_noise(clean, level, seed=seed) if kind == "Gaussian" else noise.salt_pepper_noise(clean, level, seed=seed)
    out = {"Clean reference": serialize_image(clean), "Noisy": serialize_image(noisy), "restored": []}
    session(x_session_id)["report_images"].update({"Noise experiment: clean reference": clean, "Noise experiment: noisy": noisy})
    for method in json.loads(methods):
        params = {"ksize": ksize} if method != "Gaussian filter" else {"sigma": 1.2}
        result = execute(x_session_id, method, noisy, params)
        out["restored"].append({"name": method, "image": serialize_image(result["image"]), "mse": metrics.mse(clean, result["image"]), "psnr": metrics.psnr(clean, result["image"])})
        session(x_session_id)["report_images"][f"Noise experiment: {method}"] = result["image"]
    return out


@app.get("/api/analysis")
def analysis(x_session_id: str = Header(default="")):
    state = session(x_session_id)
    if state["source"] is None: raise HTTPException(400, "Load an image first")
    return {"stats": metrics.image_stats(state["source"]), "history": json.loads(state["log"].to_json()), "rows": state["log"].rows(), "histogram": histogram.compute_histogram(cs.to_grayscale(state["source"])).tolist()}


@app.get("/api/report-data")
def report_data(x_session_id: str = Header(default="")):
    """Provide actual experiment data to the Hyper Elements report service."""

    # Never create a new session when requesting a report.
    if not x_session_id or len(x_session_id) > 128:
        raise HTTPException(401, "A valid session ID is required")

    state = SESSIONS.get(x_session_id)

    if state is None:
        raise HTTPException(404, "Session not found or expired")

    source = state.get("source")
    last_image = state.get("last_image")
    records = state["log"].records

    if source is None:
        raise HTTPException(400, "Load an image before generating a report")

    if last_image is None or not records:
        raise HTTPException(400, "Run an image-processing operation first")

    operation_key, processed = last_image
    operation = R.OPERATIONS.get(operation_key)

    if operation is None:
        raise HTTPException(400, "Latest operation is unavailable")

    record = records[-1]

    source_info = serialize_image(source)
    processed_info = serialize_image(processed)
    output_stats = metrics.image_stats(processed)

    return {
        "reportId": str(uuid.uuid4()),
        "title": "Scientific Image Processing Report",
        "generatedAt": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        ),
        "sourceName": state.get("name") or "Uploaded image",
        "dataLabel": "LIVE EXPERIMENT DATA",

        "image": {
            "width": source_info["width"],
            "height": source_info["height"],
            "channels": source_info["channels"],
        },

        "operation": {
            "name": operation_key.replace("_", " ").replace("-", " ").title(),
            "category": operation.category,
            "purpose": operation.purpose,
            "formula": operation.formula,
            "parameters": dict(record.parameters),
        },

        "processingMs": float(record.seconds) * 1000.0,

        "statistics": {
            "mean": output_stats["mean"],
            "standardDeviation": output_stats["std"],
            "entropyBits": output_stats["entropy_bits"],
            "rmsContrast": output_stats["rms_contrast"],
        },

        "originalImage": {
            "src": "data:image/png;base64," + source_info["data"],
            "width": source_info["width"],
            "height": source_info["height"],
            "alt": "Original source image",
        },

        "processedImage": {
            "src": "data:image/png;base64," + processed_info["data"],
            "width": processed_info["width"],
            "height": processed_info["height"],
            "alt": "Processed result image",
        },
    }



@app.get("/api/history.json")
def history(x_session_id: str = Header(default="")):
    return Response(session(x_session_id)["log"].to_json(), media_type="application/json", headers={"Content-Disposition": "attachment; filename=chayapicturelab_history.json"})


@app.delete("/api/history")
def clear_history(x_session_id: str = Header(default="")):
    session(x_session_id)["log"].clear()
    return {"ok": True}


@app.get("/api/export/{fmt}")
def export_image(fmt: str, x_session_id: str = Header(default="")):
    state = session(x_session_id)
    if state["last_image"] is None:
        raise HTTPException(400, "Run an operation first")
    names = {"png": "PNG", "jpeg": "JPEG", "bmp": "BMP"}
    if fmt.lower() not in names:
        raise HTTPException(400, "Choose PNG, JPEG, or BMP")
    ext, mime = OUTPUT_FORMATS[names[fmt.lower()]]
    data = encode_image(state["last_image"][1], names[fmt.lower()])
    return Response(data, media_type=mime, headers={"Content-Disposition": f"attachment; filename=result.{ext}"})


@app.post("/api/report.html")
def report(notes: str = Form(""), x_session_id: str = Header(default="")):
    state = session(x_session_id)
    stats = metrics.image_stats(state["source"]) if state["source"] is not None else {}
    images = {state["name"]: state["source"]} if state["source"] is not None else {}
    images.update(state["report_images"])
    html = build_html_report("ChayaPictureLab experiment report", state["log"].records, images, stats, notes)
    return Response(html, media_type="text/html", headers={"Content-Disposition": "attachment; filename=chayapicturelab_report.html"})
