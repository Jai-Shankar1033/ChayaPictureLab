"""Compare our manual implementations with OpenCV on the bundled samples.

Run:  python tools/validate_against_opencv.py   (needs opencv-python-headless)
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chayalab import edges as E, filters as F, histogram as H, metrics as M, noise as N, reference as ref  # noqa: E402
from chayalab.colorspace import to_grayscale  # noqa: E402
from chayalab.io_utils import load_image  # noqa: E402

print(f"Manual implementations vs OpenCV {cv2.__version__}, NumPy {np.__version__}\n")
for name in ["scene.png", "low_contrast.png", "texture.png", "shapes.png"]:
    g = to_grayscale(load_image((ROOT / "samples" / name).read_bytes())[0])
    eq = int(np.abs(H.equalize(g).astype(int) - cv2.equalizeHist(g).astype(int)).max())
    ad = (H.adaptive_threshold(g, 11, 2.0)[5:-5, 5:-5] ==
          cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)[5:-5, 5:-5]).mean()
    ga = int(np.abs(F.gaussian_filter(g, 1.5, 9).astype(int) -
                    cv2.GaussianBlur(g, (9, 9), 1.5, borderType=cv2.BORDER_REFLECT_101).astype(int)).max())
    me = (F.median_filter(g, 5)[3:-3, 3:-3] == cv2.medianBlur(g, 5)[3:-3, 3:-3]).mean()
    sx = np.allclose(E.gradients(g, "sobel")["gx"],
                     cv2.Sobel(g, cv2.CV_64F, 1, 0, ksize=3, borderType=cv2.BORDER_REPLICATE))
    ours = E.canny(g, 1.4, 0.1, 0.3)["edges"] > 0
    tol = cv2.dilate(((cv2.Canny(g, 40, 120) > 0) * 255).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    cn = (ours & tol).sum() / max(1, ours.sum())
    print(f"{name:17s} equalize max|diff|={eq} | Otsu ours/OpenCV={H.otsu_threshold(g)}/{ref.opencv_otsu_threshold(g)} | "
          f"adaptive agree={ad * 100:.2f}% | gaussian max|diff|={ga} | median interior equal={me * 100:.1f}% | "
          f"Sobel Gx identical={sx} | our Canny pixels within 2 px of cv2.Canny={cn * 100:.1f}%")

g = to_grayscale(load_image((ROOT / "samples" / "scene.png").read_bytes())[0])
print("\nRestoration on scene.png (grayscale), seed 42")
sp = N.salt_pepper_noise(g, 0.05, seed=42)
gn = N.gaussian_noise(g, 25, seed=42)
filters = {"mean 3x3": lambda x: F.mean_filter(x, 3), "median 3x3": lambda x: F.median_filter(x, 3),
           "mode 3x3": lambda x: F.mode_filter(x, 3), "gaussian s=1.2": lambda x: F.gaussian_filter(x, 1.2)}
for title, noisy in (("salt & pepper 5 %", sp), ("Gaussian sigma 25", gn)):
    cells = [f"noisy {M.psnr(g, noisy):.2f}"] + [f"{k} {M.psnr(g, f(noisy)):.2f}" for k, f in filters.items()]
    print(f"  PSNR (dB), {title}: " + " | ".join(cells))
print(f"  mode vs median output differ on {(F.mode_filter(sp, 3) != F.median_filter(sp, 3)).mean() * 100:.1f} % of pixels (S&P image)")
