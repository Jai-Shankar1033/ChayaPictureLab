"""Generate the bundled sample images (deterministic, created from scratch with NumPy).

Run:  python tools/make_samples.py
Because the images are synthetic, there are no third-party copyright concerns.
"""
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[1] / "samples"
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(2026)
H, W = 360, 480
yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)


def save(name, arr):
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(OUT / name)


# 1. scene: sky gradient, sun, hills, a house, texture -> colour image with edges, smooth areas and texture
scene = np.zeros((H, W, 3))
scene[..., 0] = 90 + 110 * (yy / H)
scene[..., 1] = 140 + 80 * (yy / H)
scene[..., 2] = 230 - 40 * (yy / H)
sun = (xx - 380) ** 2 + (yy - 70) ** 2 < 35 ** 2
scene[sun] = (255, 220, 80)
hill = yy > 250 + 25 * np.sin(xx / 45.0)
scene[hill] = (60, 140, 70)
house = (xx > 120) & (xx < 260) & (yy > 190) & (yy < 300)
scene[house] = (190, 90, 70)
scene[(yy >= 140) & (yy <= 190) & (np.abs(xx - 190) < (yy - 140) * 2.8 + 5)] = (110, 50, 40)
scene[(xx > 175) & (xx < 205) & (yy > 240) & (yy < 300)] = (70, 40, 30)
scene[(xx > 140) & (xx < 165) & (yy > 215) & (yy < 240)] = (240, 235, 150)
scene += rng.normal(0, 3, scene.shape)
save("scene.png", scene)

# 2. shapes: clean black/white objects for morphology + thresholding (with a few specks and holes)
shapes = np.zeros((H, W))
shapes[60:200, 50:190] = 255
shapes[(xx - 330) ** 2 + (yy - 130) ** 2 < 70 ** 2] = 255
shapes[230:330, 120:360] = 255
shapes[100:120, 90:110] = 0                       # hole inside the square
shapes[270:285, 200:215] = 0                      # hole inside the bar
for _ in range(45):                               # isolated one-to-two pixel specks
    y, x = rng.integers(5, H - 5), rng.integers(5, W - 5)
    shapes[y:y + 2, x:x + 2] = 255
save("shapes.png", shapes)

# 3. low-contrast: the scene squeezed into 90..150 (good for stretching / equalization)
gray = scene.mean(axis=2)
save("low_contrast.png", 90 + (gray - gray.min()) / (gray.max() - gray.min()) * 60)

# 4. checker + gradient texture for edge/filter experiments
tex = ((xx // 40 + yy // 40) % 2) * 160 + 40 + 40 * np.sin(xx / 25.0)
save("texture.png", tex + rng.normal(0, 4, tex.shape))
print("wrote", sorted(p.name for p in OUT.glob("*.png")))
