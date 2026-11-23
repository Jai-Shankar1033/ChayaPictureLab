# ChayaPictureLab Hyper Elements Report Engine

A local report service for the existing ChayaPictureLab React + FastAPI application. It uses `@hyper-elements/react` 0.5.2 and the current report templates to create six downloadable formats from the active experiment session.

## Formats

| Format route | File | Renderer |
|---|---|---|
| `pdf` | PDF | Hyper Elements `Document` + `renderPdf` |
| `html` | HTML | Hyper Elements `Page` + `render` |
| `print-html` | HTML | Print-ready `Document` + `render` |
| `png` | PNG | Hyper Elements `Canvas` + `renderImage` |
| `email-html` | HTML | Hyper Elements `Email` + email-client compatibility plugin |
| `email-text` | TXT | Hyper Elements text output |

All report files are rendered in memory for each request. The live service does not write to the shared demo `output/` directory. The `demo` script remains available for template showcase output and uses clearly labelled synthetic sample data.

## Local setup

Prerequisites: Node.js 20+ (Node 22 recommended), Python environment with the existing ChayaPictureLab requirements, and the current frontend dependencies.

### 1. Install report-engine dependencies

From the repository root:

```powershell
Set-Location report-engine
npm install
```

`@hyper-elements/email-clients` is a production dependency because the running server imports it for live email renders.

### 2. Start FastAPI

Open a separate PowerShell window at the repository root:

```powershell
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

The backend must contain `GET /api/report-data`, which returns the current session's real experiment report data and requires `X-Session-Id`. This is the endpoint added to the existing `api.py` during integration.

### 3. Start the report service

In another PowerShell window:

```powershell
Set-Location report-engine
npm run dev
```

The service listens on `http://127.0.0.1:4100` and calls the FastAPI endpoint. Optional environment variables are documented in `.env.example`.

Check it:

```powershell
Invoke-RestMethod http://127.0.0.1:4100/health
```

Expected response includes `ok: true` and `service: chayalab-report-engine`.

### 4. Start the frontend

In a third PowerShell window:

```powershell
Set-Location frontend
npm run dev
```

The Vite configuration proxies `/api/*` to FastAPI and `/reports/*` to the report service. The existing `/api/*` proxy is preserved.

## Connect the export panel to App.tsx

The ready-to-use component is `frontend/src/components/ReportExportPanel.tsx`.

Add this import to `frontend/src/App.tsx`:

```tsx
import { ReportExportPanel } from "./components/ReportExportPanel";
```

Inside the existing **Analysis & reports** page content, place the component where the export controls should appear:

```tsx
<ReportExportPanel
  sessionId={sid}
  disabled={!image || history.length === 0}
/>
```

This uses the existing `sid`, `image` and `history` state names from ChayaPictureLab. The component supports optional report notes, disables duplicate in-flight requests, downloads the generated file, and displays backend errors to the user.

## API contract

The frontend sends:

```http
POST /reports/pdf
X-Session-Id: <the current ChayaPictureLab session id>
Content-Type: application/json

{"notes":"Optional experiment notes"}
```

The report service then requests `GET /api/report-data` from FastAPI using the same `X-Session-Id`. It does not accept image data or experiment measurements from the browser. It validates the backend response, then renders the report.

The supported report routes are `/reports/pdf`, `/reports/html`, `/reports/print-html`, `/reports/png`, `/reports/email-html`, and `/reports/email-text`.

## Production build (not deployed by this patch)

```powershell
Set-Location report-engine
npm run typecheck
npm run build
npm start
```

For a cloud host, set `HOST=0.0.0.0`, `PORT` to the platform's assigned port, and `CHAYA_API_BASE_URL` to the FastAPI service URL. The report service must be deployed as a separate backend service. The frontend host must route `/reports/*` to that service. **No Vercel or Render deployment configuration is changed by this package.**

## Operational and security limitations

- The current FastAPI `SESSIONS` dictionary is in-memory. A backend restart loses active experiments; multiple backend instances do not share session data. This integration does not turn that into persistent storage.
- The session ID is a bearer-style identifier in the current application. Keep it private, do not log it, and do not expose it in a URL. Proper authentication and persistent session storage are required before a public multi-user production rollout.
- The service accepts only a restricted session-ID character set, limits notes to 4,000 characters, limits image data URI size, caps concurrent render jobs, and marks responses `no-store`.
- The API currently provides only a single latest-operation result in its main report payload. It does not invent MSE/PSNR; reference-based metrics should only be added when the backend supplies a valid reference comparison.
- Email templates intentionally omit image previews to reduce accidental disclosure of user images.
- HTML, PDF and PNG rendering can use significant CPU and memory. The live renderer limits concurrent renders to two by default.

## Verification

Run these from `report-engine/`:

```powershell
npm run typecheck
npm run build
```

Then run the service and check `/health`. After loading an image and running an operation in ChayaPictureLab, generate each output from the Analysis & reports panel.
