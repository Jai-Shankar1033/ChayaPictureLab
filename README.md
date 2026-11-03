# ChayaPictureLab

**ChayaPictureLab** is an educational Digital Image Processing laboratory built with Python, NumPy, Pillow, and Streamlit. It lets you load an image, run an operation, compare outputs, perform noise-and-restoration experiments using MSE/PSNR, and export an experiment report.

The core processing routines in `chayalab/` are implemented with NumPy so their mathematical steps can be inspected. OpenCV is used only for optional reference checks and validation; it is not used to generate the app's normal processing outputs.
You can refer https://chayapicturelab.streamlit.app/

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
  ## Research Areas

ChayaPictureLab explores the following areas of Digital Image Processing (DIP):

| Research Area | Topics Covered in ChayaPictureLab |
|---|---|
| Image Enhancement | Brightness adjustment, contrast enhancement, gamma correction, logarithmic transformation, and histogram equalization |
| Colour Image Processing | RGB, grayscale, HSV decomposition, colour-channel extraction, isolation, swapping, and adjustment |
| Histogram Processing and Thresholding | Histogram analysis, histogram stretching, equalization, Otsu thresholding, and adaptive thresholding |
| Image Filtering and Restoration | Mean, Gaussian, median, mode, minimum, maximum, Laplacian, sharpening, and noise removal |
| Edge Detection | Sobel, Prewitt, Roberts, and Canny edge detection with gradient direction analysis |
| Mathematical Morphology | Erosion, dilation, opening, closing, and boundary extraction using different structuring elements |
| Image Quality Assessment | Mean Squared Error (MSE), Peak Signal-to-Noise Ratio (PSNR), entropy, and contrast measurement |
| Comparative Algorithm Analysis | Comparing multiple image-processing operations through output visualisation, parameter analysis, and execution time |

## Research Papers and Academic References

The development and theoretical study of ChayaPictureLab are supported by established research publications and academic references in Digital Image Processing.

### Selected Research Papers

**[1] Automatic Image Thresholding**

N. Otsu, "A Threshold Selection Method from Gray-Level Histograms," *IEEE Transactions on Systems, Man, and Cybernetics*, vol. 9, no. 1, pp. 62–66, January 1979.

DOI: https://doi.org/10.1109/TSMC.1979.4310076

Application: Provides the theoretical foundation for Otsu's automatic image thresholding method used in the project.

**[2] Edge Detection**

J. Canny, "A Computational Approach to Edge Detection," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. PAMI-8, no. 6, pp. 679–698, 1986.

DOI: https://doi.org/10.1109/TPAMI.1986.4767851

Application: Provides the research foundation for Canny edge detection and the study of image boundaries.

**[3] Image Filtering and Restoration**

T. S. Huang, G. J. Yang, and G. Y. Tang, "A Fast Two-Dimensional Median Filtering Algorithm," *IEEE Transactions on Acoustics, Speech, and Signal Processing*, vol. 27, no. 1, pp. 13–18, February 1979.

DOI: https://doi.org/10.1109/TASSP.1979.1163188

Application: Provides research background for two-dimensional median filtering and noise reduction.

### Foundational Academic Textbooks

**[4] Digital Image Processing**

Rafael C. Gonzalez and Richard E. Woods, *Digital Image Processing*, 4th Edition, Pearson, 2018.

ISBN: 9789353062989.

Application: Provides the broader theoretical background for image enhancement, filtering, histogram processing, image restoration, segmentation, and image analysis.

**[5] Mathematical Morphology**

Jean Serra, *Image Analysis and Mathematical Morphology*, Academic Press, 1982.

Application: Provides the mathematical foundation for morphological operations, including erosion, dilation, opening, and closing.

## Acknowledgment

ChayaPictureLab acknowledges the researchers and academic authors whose published work has contributed to the development of Digital Image Processing. The research papers and textbooks listed above were used as academic references to understand the mathematical concepts, working principles, and theoretical foundations of the image-processing techniques explored in this project.

Their contributions provide valuable knowledge for studying image enhancement, thresholding, filtering, restoration, edge detection, and mathematical morphology.

The project applies these concepts through its own Python and NumPy-based processing implementations. The references are credited for their research contributions and theoretical foundations.

## Project history, attribution, and licence

This release was developed from an earlier ChayaPictureLab archive. Two processing modules in that earlier archive were found to match code in a public MIT-licensed image-processing project. The current `chayalab/` package was reimplemented, and the scope and limits of the review are described in `THIRD_PARTY_NOTICES.md`.

The project history is stated here for transparency; it does not imply a personal relationship with the earlier project's author or that the current release depends on that repository at runtime. See `THIRD_PARTY_NOTICES.md` for third-party library notices and the project's recorded source history.


## Known limitations

See `docs/KNOWN_ISSUES.md`. For example, the mode filter may be slow on large colour images, and geometric operations such as resizing and rotation are not included as processing operations in this lab.
