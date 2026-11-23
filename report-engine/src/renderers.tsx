import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import React from "react";

import {
  formatDiagnostics,
  outline,
  render,
  validate,
  type ValidateOptions,
} from "@hyper-elements/react";
import { emailClients } from "@hyper-elements/email-clients";
import { renderPdf } from "@hyper-elements/react/pdf";
import { renderImage } from "@hyper-elements/react/image";

import type { ExperimentReportData } from "./types.js";
import { EmailReport } from "./templates/email.js";
import { WebReport } from "./templates/page.js";
import { PdfReport } from "./templates/document.js";
import { ImageReport } from "./templates/canvas.js";

const FONT_DIR = new URL(
  "../node_modules/@fontsource/inter/files/",
  import.meta.url
);

async function loadFonts() {
  const regular = new Uint8Array(
    await readFile(new URL("inter-latin-400-normal.woff", FONT_DIR))
  );
  const bold = new Uint8Array(
    await readFile(new URL("inter-latin-700-normal.woff", FONT_DIR))
  );

  return [
    { family: "Inter", src: regular, weight: 400 as const },
    { family: "Inter", src: bold, weight: 700 as const },
  ];
}

function logValidation(
  label: string,
  element: React.ReactElement,
  options?: ValidateOptions
) {
  const result = validate(element, options);
  console.log(`\n[${label}] valid: ${result.valid}`);
  const diagnostics = formatDiagnostics(result.diagnostics);
  if (diagnostics) console.log(diagnostics);
  if (!result.valid) throw new Error(`${label} template validation failed`);
  console.log(outline(element));
  return result;
}

/** Generate illustrative local files. Never use this demo data as experiment results. */
export async function generateSampleOutputs(data: ExperimentReportData) {
  const outDir = resolve(process.cwd(), "output");
  await mkdir(outDir, { recursive: true });
  const fonts = await loadFonts();

  const emailElement = <EmailReport data={data} />;
  const pageElement = <WebReport data={data} />;
  const pdfElement = <PdfReport data={data} />;
  const imageElement = <ImageReport data={data} />;

  const emailPlugin = await emailClients();
  const emailOptions: ValidateOptions = { plugins: [emailPlugin] };

  const emailValidation = logValidation("Email", emailElement, emailOptions);
  logValidation("Web", pageElement);
  logValidation("PDF", pdfElement);
  logValidation("Image", imageElement);

  const [emailResult, pageResult, printResult, pdfResult, imageResult] =
    await Promise.all([
      render(emailElement, { pretty: true, plugins: [emailPlugin] }),
      render(pageElement, { pretty: true }),
      render(pdfElement, { pretty: true }),
      renderPdf(pdfElement, { fonts }),
      renderImage(imageElement, {
        fonts,
        format: "png",
        scale: 1,
        strict: true,
      }),
    ]);

  const diagnostics = [
    "EMAIL VALIDATION",
    formatDiagnostics(emailValidation.diagnostics),
    "EMAIL RENDER",
    formatDiagnostics(emailResult.diagnostics),
    "WEB",
    formatDiagnostics(pageResult.diagnostics),
    "PRINT",
    formatDiagnostics(printResult.diagnostics),
    "PDF",
    formatDiagnostics(pdfResult.diagnostics),
    "IMAGE",
    formatDiagnostics(imageResult.diagnostics),
  ].join("\n\n");

  await Promise.all([
    writeFile(resolve(outDir, "scientific-report-email.html"), emailResult.html, "utf8"),
    writeFile(resolve(outDir, "scientific-report-email.txt"), emailResult.text, "utf8"),
    writeFile(resolve(outDir, "scientific-report-web.html"), pageResult.html, "utf8"),
    writeFile(resolve(outDir, "scientific-report-print.html"), printResult.html, "utf8"),
    writeFile(resolve(outDir, "scientific-report.pdf"), pdfResult.pdf),
    writeFile(resolve(outDir, "scientific-report-summary.png"), imageResult.image),
    writeFile(resolve(outDir, "render-diagnostics.txt"), diagnostics, "utf8"),
  ]);

  console.log(`\nGenerated files in ${outDir}`);
  console.log(`PNG dimensions: ${imageResult.width} × ${imageResult.height}`);
  return { outDir, emailResult, pageResult, printResult, pdfResult, imageResult };
}

export type LiveReportFormat =
  | "html"
  | "print-html"
  | "pdf"
  | "png"
  | "email-html"
  | "email-text";

export type LiveReportOutput = {
  body: string | Uint8Array;
  contentType: string;
  extension: string;
  diagnostics: string;
};

function validateLiveTemplate(
  label: string,
  element: React.ReactElement,
  options?: ValidateOptions
): string {
  const result = validate(element, options);
  const diagnostics = formatDiagnostics(result.diagnostics);
  if (!result.valid) {
    throw new Error(`${label} template validation failed:\n${diagnostics}`);
  }
  return diagnostics;
}

function combineDiagnostics(...items: string[]): string {
  return items.filter(Boolean).join("\n\n");
}

/** Render one real session report in memory; no shared output filenames are used. */
export async function renderLiveReport(
  data: ExperimentReportData,
  format: LiveReportFormat
): Promise<LiveReportOutput> {
  if (format === "html") {
    const element = <WebReport data={data} />;
    const validation = validateLiveTemplate("Web", element);
    const result = await render(element, { pretty: true });
    return {
      body: result.html,
      contentType: "text/html; charset=utf-8",
      extension: "html",
      diagnostics: combineDiagnostics(validation, formatDiagnostics(result.diagnostics)),
    };
  }

  if (format === "print-html") {
    const element = <PdfReport data={data} />;
    const validation = validateLiveTemplate("Print", element);
    const result = await render(element, { pretty: true });
    return {
      body: result.html,
      contentType: "text/html; charset=utf-8",
      extension: "html",
      diagnostics: combineDiagnostics(validation, formatDiagnostics(result.diagnostics)),
    };
  }

  if (format === "pdf") {
    const element = <PdfReport data={data} />;
    const validation = validateLiveTemplate("PDF", element);
    const fonts = await loadFonts();
    const result = await renderPdf(element, { fonts });
    return {
      body: result.pdf,
      contentType: "application/pdf",
      extension: "pdf",
      diagnostics: combineDiagnostics(validation, formatDiagnostics(result.diagnostics)),
    };
  }

  if (format === "png") {
    const element = <ImageReport data={data} />;
    const validation = validateLiveTemplate("Image", element);
    const fonts = await loadFonts();
    const result = await renderImage(element, {
      fonts,
      format: "png",
      scale: 1,
      strict: true,
    });
    return {
      body: result.image,
      contentType: "image/png",
      extension: "png",
      diagnostics: combineDiagnostics(validation, formatDiagnostics(result.diagnostics)),
    };
  }

  if (format === "email-html" || format === "email-text") {
    const element = <EmailReport data={data} />;
    const emailPlugin = await emailClients();
    const options: ValidateOptions = { plugins: [emailPlugin] };
    const validation = validateLiveTemplate("Email", element, options);
    const result = await render(element, {
      pretty: true,
      plugins: [emailPlugin],
    });
    return {
      body: format === "email-html" ? result.html : result.text,
      contentType:
        format === "email-html"
          ? "text/html; charset=utf-8"
          : "text/plain; charset=utf-8",
      extension: format === "email-html" ? "html" : "txt",
      diagnostics: combineDiagnostics(validation, formatDiagnostics(result.diagnostics)),
    };
  }

  throw new Error("Unsupported report format");
}
