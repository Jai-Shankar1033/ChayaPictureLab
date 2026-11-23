import express, { type ErrorRequestHandler } from "express";
import type { ExperimentReportData } from "./types.js";
import {
  renderLiveReport,
  type LiveReportFormat,
} from "./renderers.js";

const PORT = Number.parseInt(process.env.PORT ?? "4100", 10);
const HOST = process.env.HOST ?? "127.0.0.1";
const API_BASE_URL = (process.env.CHAYA_API_BASE_URL ?? "http://127.0.0.1:8000")
  .trim()
  .replace(/\/+$/, "");
const MAX_ACTIVE_RENDERS = Math.max(
  1,
  Math.min(4, Number.parseInt(process.env.MAX_ACTIVE_REPORTS ?? "2", 10) || 2)
);
const MAX_IMAGE_DATA_URI_CHARS = 20 * 1024 * 1024;
const ALLOWED_FORMATS = new Set<LiveReportFormat>([
  "html",
  "print-html",
  "pdf",
  "png",
  "email-html",
  "email-text",
]);

const app = express();
let activeRenders = 0;

app.disable("x-powered-by");
app.use((req, res, next) => {
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Referrer-Policy", "no-referrer");
  res.setHeader("Cache-Control", "no-store, private");
  next();
});
app.use(express.json({ limit: "8kb", strict: true }));

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function isValidSessionId(value: string): boolean {
  return value.length >= 8 && value.length <= 128 && /^[A-Za-z0-9._:-]+$/.test(value);
}

function validateReportData(value: unknown): asserts value is ExperimentReportData {
  if (!isPlainObject(value)) throw new Error("Backend returned an invalid report payload");
  const data = value;
  const operation = data.operation;
  const image = data.image;
  const stats = data.statistics;

  if (
    typeof data.reportId !== "string" || data.reportId.length > 80 ||
    typeof data.title !== "string" || data.title.length > 180 ||
    typeof data.generatedAt !== "string" ||
    typeof data.sourceName !== "string" || data.sourceName.length > 240 ||
    typeof data.dataLabel !== "string" || data.dataLabel.length > 100 ||
    !isPlainObject(operation) || !isPlainObject(image) || !isPlainObject(stats)
  ) {
    throw new Error("Backend returned an incomplete report payload");
  }

  if (
    typeof operation.name !== "string" ||
    typeof operation.category !== "string" ||
    typeof operation.purpose !== "string" ||
    !isPlainObject(operation.parameters) ||
    Object.keys(operation.parameters).length > 60 ||
    !isFiniteNumber(data.processingMs) || data.processingMs < 0 ||
    !isFiniteNumber(image.width) || !isFiniteNumber(image.height) ||
    !isFiniteNumber(image.channels) ||
    !isFiniteNumber(stats.mean) ||
    !isFiniteNumber(stats.standardDeviation) ||
    !isFiniteNumber(stats.entropyBits) ||
    !isFiniteNumber(stats.rmsContrast)
  ) {
    throw new Error("Backend returned invalid experiment measurements");
  }

  const checkImage = (candidate: unknown, label: string) => {
    if (!isPlainObject(candidate)) throw new Error(`${label} image is missing`);
    if (
      typeof candidate.src !== "string" ||
      candidate.src.length > MAX_IMAGE_DATA_URI_CHARS ||
      !/^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(candidate.src) ||
      !isFiniteNumber(candidate.width) || candidate.width < 1 || candidate.width > 8192 ||
      !isFiniteNumber(candidate.height) || candidate.height < 1 || candidate.height > 8192 ||
      typeof candidate.alt !== "string"
    ) {
      throw new Error(`${label} image data is invalid or too large`);
    }
  };

  checkImage(data.originalImage, "Original");
  checkImage(data.processedImage, "Processed");
}

function errorMessage(value: unknown): string {
  if (isPlainObject(value) && typeof value.detail === "string") {
    return value.detail.slice(0, 500);
  }
  if (isPlainObject(value) && typeof value.error === "string") {
    return value.error.slice(0, 500);
  }
  return "The image-processing backend could not provide report data";
}

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "chayalab-report-engine", activeRenders });
});

app.post("/reports/:format", async (req, res) => {
  const sessionId = req.get("X-Session-Id")?.trim() ?? "";
  if (!isValidSessionId(sessionId)) {
    res.status(401).json({ error: "A valid X-Session-Id header is required" });
    return;
  }

  const requestedFormat = String(req.params.format) as LiveReportFormat;
  if (!ALLOWED_FORMATS.has(requestedFormat)) {
    res.status(400).json({ error: "Unsupported report format" });
    return;
  }

  if (activeRenders >= MAX_ACTIVE_RENDERS) {
    res.status(429).json({ error: "The report service is busy. Try again shortly." });
    return;
  }

  const notesValue = isPlainObject(req.body) ? req.body.notes : undefined;
  if (notesValue !== undefined && typeof notesValue !== "string") {
    res.status(400).json({ error: "Report notes must be text" });
    return;
  }
  const notes = typeof notesValue === "string" ? notesValue.trim() : "";
  if (notes.length > 4000) {
    res.status(413).json({ error: "Report notes must be 4,000 characters or fewer" });
    return;
  }

  activeRenders += 1;
  try {
    const backendResponse = await fetch(`${API_BASE_URL}/api/report-data`, {
      method: "GET",
      headers: { "X-Session-Id": sessionId, Accept: "application/json" },
      signal: AbortSignal.timeout(45_000),
    });

    if (!backendResponse.ok) {
      let payload: unknown;
      try {
        payload = await backendResponse.json();
      } catch {
        payload = null;
      }
      const status = [400, 401, 404, 409, 413, 429].includes(backendResponse.status)
        ? backendResponse.status
        : 502;
      res.status(status).json({ error: errorMessage(payload) });
      return;
    }

    const payload: unknown = await backendResponse.json();
    validateReportData(payload);
    const reportData: ExperimentReportData = {
      ...payload,
      notes: notes || payload.notes,
    };

    const output = await renderLiveReport(reportData, requestedFormat);
    const filename = `chayapicturelab-${requestedFormat}-${Date.now()}.${output.extension}`;
    const body = typeof output.body === "string"
      ? Buffer.from(output.body, "utf8")
      : Buffer.from(output.body);

    res.status(200);
    res.setHeader("Content-Type", output.contentType);
    res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
    res.setHeader("Content-Length", String(body.byteLength));
    res.setHeader("X-Report-Format", requestedFormat);
    res.end(body);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown report error";
    console.error(`[report-service] ${requestedFormat} render failed: ${message}`);
    if (!res.headersSent) {
      const isBackendConnectionError =
        error instanceof TypeError ||
        (error instanceof Error && error.name === "TimeoutError");
      res.status(isBackendConnectionError ? 502 : 500).json({
        error: isBackendConnectionError
          ? "Cannot reach the ChayaPictureLab API. Check that FastAPI is running."
          : "Report generation failed. Check the report service console for details.",
      });
    }
  } finally {
    activeRenders = Math.max(0, activeRenders - 1);
  }
});

const errorHandler: ErrorRequestHandler = (error, _req, res, _next) => {
  const status = typeof error?.status === "number" ? error.status : 400;
  res.status(status).json({ error: status === 413 ? "Request is too large" : "Invalid report request" });
};
app.use(errorHandler);

if (!Number.isFinite(PORT) || PORT < 1 || PORT > 65535) {
  throw new Error("PORT must be a valid TCP port");
}

app.listen(PORT, HOST, () => {
  console.log(`[report-service] listening on ${HOST}:${PORT}`);
  console.log(`[report-service] FastAPI upstream: ${API_BASE_URL}`);
});
