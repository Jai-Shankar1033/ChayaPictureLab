import {
  Column,
  Heading,
  Image,
  Row,
  Text,
} from "@hyper-elements/react";
import type { ExperimentReportData, ReportImage } from "../types.js";
import { palette } from "../theme.js";

function formatNumber(value: number, digits = 2): string {
  return Number.isFinite(value) ? value.toFixed(digits) : "Not available";
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Column style={{ flex: 1, gap: 5, padding: 14, backgroundColor: "#F3F6FA", borderRadius: 10 }}>
      <Text style={{ color: palette.muted, fontSize: 10, fontWeight: 700 }}>{label.toUpperCase()}</Text>
      <Heading level={3} style={{ color: palette.ink, fontSize: 21 }}>{value}</Heading>
      <Text style={{ color: palette.muted, fontSize: 10 }}>{detail}</Text>
    </Column>
  );
}

function ImagePanel({ label, image }: { label: string; image: ReportImage }) {
  return (
    <Column style={{ flex: 1, gap: 8 }}>
      <Image
        src={{ src: image.src, width: image.width, height: image.height }}
        alt={image.alt}
        style={{ width: "100%", maxWidth: 320, borderRadius: 10 }}
      />
      <Text style={{ color: palette.muted, fontSize: 11, fontWeight: 700 }}>{label}</Text>
    </Column>
  );
}

export function ReportBody({ data, includeImages }: { data: ExperimentReportData; includeImages: boolean }) {
  const generated = new Date(data.generatedAt);
  const generatedLabel = Number.isNaN(generated.getTime()) ? data.generatedAt : generated.toLocaleString("en-IN");

  return (
    <Column style={{ gap: 18, padding: 26, backgroundColor: palette.paper, borderRadius: 14 }}>
      <Column style={{ gap: 7 }}>
        <Text style={{ color: palette.teal, fontSize: 10, fontWeight: 700, letterSpacing: 1.2 }}>CHAYALAB / IMAGE SCIENCE</Text>
        <Heading level={1} style={{ color: palette.ink, fontSize: 28, lineHeight: 1.15 }}>{data.title}</Heading>
        <Text style={{ color: palette.muted, fontSize: 11 }}>Report {data.reportId} · Generated {generatedLabel}</Text>
        <Text style={{ color: "#946200", fontSize: 10, fontWeight: 700 }}>{data.dataLabel}</Text>
      </Column>

      <Column style={{ gap: 7 }}>
        <Heading level={2} style={{ color: palette.ink, fontSize: 17 }}>Experiment overview</Heading>
        <Text style={{ color: palette.muted, fontSize: 12 }}>Source: {data.sourceName}</Text>
        <Text style={{ color: palette.muted, fontSize: 12 }}>Dimensions: {data.image.width} × {data.image.height} pixels · {data.image.channels} channel(s)</Text>
        <Text style={{ color: palette.muted, fontSize: 12 }}>Category: {data.operation.category}</Text>
      </Column>

      <Column style={{ gap: 9 }}>
        <Heading level={2} style={{ color: palette.ink, fontSize: 17 }}>Measured results</Heading>
        <Row stackOnMobile style={{ gap: 9 }}>
          <Metric label="Processing time" value={`${formatNumber(data.processingMs, 1)} ms`} detail="Measured elapsed time" />
          <Metric label="Mean intensity" value={formatNumber(data.statistics.mean, 2)} detail="Output image mean" />
        </Row>
        <Row stackOnMobile style={{ gap: 9 }}>
          <Metric label="Entropy" value={`${formatNumber(data.statistics.entropyBits, 2)} bits`} detail="Shannon entropy" />
          <Metric label="RMS contrast" value={formatNumber(data.statistics.rmsContrast, 4)} detail="Standard deviation / 255" />
        </Row>
        <Text style={{ color: palette.muted, fontSize: 10 }}>Standard deviation: {formatNumber(data.statistics.standardDeviation, 3)}</Text>
        {data.referenceQuality && (data.referenceQuality.mse !== undefined || data.referenceQuality.psnrDb !== undefined) ? (
          <Column style={{ gap: 4, padding: 12, backgroundColor: palette.violetLight, borderRadius: 9 }}>
            <Text style={{ color: palette.violet, fontSize: 11, fontWeight: 700 }}>REFERENCE-BASED QUALITY METRICS</Text>
            {data.referenceQuality.mse !== undefined ? <Text style={{ color: palette.ink, fontSize: 12 }}>MSE: {formatNumber(data.referenceQuality.mse, 4)}</Text> : null}
            {data.referenceQuality.psnrDb !== undefined ? <Text style={{ color: palette.ink, fontSize: 12 }}>PSNR: {formatNumber(data.referenceQuality.psnrDb, 3)} dB</Text> : null}
          </Column>
        ) : (
          <Text style={{ color: palette.muted, fontSize: 10 }}>MSE and PSNR are not reported because this example does not include a ground-truth reference comparison.</Text>
        )}
      </Column>

      <Column style={{ gap: 7 }}>
        <Heading level={2} style={{ color: palette.ink, fontSize: 17 }}>Processing operation</Heading>
        <Heading level={3} style={{ color: palette.teal, fontSize: 15 }}>{data.operation.name}</Heading>
        <Text style={{ color: palette.muted, fontSize: 12 }}>{data.operation.purpose}</Text>
        {data.operation.formula ? <Column style={{ gap: 5, padding: 12, backgroundColor: "#F3F6FA", borderRadius: 9 }}>
          <Text style={{ color: palette.muted, fontSize: 9, fontWeight: 700 }}>FORMULA</Text>
          <Text style={{ color: palette.ink, fontSize: 12 }}>{data.operation.formula}</Text>
        </Column> : null}
        <Text style={{ color: palette.muted, fontSize: 10, fontWeight: 700 }}>PARAMETERS</Text>
        {Object.entries(data.operation.parameters).map(([key, value]) => (
          <Row key={key} style={{ gap: 12, padding: 7, backgroundColor: "#F8FAFC", borderRadius: 6 }}>
            <Text style={{ color: palette.muted, fontSize: 11 }}>{key}</Text>
            <Text style={{ color: palette.ink, fontSize: 11, fontWeight: 700, textAlign: "right" }}>{String(value)}</Text>
          </Row>
        ))}
      </Column>

      {includeImages && data.originalImage && data.processedImage ? (
        <Column style={{ gap: 9 }}>
          <Heading level={2} style={{ color: palette.ink, fontSize: 17 }}>Visual comparison</Heading>
          <Row stackOnMobile style={{ gap: 12, alignItems: "start" }}>
            <ImagePanel label="ORIGINAL IMAGE" image={data.originalImage} />
            <ImagePanel label="PROCESSED IMAGE" image={data.processedImage} />
          </Row>
        </Column>
      ) : (
        <Column style={{ gap: 4, padding: 12, backgroundColor: "#F3F6FA", borderRadius: 9 }}>
          <Text style={{ color: palette.ink, fontSize: 11, fontWeight: 700 }}>IMAGE PRIVACY</Text>
          <Text style={{ color: palette.muted, fontSize: 10 }}>Image previews are omitted from this email-safe version. Open the report in ChayaPictureLab to view the original and processed images.</Text>
        </Column>
      )}

      {data.notes ? <Column style={{ gap: 5 }}>
        <Heading level={2} style={{ color: palette.ink, fontSize: 15 }}>Notes and interpretation</Heading>
        <Text style={{ color: palette.muted, fontSize: 11 }}>{data.notes}</Text>
      </Column> : null}

      <Column style={{ gap: 4 }}>
        <Text style={{ color: palette.muted, fontSize: 9 }}>ChayaPictureLab · Scientific image-processing report</Text>
        <Text style={{ color: palette.muted, fontSize: 9 }}>Report values should be interpreted in the context of the source image, parameters and experimental method.</Text>
      </Column>
    </Column>
  );
}

export function CanvasSummary({ data }: { data: ExperimentReportData }) {
  return (
    <Column style={{ gap: 18, padding: 34, backgroundColor: "#F3F6FA", borderRadius: 18 }}>
      <Row style={{ justifyContent: "space-between", alignItems: "start", gap: 18 }}>
        <Column style={{ flex: 1, gap: 6 }}>
          <Text style={{ color: palette.teal, fontSize: 12, fontWeight: 700, letterSpacing: 1.3 }}>CHAYALAB / IMAGE SCIENCE</Text>
          <Heading level={1} style={{ color: palette.ink, fontSize: 34, lineHeight: 1.1 }}>Experiment summary</Heading>
          <Text style={{ color: palette.muted, fontSize: 14 }}>{data.operation.name} · {data.operation.category}</Text>
        </Column>
        <Column style={{ padding: 10, backgroundColor: "#FFF4D8", borderRadius: 8 }}>
          <Text style={{ color: "#805B12", fontSize: 9, fontWeight: 700 }}>{data.dataLabel}</Text>
        </Column>
      </Row>
      <Row style={{ gap: 12 }}>
        <Metric label="Runtime" value={`${formatNumber(data.processingMs, 1)} ms`} detail="Elapsed" />
        <Metric label="Entropy" value={`${formatNumber(data.statistics.entropyBits, 2)} bits`} detail="Shannon" />
        <Metric label="RMS contrast" value={formatNumber(data.statistics.rmsContrast, 3)} detail="Output" />
      </Row>
      <Row style={{ gap: 14, alignItems: "start" }}>
        {data.originalImage ? <ImagePanel label="ORIGINAL" image={data.originalImage} /> : null}
        {data.processedImage ? <ImagePanel label="PROCESSED" image={data.processedImage} /> : null}
      </Row>
      <Text style={{ color: palette.muted, fontSize: 10 }}>Report {data.reportId} · {data.sourceName} · {data.image.width} × {data.image.height}</Text>
    </Column>
  );
}
