# ChayaPictureLab

**ChayaPictureLab** is an educational Digital Image Processing laboratory built with Python, NumPy, Pillow, and Streamlit. It lets you load an image, run an operation, compare outputs, perform noise-and-restoration experiments using MSE/PSNR, and export an experiment report.

The core processing routines in `chayalab/` are implemented with NumPy so their mathematical steps can be inspected. OpenCV is used only for optional reference checks and validation; it is not used to generate the app's normal processing outputs.

## Features

| Area | Capabilities |
|---|---|
| Image input | Upload JPG, PNG, BMP, or WebP files; load a bundled sample; set a maximum image size for loading |
| Point and colour operations | Negative, brightness, intensity scaling, contrast, thresholding, gamma and logarithmic transforms, grayscale, channel extraction/isolation/swapping/adjustment/elimination, and HSV decomposition |
| Histogram and enhancement | Histogram display, stretching, equalization with CDF/mapping plot, global/Otsu/adaptive thresholding, and optional OpenCV validation |
| Filtering and restoration | Mean, Gaussian, median, true mode, min/max, Laplacian, sharpening, unsharp mask, and outlier filtering; Gaussian or salt-and-pepper noise experiments with MSE/PSNR and reproducible random seeds |
| Edge detection | Sobel, Prewitt, Roberts, and Canny, including gradient direction visualisation |
| Morphology | Erosion, dilation, opening, closing, and boundary extraction using rectangular, cross, or elliptical structuring elements |
| Algorithm comparison | Compare 2–6 operations on the same image, with parameters and timings displayed |
| Analysis and reports | Dimensions, channels, mean, standard deviation, RMS/Michelson contrast, entropy, histograms, session history, HTML report export, and JSON history download |

Operation pages show the method's purpose, relevant formula, and which parts use manual NumPy implementations.

## Requirements

- Python 3.10 or newer (the recorded development environment used Python 3.12).
- Dependencies listed in `requirements.txt`.
- For tests, install the additional packages listed in `requirements-dev.txt`.

## Install and run

### Windows PowerShell

From the project root directory, run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run main.py
```

If PowerShell blocks activation, you can use the current-session setting below and then activate the environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bat
py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
streamlit run main.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run main.py
```

The app normally opens at <http://localhost:8501>. Once dependencies are installed, routine local use does not require an internet connection.

## Run the tests

Activate the virtual environment, then run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

A recorded test run is saved in `docs/test_results.txt`; run the tests locally to confirm results for your own Python version and computer. Additional validation notes are in `docs/validation_numbers.txt`.

## Project layout

```text
main.py                 Streamlit interface
chayalab/
  validation.py         Input checks and safe float-to-uint8 conversion
  colorspace.py         RGB/BGR, grayscale, channels, and HSV operations
  point_ops.py          Point transforms, thresholds, and image arithmetic
  histogram.py          Histogram/PDF/CDF, stretching, equalization, Otsu, adaptive threshold
  filters.py            Mean, Gaussian, median, mode, min/max, Laplacian, unsharp, outlier filters
  noise.py              Gaussian and salt-and-pepper noise; restoration helpers
  edges.py              Sobel, Prewitt, Roberts, and Canny
  morphology.py         Structuring elements, erosion, dilation, opening, closing, boundaries
  metrics.py            MSE, PSNR, entropy, contrast, and image statistics
  registry.py           Operation definitions, parameters, and formulas for the UI
  history.py            Session experiment history
  report.py             HTML report export
  io_utils.py           Image loading and saving with Pillow
  reference.py          Optional OpenCV reference implementations for validation
 tests/                  Automated tests for algorithms, edge cases, and UI flows
 tools/make_samples.py   Generates bundled synthetic sample images
 samples/                Bundled synthetic sample images
 docs/                   Audit, originality review, known issues, test and output
```

## Algorithms and libraries

- **NumPy:** core array calculations and the project's manual implementations of point operations, colour conversion, histogram methods, filters, noise handling, edge detection, morphology, and metrics.
- **Pillow:** image-file loading/saving, resizing on load, and report image encoding.
- **Streamlit:** application interface and controls.
- **Matplotlib:** plots and histogram visualisation.
- **OpenCV:** optional reference comparison in validation tests and the app's validation control; not used to produce standard processed-image outputs.

## Project history, attribution, and licence

This release was developed from an earlier ChayaPictureLab archive. Two processing modules in that earlier archive were found to match code in a public MIT-licensed image-processing project. The current `chayalab/` package was reimplemented, and the scope and limits of the review are described in `THIRD_PARTY_NOTICES.md`.

The project history is stated here for transparency; it does not imply a personal relationship with the earlier project's author or that the current release depends on that repository at runtime. See `THIRD_PARTY_NOTICES.md` for third-party library notices and the project's recorded source history.


## Known limitations

See `docs/KNOWN_ISSUES.md`. For example, the mode filter may be slow on large colour images, and geometric operations such as resizing and rotation are not included as processing operations in this lab.
