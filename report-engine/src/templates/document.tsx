import { Document } from "@hyper-elements/react";
import { chayaTheme } from "../theme.js";
import type { ExperimentReportData } from "../types.js";
import { ReportBody } from "./shared.js";

export function PdfReport({ data }: { data: ExperimentReportData }) {
  return (
    <Document size="A4" orientation="portrait" title={data.title} theme={chayaTheme} style={{ backgroundColor: "#FFFFFF", gap: 12 }}>
      <ReportBody data={data} includeImages />
    </Document>
  );
}
