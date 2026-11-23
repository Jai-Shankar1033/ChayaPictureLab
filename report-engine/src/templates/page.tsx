import { Page } from "@hyper-elements/react";
import { chayaTheme } from "../theme.js";
import type { ExperimentReportData } from "../types.js";
import { ReportBody } from "./shared.js";

export function WebReport({ data }: { data: ExperimentReportData }) {
  return (
    <Page width={960} title={data.title} description={`ChayaLab report for ${data.operation.name}`} theme={chayaTheme} style={{ backgroundColor: "#F3F6FA", gap: 16 }}>
      <ReportBody data={data} includeImages />
    </Page>
  );
}
