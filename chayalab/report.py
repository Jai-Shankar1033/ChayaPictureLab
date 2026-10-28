"""Experiment report export (self-contained HTML + JSON). Reports only list what was
measured in this session; they make no claims about scientific significance."""
from __future__ import annotations

import base64
import html
import io
import json
from datetime import datetime

import numpy as np
from PIL import Image

from . import __version__


def _png_data_uri(img: np.ndarray, max_side: int = 480) -> str:
    im = Image.fromarray(img)
    if max(im.size) > max_side:
        s = max_side / max(im.size)
        im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _fmt(v):
    if isinstance(v, float):
        return "inf" if v == float("inf") else f"{v:.4f}"
    return str(v)


def build_html_report(title: str, records: list, images: dict[str, np.ndarray] | None = None,
                      stats: dict | None = None, notes: str = "") -> str:
    e = html.escape
    out = [f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{e(title)}</title>",
           "<style>body{font-family:Arial,sans-serif;max-width:960px;margin:2em auto;color:#222}"
           "table{border-collapse:collapse;width:100%;margin:1em 0}td,th{border:1px solid #bbb;"
           "padding:4px 8px;font-size:13px;text-align:left}th{background:#eee}"
           "img{max-width:46%;margin:4px;border:1px solid #ccc}code{background:#f4f4f4}</style></head><body>",
           f"<h1>{e(title)}</h1>",
           f"<p>Generated {datetime.now():%Y-%m-%d %H:%M:%S} by ChayaPictureLab {__version__}. "
           "All numbers below were computed in this session from the images shown; no "
           "statistical significance is implied.</p>"]
    if notes.strip():
        out.append(f"<h2>Notes</h2><p>{e(notes)}</p>")
    if images:
        out.append("<h2>Images</h2>")
        for name, img in images.items():
            out.append(f"<figure style='display:inline-block;margin:0'><img src='{_png_data_uri(img)}' "
                       f"alt='{e(name)}'><figcaption>{e(name)}</figcaption></figure>")
    if stats:
        out.append("<h2>Measurements</h2><table><tr><th>Measure</th><th>Value</th></tr>")
        for k, v in stats.items():
            out.append(f"<tr><td>{e(str(k))}</td><td>{e(_fmt(v))}</td></tr>")
        out.append("</table>")
    out.append("<h2>Experiment log</h2>")
    if not records:
        out.append("<p>No experiments were recorded.</p>")
    else:
        out.append("<table><tr><th>#</th><th>Time</th><th>Operation</th><th>Parameters</th>"
                   "<th>Seconds</th><th>Input id</th><th>Output id</th><th>Measurements</th></tr>")
        for r in records:
            meas = ", ".join(f"{k}={_fmt(v)}" for k, v in r.measurements.items())
            out.append(f"<tr><td>{r.number}</td><td>{e(r.timestamp)}</td><td>{e(r.operation)}</td>"
                       f"<td><code>{e(json.dumps(r.parameters, sort_keys=True, default=str))}</code></td>"
                       f"<td>{r.seconds:.4f}</td><td>{e(r.input_info['id'])}</td>"
                       f"<td>{e(r.output_info['id'])}</td><td>{e(meas)}</td></tr>")
        out.append("</table>")
    out.append("</body></html>")
    return "".join(out)
