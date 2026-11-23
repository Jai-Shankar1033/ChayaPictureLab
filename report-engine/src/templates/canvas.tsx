import { Canvas } from "@hyper-elements/react";
import { chayaTheme } from "../theme.js";
import type { ExperimentReportData } from "../types.js";
import { CanvasSummary } from "./shared.js";

export function ImageReport({ data }: { data: ExperimentReportData }) {
  return (
    <Canvas width={1200} height={760} title={`${data.operation.name} experiment summary`} theme={chayaTheme} style={{ backgroundColor: "#F3F6FA", padding: 10 }}>
      <CanvasSummary data={data} />
    </Canvas>
  );
}
