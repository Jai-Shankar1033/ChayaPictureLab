## Architecture found
`main.py` (Streamlit, sidebar categories) + `ui_catalog.py` (operation catalogue) + `ui_style.py` (CSS) + six processing
modules (`point_operations.py, color_operations.py, Histogram.py, filters_logic.py, edge_detection.py, morphology_logic.py`).
Mostly thin wrappers around OpenCV calls. No tests, unpinned `requirements.txt`.

## Functional defects reproduced by running the old code
| # | Finding | Evidence |
|---|---|---|
| 1 | "Mode filter" is the **median filter** (`cv2.medianBlur`) | outputs identical on a random image |
| 2 | "Gaussian Averaging" brightens the image: negative noise is cast to uint8 and wraps | flat image of 100 -> mean **181.6** (expected ~100) |
| 3 | Laplacian response cast with `np.uint8` wraps | isolated bright pixel: true response 1020, stored as **252** |
| 4 | Histogram stretching of a constant image divides by zero | RuntimeWarnings, output all 0 |
| 5 | Salt-and-pepper random masks use `image.shape`, so each colour channel is corrupted independently (colour speckle); black/white drawn separately | read from code |
| 6 | Only Sobel offered, combining |Gx| and |Gy| with 0.5/0.5 weights (not the true magnitude); no Prewitt, Roberts, Canny | read from code |
| 7 | Morphology lacked **closing** (it already had internal/external/gradient boundaries); no metrics (MSE/PSNR), no tests | read from code |

## Dependencies, licensing, attribution
OpenCV, NumPy, Streamlit, (Matplotlib) unpinned. README claims MIT without a LICENSE file; upstream attribution absent.
Two modules match a public MIT repository (see `originality_review.md`). Sample images of unknown or likely copyrighted origin
(anime artwork, textbook figures, a test photo) are bundled.

## Keep / redesign / replace
* **Kept (as features):** the operation list, outlier restoration idea, Streamlit UI with original-vs-result view, downloads.
* **Redesigned:** UI built from a registry; sections reorganised into an experiment workflow.
* **Replaced:** every processing module (new NumPy implementations), samples, requirements, README.
