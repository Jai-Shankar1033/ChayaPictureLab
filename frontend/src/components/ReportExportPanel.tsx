import { useState } from "react";

type ReportFormat =
  | "html"
  | "print-html"
  | "pdf"
  | "png"
  | "email-html"
  | "email-text";

type ReportOption = {
  format: ReportFormat;
  label: string;
  description: string;
};

const REPORT_OPTIONS: ReportOption[] = [
  { format: "pdf", label: "PDF report", description: "Shareable scientific report" },
  { format: "html", label: "Web HTML", description: "Interactive browser-friendly layout" },
  { format: "print-html", label: "Print HTML", description: "Print-ready report layout" },
  { format: "png", label: "PNG summary", description: "Image summary card" },
  { format: "email-html", label: "Email HTML", description: "Email-compatible markup" },
  { format: "email-text", label: "Email text", description: "Plain-text email version" },
];

const EXTENSIONS: Record<ReportFormat, string> = {
  html: "html",
  "print-html": "html",
  pdf: "pdf",
  png: "png",
  "email-html": "html",
  "email-text": "txt",
};

export type ReportExportPanelProps = {
  /** The same session ID used by the ChayaPictureLab /api requests. */
  sessionId: string;
  disabled?: boolean;
  className?: string;
};

function getApiError(message: string, fallback: string): string {
  try {
    const parsed: unknown = JSON.parse(message);
    if (
      typeof parsed === "object" && parsed !== null &&
      "error" in parsed && typeof parsed.error === "string"
    ) return parsed.error;
  } catch {
    // The response was not JSON. Use the fallback message below.
  }
  return fallback;
}

export function ReportExportPanel({
  sessionId,
  disabled = false,
  className = "",
}: ReportExportPanelProps) {
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState<ReportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function downloadReport(format: ReportFormat) {
    if (!sessionId.trim()) {
      setError("Your analysis session is missing. Reload the workspace and try again.");
      return;
    }

    setBusy(format);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`/reports/${format}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-Id": sessionId,
        },
        body: JSON.stringify({ notes }),
      });

      if (!response.ok) {
        const responseText = await response.text();
        throw new Error(
          getApiError(responseText, `Report generation failed (${response.status})`)
        );
      }

      const blob = await response.blob();
      if (blob.size === 0) throw new Error("The report service returned an empty file.");

      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const filename = `chayapicturelab-${format}-${new Date().toISOString().replace(/[:.]/g, "-")}.${EXTENSIONS[format]}`;
      anchor.href = objectUrl;
      anchor.download = filename;
      anchor.style.display = "none";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 30_000);

      setSuccess(`${REPORT_OPTIONS.find((option) => option.format === format)?.label ?? "Report"} generated successfully.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to generate the report.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
      aria-busy={busy !== null}
    >
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-700">
          Hyper Elements · Report Studio
        </p>
        <h2 className="mt-1 text-lg font-semibold text-slate-900">
          Export scientific report
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Generate reports from this session's actual image, operation parameters and measured results.
        </p>
      </div>

      <label htmlFor="chaya-report-notes" className="mb-1 block text-sm font-medium text-slate-700">
        Notes and interpretation <span className="font-normal text-slate-400">(optional)</span>
      </label>
      <textarea
        id="chaya-report-notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value.slice(0, 4000))}
        maxLength={4000}
        rows={3}
        placeholder="Add observations, experiment conditions or interpretation..."
        disabled={disabled || busy !== null}
        className="mb-1 w-full resize-y rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-teal-600 focus:ring-2 focus:ring-teal-600/15 disabled:cursor-not-allowed disabled:opacity-60"
      />
      <p className="mb-4 text-right text-xs text-slate-400">{notes.length}/4000</p>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {REPORT_OPTIONS.map((option) => (
          <button
            key={option.format}
            type="button"
            onClick={() => void downloadReport(option.format)}
            disabled={disabled || busy !== null}
            className="group rounded-xl border border-slate-200 bg-white p-3 text-left transition hover:border-teal-500 hover:bg-teal-50/50 focus:outline-none focus:ring-2 focus:ring-teal-600/30 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-slate-800">{option.label}</span>
              <span className="text-xs text-teal-700" aria-hidden="true">
                {busy === option.format ? "Generating…" : "↓"}
              </span>
            </span>
            <span className="mt-1 block text-xs text-slate-500">{option.description}</span>
          </button>
        ))}
      </div>

      {disabled ? (
        <p className="mt-3 text-sm text-slate-500">Load an image and run an operation before generating a report.</p>
      ) : null}
      {error ? (
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
          {error}
        </p>
      ) : null}
      {success ? (
        <p className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" role="status">
          {success}
        </p>
      ) : null}
    </section>
  );
}
