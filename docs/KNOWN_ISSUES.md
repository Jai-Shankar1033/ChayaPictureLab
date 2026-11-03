# Known issues and software limitations

This page describes known limitations of the application. Testing coverage and release/licensing tasks are tracked separately in [Validation status](VALIDATION_STATUS.md).

## Processing limitations

1. **Mode filter performance.** The mode filter becomes slower as the number of distinct grey levels increases. In the recorded measurement on a random 1024 × 768 image, it took about 2.7 seconds for grayscale input and 8 seconds for colour input. These are observations from one test environment, not performance guarantees; timings will vary with hardware and input data.

2. **Mode filtering is not a good general-purpose denoiser for continuous-tone photos.** The mode filter works best when neighbourhoods contain repeated values. In one recorded 5% salt-and-pepper noise experiment, the mode-filter result measured 22.7 dB PSNR, compared with 39.0 dB for the median-filter result. This is an example from the tested sample, not a result that should be expected for every image.

3. **Adaptive threshold comparison.** The implementation uses the exact local mean. OpenCV rounds the local mean to an integer, so the two methods can differ on some interior pixels. The recorded comparison found differences on approximately 2–7% of interior pixels in the tested natural-looking images. The expected rounding difference is covered in `tests/test_histogram.py`.

4. **Canny threshold settings are not directly interchangeable with OpenCV.** This implementation expresses its thresholds as fractions of the maximum thinned gradient. OpenCV uses absolute threshold values. The resulting edge maps can be compared, but agreement is approximate rather than pixel-identical. See `docs/validation_numbers.txt` for the recorded comparison, if that file is present in the repository.

5. **Colour histogram equalization is not provided.** Equalizing the red, green, and blue channels independently can shift colours. For this operation, colour input is converted to grayscale first, and the interface explains this behaviour.

6. **Input resizing and geometric operations.** Images are reduced during loading when their longest side exceeds the configured maximum; the default maximum is 1024 pixels. General geometric processing operations such as resize, rotate, and flip are outside the current project scope. Resizing during loading is an input-size safeguard, not a general-purpose resize operation.

7. **Session history is temporary.** Experiment history is stored in browser-session memory. Refreshing or ending the session clears that history. Download the JSON history or export the HTML report before ending a session when a permanent copy is needed.

## Reporting a problem

When reporting an issue, include the operation name, input image dimensions and colour mode, parameter values, Python/package versions, and the steps needed to reproduce the result. Do not include private images unless you are comfortable sharing them.
