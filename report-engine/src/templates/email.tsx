import { Email } from "@hyper-elements/react";
import { chayaTheme } from "../theme.js";
import type { ExperimentReportData } from "../types.js";
import { ReportBody } from "./shared.js";

export function EmailReport({ data }: { data: ExperimentReportData }) {
  return (
    <Email width={600} theme={chayaTheme} previewText={`${data.operation.name} experiment report`} style={{ backgroundColor: "#F3F6FA", gap: 12 }}>
      <ReportBody data={data} includeImages={false} />
    </Email>
  );
}
