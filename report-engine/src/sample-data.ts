import { Resvg } from "@resvg/resvg-js";
import type { ExperimentReportData, ReportImage } from "./types.js";

/**
 * Create a local PNG placeholder for the demo.
 * The report renderers can embed PNG data URIs in PDF, web and Canvas output.
 * These are illustrative graphics, not actual source or processed images.
 */
function pngDataUri(label: string, background: string, accent: string): ReportImage {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="720" height="420" viewBox="0 0 720 420">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop stop-color="${background}"/><stop offset="1" stop-color="#172033"/>
      </linearGradient>
      <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse">
        <path d="M36 0H0V36" fill="none" stroke="#FFFFFF" stroke-opacity=".07" stroke-width="1"/>
      </pattern>
    </defs>
    <rect width="720" height="420" rx="24" fill="url(#g)"/>
    <rect width="720" height="420" rx="24" fill="url(#grid)"/>
    <circle cx="360" cy="180" r="108" fill="none" stroke="${accent}" stroke-width="3" opacity=".85"/>
    <circle cx="360" cy="180" r="66" fill="none" stroke="${accent}" stroke-width="2" opacity=".52"/>
    <path d="M252 180h216M360 72v216M284 104l152 152M436 104 284 256" stroke="${accent}" stroke-width="2" opacity=".48"/>
    <circle cx="360" cy="180" r="10" fill="${accent}"/>
    <path d="M80 350h560" stroke="#FFFFFF" stroke-opacity=".3" stroke-width="2"/>
  </svg>`;

  const png = new Resvg(svg).render().asPng();
  return {
    src: `data:image/png;base64,${Buffer.from(png).toString("base64")}`,
    width: 720,
    height: 420,
    alt: `${label}, illustrative placeholder image; not an actual experiment image`,
  };
}

/** Synthetic demo content. Replace it with values returned by ChayaPictureLab's API. */
export function createSampleReport(): ExperimentReportData {
  return {
    reportId: "DEMO-EXP-0001",
    title: "Scientific Image Processing Report",
    generatedAt: new Date().toISOString(),
    sourceName: "sample-scene.png",
    image: { width: 1024, height: 768, channels: 3 },
    operation: {
      name: "Gaussian Blur",
      category: "Filtering",
      purpose: "Reduces high-frequency variation by smoothing local pixel neighborhoods.",
      formula: "G(x,y) = (1 / 2πσ²) · exp(−(x² + y²) / 2σ²)",
      parameters: { kernel_size: 5, sigma: 1.2 },
    },
    processingMs: 12.4,
    statistics: {
      mean: 128.4,
      standardDeviation: 42.1,
      entropyBits: 7.26,
      rmsContrast: 0.165,
    },
    // No MSE/PSNR is supplied for this single-operation example because no clean reference
    // comparison was made. The real app should include these only for valid reference tests.
    originalImage: pngDataUri("ORIGINAL", "#21636A", "#83D4CE"),
    processedImage: pngDataUri("PROCESSED", "#51447B", "#B8A8F0"),
    notes: "Demonstration report only. Replace this note and all sample values with measured experiment data before research or production use.",
    dataLabel: "ILLUSTRATIVE SAMPLE DATA — NOT A REAL EXPERIMENT",
  };
}
