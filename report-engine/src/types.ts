export type ReportImage = {
  /** Data URI for local/demo use, or a URL supplied by the application. */
  src: string;
  width: number;
  height: number;
  alt: string;
};

export type ExperimentReportData = {
  reportId: string;
  title: string;
  generatedAt: string;
  sourceName: string;
  image: { width: number; height: number; channels: number };
  operation: {
    name: string;
    category: string;
    purpose: string;
    formula?: string;
    parameters: Record<string, string | number | boolean>;
  };
  processingMs: number;
  statistics: {
    mean: number;
    standardDeviation: number;
    entropyBits: number;
    rmsContrast: number;
  };
  /** Only include MSE/PSNR when calculated against a valid reference image. */
  referenceQuality?: { mse?: number; psnrDb?: number };
  originalImage?: ReportImage;
  processedImage?: ReportImage;
  notes?: string;
  /** Clearly labels synthetic demonstration values. */
  dataLabel: string;
};
