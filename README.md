# ChayaPictureLab

### ChayaLab Scientific Report Kit | Hyper Elements Template Challenge 2026

**ChayaPictureLab** is an educational Digital Image Processing laboratory that combines mathematical image-processing implementations with interactive experimentation, algorithm comparison, image-quality analysis, and scientific report generation.

Built with Python, NumPy, Pillow, React, TypeScript, FastAPI, and Hyper Elements, the project allows users to process images, inspect algorithm behaviour, evaluate results, and turn experiments into structured, professional reports.

**Challenge submission: ChayaLab Scientific Report Kit**

ChayaLab Scientific Report Kit is a reusable scientific reporting system built with [Hyper Elements](https://github.com/hyper-elements/hyper-elements). It transforms actual image-processing experiment data into six different report formats using a shared set of reusable templates.

One experiment. Six formats. Consistent scientific reporting.

---

## Hyper Elements Template Challenge Submission

### ChayaLab Scientific Report Kit

Image-processing experiments produce more than just a processed image. They produce parameters, execution measurements, image statistics, comparisons, and observations that need to be presented clearly.

ChayaLab Scientific Report Kit turns this information into structured scientific reports.

It is integrated into the existing ChayaPictureLab application and uses the experiment data from the active user session rather than relying on fabricated report measurements.

### Six output formats

| Format        | Output  | Hyper Elements implementation               |
| ------------- | ------- | ------------------------------------------- |
| PDF Report    | `.pdf`  | `Document` + `renderPdf()`                  |
| Web Report    | `.html` | `Page` + `render()`                         |
| Print Report  | `.html` | Print-ready `Document` + `render()`         |
| Image Summary | `.png`  | `Canvas` + `renderImage()`                  |
| Email Report  | `.html` | `Email` + email-client compatibility plugin |
| Email Text    | `.txt`  | Hyper Elements text rendering               |

### What makes the report useful?

The generated report can contain:

- Experiment title, report ID, and generation timestamp.
- Source image name and image dimensions.
- Original and processed image previews.
- Processing operation and its category.
- Operation purpose and mathematical formula.
- Parameters used during processing.
- Processing execution time.
- Mean image intensity.
- Standard deviation.
- Shannon entropy.
- RMS contrast.
- Optional reference-based quality measurements when valid comparison data is available.
- User-provided notes and interpretation.

The report uses the latest completed image-processing operation in the selected experiment session.

### Meaningful use of Hyper Elements

Hyper Elements is the rendering foundation of the Scientific Report Kit, not simply an additional frontend dependency.

The implementation uses:

- **Page:** Generates the web-based scientific report.
- **Document:** Defines the print-friendly report and PDF document.
- **Canvas:** Creates the visual PNG summary.
- **Email:** Produces an email-compatible report and plain-text alternative.
- **Reusable primitives:** Shared `Column`, `Row`, `Heading`, `Text`, and `Image` components maintain a consistent layout across output types.
- **Validation:** Templates are validated before rendering.
- **Email compatibility:** The email-client compatibility plugin helps identify rendering limitations across email clients.

The reusable report structure is maintained in `report-engine/src/templates/`, while the rendering logic is implemented in `report-engine/src/renderers.tsx`.

The live report service is implemented in `report-engine/src/server.ts`.

### Architecture

The reporting workflow uses the existing ChayaPictureLab experiment session.

1. The user loads an image and performs an image-processing operation.
2. React sends a report-generation request with the current session ID.
3. The Express report service retrieves the experiment data from FastAPI.
4. FastAPI validates the session and supplies the actual experiment information and image previews.
5. Hyper Elements renders the selected output format.
6. The generated report is returned to the frontend for downloading.

```text
ChayaPictureLab React Frontend
          |
          | POST /reports/{format}
          | X-Session-Id
          v
Hyper Elements Report Service
          |
          | GET /api/report-data
          | X-Session-Id
          v
Existing FastAPI Backend
          |
          v
Active Experiment Session
          |
          +-- Source Image
          +-- Processed Image
          +-- Operation and Parameters
          +-- Processing Time
          +-- Image Statistics
          |
          v
Hyper Elements Templates
          |
          +-- PDF
          +-- HTML
          +-- Print HTML
          +-- PNG
          +-- Email HTML
          +-- Email Text
```

All live reports are rendered in memory for individual requests. User-specific report files are not written to a shared demo output directory.

The separate demo command remains available for demonstrating the templates with clearly identified synthetic sample data.

## Screenshots and Rendered Output

The following screenshots demonstrate the actual ChayaPictureLab integration and report templates generated using Hyper Elements.

### Part 1: Hyper Elements Report Studio Interface

The integrated Report Studio provides six export formats within the ChayaPictureLab application.

<img width="939" alt="Hyper Elements Report Studio Interface" src="https://github.com/user-attachments/assets/c1e8ee34-87be-4e7a-bee2-272790ba57b7" />

### Part 2: Generated Scientific Reports

The same experiment data can be rendered into multiple professional report formats.

**A. JPG Scientific Report Preview**

Generated using the Hyper Elements Canvas template.

<img width="1200" alt="ChayaLab JPG Scientific Report" src="https://github.com/user-attachments/assets/4d40217e-4431-4c56-995f-d0cd1a8938f5" />

**B. PDF Scientific Report**

Generated using the Hyper Elements Document template.

<img width="404" alt="ChayaLab PDF Scientific Report" src="https://github.com/user-attachments/assets/5d3628d3-17e0-464f-b8e5-bc100ea249a7" />

## Main Project Features

| Area                        | Capabilities                                                                                                                                                                                          |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Image input                 | Upload JPG, PNG, BMP, and WebP files; load bundled samples; configure maximum loading size                                                                                                            |
| Point and colour operations | Negative, brightness, intensity scaling, contrast, thresholding, gamma and logarithmic transforms, grayscale, channel extraction, isolation, swapping, adjustment, elimination, and HSV decomposition |
| Histogram and enhancement   | Histogram display, stretching, equalization, CDF mapping, global/Otsu/adaptive thresholding                                                                                                           |
| Filtering and restoration   | Mean, Gaussian, median, true mode, minimum, maximum, Laplacian, sharpening, unsharp mask, and outlier filtering                                                                                       |
| Noise experiments           | Gaussian and salt-and-pepper noise with reproducible random seeds, MSE, and PSNR                                                                                                                      |
| Edge detection              | Sobel, Prewitt, Roberts, and Canny with gradient direction visualisation                                                                                                                              |
| Mathematical morphology     | Erosion, dilation, opening, closing, and boundary extraction                                                                                                                                          |
| Algorithm comparison        | Compare 2–6 operations on the same image with parameters and execution timings                                                                                                                        |
| Image analysis              | Dimensions, channels, mean, standard deviation, RMS contrast, Michelson contrast, entropy, and histograms                                                                                             |
| Experiment history          | Session-based operation history and JSON export                                                                                                                                                       |
| Scientific reporting        | Existing HTML report and the six-format Hyper Elements Report Studio                                                                                                                                  |

Operation pages display the method's purpose, relevant mathematical formula, parameters, and implementation details.

## Technology Stack

| Layer               | Technologies                                 |
| ------------------- | -------------------------------------------- |
| Image processing    | Python, NumPy, Pillow                        |
| Existing interface  | Streamlit                                    |
| Modern frontend     | React, TypeScript, Vite                      |
| Backend API         | FastAPI                                      |
| Report service      | Node.js, TypeScript, Express                 |
| Report rendering    | Hyper Elements                               |
| PDF generation      | `@hyper-elements/react/pdf`                  |
| Image rendering     | `@hyper-elements/react/image`                |
| Email compatibility | `@hyper-elements/email-clients`              |
| Testing             | pytest, TypeScript checks, production builds |

### Image-processing implementation

The core processing routines in `chayalab/` are implemented using NumPy so that their mathematical steps can be inspected.

OpenCV is used only for optional reference checks and validation. It does not generate the normal processing outputs of the application.

---

## Installation and Local Setup

### Requirements

- Python 3.10 or newer.
- Node.js 20 or newer; Node.js 22 is recommended.
- npm.
- Dependencies listed in the project's requirements files.

### 1. Clone the repository

```powershell
git clone https://github.com/Jai-Shankar1033/ChayaPictureLab.git

cd ChayaPictureLab
git switch feature/hyper-elements-report-kit
```

### 2. Configure the Python environment

From the project root:

```powershell
py -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

python -m pip install -r requirements-render.txt
```

The API runtime requirements are separated from the complete Streamlit development requirements.

### 3. Install the report-engine dependencies

Open a separate terminal:

```powershell
cd report-engine

npm ci
```

The report engine uses the installed Hyper Elements dependencies and email-client compatibility plugin.

### 4. Install the frontend dependencies

Open another terminal:

```powershell
cd frontend

npm ci
```

### 5. Start FastAPI

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

FastAPI runs at:

`http://127.0.0.1:8000`

Health endpoint:

`http://127.0.0.1:8000/api/health`

### 6. Start the Hyper Elements report service

From `report-engine/`:

```powershell
npm run dev
```

The report service runs at:

`http://127.0.0.1:4100`

Check its health:

```powershell
Invoke-RestMethod http://127.0.0.1:4100/health
```

### 7. Start the React frontend

From `frontend/`:

```powershell
npm run dev
```

Open:

`http://localhost:5173`

Vite proxies `/api/*` requests to FastAPI and `/reports/*` requests to the Hyper Elements report service.

### Local service overview

| Service                       | Local address           |
| ----------------------------- | ----------------------- |
| React frontend                | `http://localhost:5173` |
| FastAPI backend               | `http://127.0.0.1:8000` |
| Hyper Elements report service | `http://127.0.0.1:4100` |

---

## Using the Report Studio

1. Open ChayaPictureLab in your browser.
2. Upload an image or select a bundled sample.
3. Select an image-processing operation.
4. Configure its parameters and run it.
5. Open **Analysis & reports**.
6. Locate **Hyper Elements Report Studio**.
7. Add optional experiment notes.
8. Select the desired output format.
9. Download the generated report.

The report service retrieves experiment information from FastAPI using the active `X-Session-Id` header. The browser does not supply arbitrary image measurements for report generation.

### Report API routes

The report service supports the following endpoints:

| Method | Route                 | Purpose             |
| ------ | --------------------- | ------------------- |
| POST   | `/reports/pdf`        | Generate PDF        |
| POST   | `/reports/html`       | Generate web HTML   |
| POST   | `/reports/print-html` | Generate print HTML |
| POST   | `/reports/png`        | Generate PNG        |
| POST   | `/reports/email-html` | Generate email HTML |
| POST   | `/reports/email-text` | Generate email text |



---



### Python tests

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt

python -m pytest -v
```

### Report-engine checks

From `report-engine/`:

```powershell
npm run typecheck

npm run build
```

### Frontend production build

From `frontend/`:

```powershell
npm run build
```

Run these checks locally to validate the current environment.

The demo renderer can also be used to generate showcase output:

```powershell
cd report-engine

npm run demo
```


---

## Project Structure

```text
ChayaPictureLab/
│
├── main.py
├── api.py
├── LICENSE
├── requirements.txt
├── requirements-render.txt
├── requirements-dev.txt
│
├── frontend/
│   └── src/
│       ├── App.tsx
│       └── components/
│           └── ReportExportPanel.tsx
│
├── report-engine/
│   ├── package.json
│   ├── README.md
│   └── src/
│       ├── server.ts
│       ├── renderers.tsx
│       ├── types.ts
│       ├── theme.ts
│       ├── demo.tsx
│       └── templates/
│           ├── page.tsx
│           ├── document.tsx
│           ├── canvas.tsx
│           ├── email.tsx
│           └── shared.tsx
│
├── chayalab/
│   ├── validation.py
│   ├── colorspace.py
│   ├── point_ops.py
│   ├── histogram.py
│   ├── filters.py
│   ├── noise.py
│   ├── edges.py
│   ├── morphology.py
│   ├── metrics.py
│   ├── registry.py
│   ├── history.py
│   ├── report.py
│   ├── io_utils.py
│   └── reference.py
│
├── tests/
├── tools/
├── samples/
└── docs/
    └── screenshots/
```

---

## Research Areas

ChayaPictureLab explores the following areas of Digital Image Processing.

| Research area                  | Topics                                                                                 |
| ------------------------------ | -------------------------------------------------------------------------------------- |
| Image enhancement              | Brightness, contrast, gamma correction, logarithmic transforms, histogram equalization |
| Colour image processing        | RGB, grayscale, HSV decomposition, colour-channel operations                           |
| Histogram processing           | Histograms, stretching, equalization, Otsu and adaptive thresholding                   |
| Filtering and restoration      | Spatial filters, noise generation, noise removal                                       |
| Edge detection                 | Sobel, Prewitt, Roberts and Canny                                                      |
| Mathematical morphology        | Erosion, dilation, opening, closing and boundaries                                     |
| Image quality assessment       | MSE, PSNR, entropy and contrast                                                        |
| Comparative algorithm analysis | Output comparison, parameter analysis and processing time                              |

---

## Research Papers and Academic References

### Selected research papers

**[1] Automatic Image Thresholding**

N. Otsu, "A Threshold Selection Method from Gray-Level Histograms," *IEEE Transactions on Systems, Man, and Cybernetics*, vol. 9, no. 1, pp. 62–66, January 1979.

DOI: [https://doi.org/10.1109/TSMC.1979.4310076](https://doi.org/10.1109/TSMC.1979.4310076)

Application: Theoretical foundation for Otsu's automatic image thresholding.

**[2] Edge Detection**

J. Canny, "A Computational Approach to Edge Detection," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. PAMI-8, no. 6, pp. 679–698, 1986.

DOI: [https://doi.org/10.1109/TPAMI.1986.4767851](https://doi.org/10.1109/TPAMI.1986.4767851)

Application: Research foundation for Canny edge detection.

**[3] Image Filtering and Restoration**

T. S. Huang, G. J. Yang, and G. Y. Tang, "A Fast Two-Dimensional Median Filtering Algorithm," *IEEE Transactions on Acoustics, Speech, and Signal Processing*, vol. 27, no. 1, pp. 13–18, February 1979.

DOI: [https://doi.org/10.1109/TASSP.1979.1163188](https://doi.org/10.1109/TASSP.1979.1163188)

Application: Research background for median filtering and image noise reduction.

### Foundational academic textbooks

**[4] Digital Image Processing**

Rafael C. Gonzalez and Richard E. Woods, *Digital Image Processing*, 4th Edition, Pearson, 2018.

ISBN: 9789353062989.

**[5] Mathematical Morphology**

Jean Serra, *Image Analysis and Mathematical Morphology*, Academic Press, 1982.

---

## Known Limitations

- The FastAPI application currently stores experiment sessions in an in-memory `SESSIONS` dictionary. Restarting the backend clears active session data.
- Multiple backend instances do not automatically share session state.
- The current live report focuses on the latest completed operation in the selected session.
- Reference-based quality measurements such as MSE and PSNR should only be reported when valid reference-comparison data is available.
- Email reports intentionally omit image previews.
- Large image operations and report rendering can require significant CPU and memory.
- The current session-ID mechanism is intended for the academic demonstration and is not a substitute for production authentication and persistent storage.

A persistent storage and authentication layer would be required before exposing the application as a public, multi-user production service.

---

## Challenge Submission Notes

**Submission:** ChayaLab Scientific Report Kit

**Challenge:** Hyper Elements Template Challenge 2026

**Repository:** [ChayaPictureLab](https://github.com/Jai-Shankar1033/ChayaPictureLab)

**Implementation branch:** [feature/hyper-elements-report-kit](https://github.com/Jai-Shankar1033/ChayaPictureLab/tree/feature/hyper-elements-report-kit)

The complete implementation source, reusable templates, local setup instructions, and report-generation service are included in this branch.

A live deployment is not required for the challenge. The project can be reproduced locally using the instructions above.

---

## License

ChayaPictureLab is distributed under the [MIT License](LICENSE).

Copyright (c) 2026 Jai Shankar.

The MIT License applies to the project's original work. Third-party libraries and dependencies remain subject to their respective licenses.

---

## Acknowledgment

ChayaPictureLab acknowledges the researchers and academic authors whose published work contributed to the theoretical foundations of Digital Image Processing.

The project also uses open-source technologies, including Python, NumPy, Pillow, React, FastAPI, and Hyper Elements.

The Scientific Report Kit uses Hyper Elements to create reusable, structured, and multi-format reports from image-processing experiments.

Research publications are credited for their theoretical contributions, while the project's processing routines and reporting templates are implemented as part of ChayaPictureLab.
