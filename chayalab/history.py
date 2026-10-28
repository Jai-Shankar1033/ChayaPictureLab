"""Session experiment history: small metadata records only (no image copies)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime

import numpy as np


def fingerprint(img: np.ndarray) -> str:
    """Short SHA-1 of the pixel bytes + shape: identifies an image without storing it."""
    h = hashlib.sha1(np.ascontiguousarray(img).tobytes())
    h.update(str(img.shape).encode())
    return h.hexdigest()[:10]


def describe(img: np.ndarray) -> dict:
    return {"shape": list(img.shape), "dtype": str(img.dtype), "id": fingerprint(img)}


@dataclass
class ExperimentRecord:
    number: int
    operation: str
    category: str
    parameters: dict
    timestamp: str
    seconds: float
    input_info: dict
    output_info: dict
    measurements: dict = field(default_factory=dict)

    def as_row(self) -> dict:
        return {"#": self.number, "time": self.timestamp, "operation": self.operation,
                "parameters": json.dumps(self.parameters, sort_keys=True, default=str),
                "seconds": round(self.seconds, 4), "input": self.input_info["id"],
                "output": self.output_info["id"]}


class ExperimentLog:
    """In-memory list of ExperimentRecord with a hard cap (oldest dropped)."""

    def __init__(self, max_records: int = 200):
        self.max_records = max_records
        self.records: list[ExperimentRecord] = []
        self._counter = 0

    def add(self, operation, category, parameters, seconds, input_img, output_img, measurements=None):
        self._counter += 1
        rec = ExperimentRecord(self._counter, operation, category, dict(parameters),
                               datetime.now().strftime("%Y-%m-%d %H:%M:%S"), float(seconds),
                               describe(input_img), describe(output_img), dict(measurements or {}))
        self.records.append(rec)
        del self.records[:-self.max_records]
        return rec

    def clear(self):
        self.records.clear()

    def rows(self):
        return [r.as_row() for r in self.records]

    def to_json(self) -> str:
        return json.dumps([asdict(r) for r in self.records], indent=2, default=str)
