import { createSampleReport } from "./sample-data.js";
import { generateSampleOutputs } from "./renderers.js";

try {
  const report = createSampleReport();
  await generateSampleOutputs(report);
} catch (error) {
  console.error("Report generation failed:", error);
  process.exitCode = 1;
}
