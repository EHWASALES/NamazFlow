"""Generate a crisp, proprietary-free Windows ICO in multiple resolutions.

Source of truth is this vector-like Pillow drawing recipe.
Run before PyInstaller; do not commit generated binary assets.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def draw_icon(size=512):
    s = 4
    w = size * s
    image = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    p = ImageDraw.Draw(image)
    ring = int(w * .043)
    center = w // 2
    radius = int(w * .46)
    p.ellipse((center-radius, center-radius, center+radius, center+radius),
              fill="#192830", outline="#C9A061", width=max(1, int(w*.012)))
    p.arc((center-radius+ring, center-radius+ring, center+radius-ring, center+radius-ring),
          start=265, end=335, fill="#57E8CD", width=max(1, int(w*.028)))
    # Gold crescent: erase only from the moon layer (not from dark background).
    moon = Image.new("RGBA", (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(moon)
    d.ellipse((int(w*.265), int(w*.25), int(w*.675), int(w*.66)), fill="#E7BE7B")
    d.ellipse((int(w*.39), int(w*.19), int(w*.735), int(w*.58)), fill=(0,0,0,0))
    image.alpha_composite(moon)
    p = ImageDraw.Draw(image)
    gold = "#F2C98C"
    p.polygon([(int(w*.68), int(w*.67)), (int(w*.68), int(w*.44)),
               (int(w*.735), int(w*.38)), (int(w*.79), int(w*.44)),
               (int(w*.79), int(w*.67))], fill=gold)
    p.line([(int(w*.735), int(w*.38)), (int(w*.735), int(w*.285))],
           fill=gold, width=max(2, int(w*.011)))
    p.ellipse((int(w*.72), int(w*.274), int(w*.75), int(w*.304)), fill=gold)
    p.rectangle((int(w*.64), int(w*.665), int(w*.83), int(w*.69)), fill=gold)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(ASSETS / "namazflow.png")
    icon.save(ASSETS / "namazflow.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    print(f"Created {ASSETS / 'namazflow.ico'}")


if __name__ == "__main__":
    main()
