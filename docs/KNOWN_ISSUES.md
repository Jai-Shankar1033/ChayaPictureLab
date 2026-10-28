# Known issues, unavailable checks and uncertainties

## Limitations of the software
1. **Mode filter speed.** Cost grows with the number of distinct grey levels. Measured on a random 1024x768 image:
   about 2.7 s (gray) and 8 s (colour). The UI warns and the noise experiment defaults to grayscale.
2. **Mode filter on continuous noisy photos is a poor denoiser** (it needs repeated values). On the noisy sample it
   scored PSNR 22.7 dB vs 39.0 dB for the median at 5% salt-and-pepper. This is expected behaviour, not a bug.
3. **Adaptive threshold** differs from OpenCV on 2-7% of interior pixels of natural-looking images because OpenCV rounds
   the local mean to an integer (reproduced exactly in `tests/test_histogram.py`). Ours uses the exact mean.
4. **Canny** thresholds are fractions of the maximum thinned gradient, not OpenCV's absolute values, so settings are not
   interchangeable. Results agree with `cv2.Canny` only approximately (see the report).
5. **Colour histogram equalization** is not offered (equalizing R, G, B separately shifts colours); colour input is converted
   to grayscale first and the UI says so.
6. Images are shrunk on load (default longest side 1024 px). Geometric operations (resize, rotate, flip) are out of scope.
7. Session history lives in browser-session memory only; refreshing the page clears it.

## Checks that were NOT performed
* No code-similarity tool (MOSS, JPlag, etc.) was run, and GitHub was **not** searched exhaustively.
* Only two files of the earlier repository were compared line by line (see `originality_review.md`).
* Tested only on Linux with Python 3.12.3 (NumPy 2.4.4, OpenCV 4.13.0, Pillow 12.1.1, Streamlit 1.66.1).
  Windows/macOS and other Python versions were not run.
* No manual testing with real browser file-upload of a user photo; upload was tested through the loader function with
  generated PNG/JPEG/BMP bytes, and the UI through bundled samples (AppTest + Playwright screenshots).
* Dependency installation in a clean virtual environment: see the final verification section of the report.

## Licensing uncertainties
* `LICENSE` has a **placeholder name** that you must replace.
* Third-party licence names in `THIRD_PARTY_NOTICES.md` were not read from installed metadata.
* Whether retaining the upstream MIT notice is sufficient for your college is for your instructor to decide.
