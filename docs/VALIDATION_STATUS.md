# Validation status and test coverage

This document separates checks that have recorded evidence from checks that have not been completed. It is not a plagiarism certificate or a guarantee that the application works on every machine.

## Recorded test environment

The previous test record identifies this environment:

- Operating system: Linux
- Python: 3.12.3
- NumPy: 2.4.4
- OpenCV: 4.13.0
- Pillow: 12.1.1
- Streamlit: 1.66.1

The recorded environment is not a substitute for running the tests on the machine and Python version used for submission. See `docs/test_results.txt` and `docs/validation_numbers.txt` for the saved outputs, if these files are present.

## Recorded test coverage

The project notes report the following:

- Algorithm and edge-case tests are available under `tests/`.
- Loader tests used generated PNG, JPEG, and BMP byte data.
- UI flows were exercised with bundled sample images using Streamlit AppTest and Playwright screenshots.

These records describe the earlier test run. Run the commands below to check the current checkout:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

## Checks not recorded as completed

- **Project-wide code similarity:** No MOSS, JPlag, or equivalent full-project similarity run is recorded.
- **Exhaustive public-source search:** GitHub and other public repositories were not searched exhaustively.
- **Historical source comparison:** The earlier audit says that only two files from an earlier project archive were compared line by line. The exact upstream repository, commit, filenames, matching ranges, and reproducible before-and-after diff still need to be recorded in `docs/ORIGINALITY_REVIEW.md`.
- **Cross-platform testing:** Windows, macOS, and Python versions other than the recorded Linux/Python 3.12.3 environment were not tested in the recorded run.
- **Real browser upload with a user photo:** A real user-photo upload through the browser was not manually tested. The loader was tested with generated image bytes, and UI tests used bundled samples.

The earlier notes refer to a dependency installation in a clean virtual environment. Keep that claim only when the corresponding command and output can be produced from the test report; otherwise treat the clean-environment installation check as not independently verified.

## How to report a new validation run

For a new run, record:

1. Date and operating system.
2. Python version and installed dependency versions.
3. Exact command used.
4. Pass/fail result and test count.
5. Any skipped tests and the reason they were skipped.

Do not update the recorded environment above unless a new run actually took place.
