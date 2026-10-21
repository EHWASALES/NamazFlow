"""Generate a crisp, proprietary-free Windows ICO in multiple resolutions.

Source of truth is this vector-like Pillow drawing recipe.
Run before PyInstaller; do not commit generated binary assets.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def draw_icon(size=512):
    s = 4
    w = size * s
    image = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    p = ImageDraw.Draw(image)
    ring = int(w * 0.043)
    center = w // 2
    radius = int(w * 0.46)
    p.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        fill="#192830",
        outline="#C9A061",
        width=max(1, int(w * 0.012)),
    )
    p.arc(
        (
            center - radius + ring,
            center - radius + ring,
            center + radius - ring,
            center + radius - ring,
        ),
        start=265,
        end=335,
        fill="#57E8CD",
        width=max(1, int(w * 0.028)),
    )
    # Gold crescent: erase only from the moon layer (not from dark background).
    moon = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(moon)
    d.ellipse(
        (int(w * 0.265), int(w * 0.25), int(w * 0.675), int(w * 0.66)), fill="#E7BE7B"
    )
    d.ellipse(
        (int(w * 0.39), int(w * 0.19), int(w * 0.735), int(w * 0.58)), fill=(0, 0, 0, 0)
    )
    image.alpha_composite(moon)
    # Five-point star beside the crescent; no crossed minaret strokes.
    import math

    p = ImageDraw.Draw(image)
    points = []
    for i in range(10):
        angle = math.pi * i / 5 - math.pi / 2
        radius = w * (0.068 if i % 2 == 0 else 0.030)
        points.append(
            (
                int(w * 0.70 + math.cos(angle) * radius),
                int(w * 0.34 + math.sin(angle) * radius),
            )
        )
    p.polygon(points, fill="#F2C98C")
    return image.resize((size, size), Image.Resampling.LANCZOS)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(ASSETS / "namazflow.png")
    icon.save(
        ASSETS / "namazflow.ico",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )
    print(f"Created {ASSETS / 'namazflow.ico'}")


if __name__ == "__main__":
    main()
