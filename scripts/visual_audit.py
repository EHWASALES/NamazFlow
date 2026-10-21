"""Three-stage reproducible visual QA for the actual PySide6 widget.

Run in a desktop/CI Qt environment:
  QT_QPA_PLATFORM=offscreen python scripts/visual_audit.py
Optionally compare to an exported crop of the approved concept:
  python scripts/visual_audit.py --reference-image docs/concept-panel.png

Reports screenshot metrics and reference proximity, NOT an unearned pixel-perfect claim.
"""
import argparse
from datetime import datetime, time, timedelta
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication
from namazflow.prayers import PrayerDay
from namazflow.ui import NamazWidget

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "qa-artifacts"
OUT.mkdir(exist_ok=True)
ZONE = ZoneInfo("Europe/Berlin")


def sample_days(day):
    hour = ((6, 11), (12, 46), (15, 42), (18, 11), (19, 32))
    keys = ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
    result = []
    for delta in (-1, 0, 1):
        d = day + timedelta(days=delta)
        times = {key: datetime.combine(d, time(*part), tzinfo=ZONE)
                 for key, part in zip(keys, hour)}
        result.append(PrayerDay(d, "Europe/Berlin", times, "09-05-1448"))
    return result


def measure(image: Image.Image):
    image = image.convert("RGBA")
    pixels = list(image.getdata())
    visible = [x for x in pixels if x[3] > 100]
    if not visible:
        return dict(visible_pixels=0, dark_fraction=0, gold_pixels=0, teal_pixels=0)
    dark = sum(max(r, g, b) < 100 for r, g, b, a in visible)
    gold = sum(r > 125 and r > g * 1.15 and g > b * 1.15 for r, g, b, a in visible)
    teal = sum(g > r * 1.3 and b > r * 1.1 and g > 90 for r, g, b, a in visible)
    return dict(
        visible_pixels=len(visible),
        dark_fraction=round(dark / len(visible), 3),
        gold_pixels=gold, teal_pixels=teal,
    )


def reference_characteristics(path):
    image = Image.open(path).convert("RGB")
    # Crop the expanded panel from the original 1672x941 concept composition.
    # With panel-only image supplied, avoid cropping.
    if image.width > image.height * 1.35:
        image = image.crop((int(image.width * 0.675), int(image.height * 0.075),
                            int(image.width * 0.925), int(image.height * 0.77)))
    metrics = measure(image.convert("RGBA"))
    return metrics



def save_reference_comparison(reference_path, screenshot_path):
    """Export transparent side-by-side evidence, no false similarity score."""
    reference = Image.open(reference_path).convert("RGB")
    if reference.width > reference.height * 1.35:
        reference = reference.crop(
            (int(reference.width * .675), int(reference.height * .075),
             int(reference.width * .925), int(reference.height * .77)))
    before = reference.resize((426, 666))
    actual = Image.open(screenshot_path).convert("RGBA")
    backdrop = Image.new("RGBA", actual.size, "#283743")
    backdrop.alpha_composite(actual)
    rendered = backdrop.crop((128, 39, 554, 635)).convert("RGB").resize((426, 666))
    paired = Image.new("RGB", (900, 720), "#EBEAEB")
    paired.paste(before, (12, 42))
    paired.paste(rendered, (462, 42))
    painter = ImageDraw.Draw(paired)
    painter.text((15, 15), "APPROVED CONCEPT / ORIGINAL", fill="#172028")
    painter.text((467, 15), "ACTUAL QT WIDGET / CURRENT DESIGN", fill="#172028")
    destination = OUT / "reference-vs-qt.png"
    paired.save(destination)
    return str(destination)

def evaluate(label, img, target, reference=None):
    values = measure(img)
    goals = {
        "transparent_background": img.getpixel((0, 0))[3] < 15,
        "dark_glass": values["dark_fraction"] > (0.60 if target == "panel" else 0.35),
        "gold_detail": values["gold_pixels"] > (65 if target == "panel" else 20),
        "teal_accent": values["teal_pixels"] > (70 if target == "panel" else 20),
        "content_visible": values["visible_pixels"] > (90000 if target == "panel" else 3000),
    }
    outcome = {"stage": label, "metrics": values, "checks": goals,
               "pass": all(goals.values())}
    if reference and target == "panel":
        # Palette distance only; concept screenshot has photographic background.
        outcome["concept_palette_comparison"] = {
            "reference": reference,
            "difference_dark_fraction": round(abs(values["dark_fraction"] - reference["dark_fraction"]), 3),
            "method": "Dark-area ratio only; not an image similarity score",
        }
    return outcome


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument("--reference-image", type=Path)
    arg.add_argument("--strict", action="store_true", help="Return failure for QA gates")
    options = arg.parse_args()
    app = QApplication.instance() or QApplication(sys.argv)
    old_refresh = NamazWidget.refresh
    NamazWidget.refresh = lambda self: None
    try:
        window = NamazWidget()
    finally:
        NamazWidget.refresh = old_refresh
    window.tick.stop()
    date = datetime.now(ZONE).date()
    window._now = lambda: datetime.combine(date, time(16, 47), tzinfo=ZONE)
    window.days = sample_days(date)
    window.error = ""
    window.online = True
    window._demo = True
    window.move(50, 50)
    window.show()
    app.processEvents()
    ref = reference_characteristics(options.reference_image) if options.reference_image else None
    rows = []
    # Pass 1: the collapsed floating icon, its translucency, vector and time ring.
    p1 = OUT / "iteration-1-floating-orb.png"
    window.grab().save(str(p1))
    rows.append(evaluate("1 · Floating symbol", Image.open(p1), "orb", ref))
    # Pass 2: expanded layout, typography, spacing and five-prayer hierarchy.
    window.toggle()
    app.processEvents()
    p2 = OUT / "iteration-2-expanded-panel.png"
    window.grab().save(str(p2))
    rows.append(evaluate("2 · Concept glass panel", Image.open(p2), "panel", ref))
    # Pass 3: personalization and a repeat readability/palette check.
    window.settings["icons"]["Asr"] = "lantern"
    window.settings["symbol"] = "mosque"
    window.update()
    app.processEvents()
    p3 = OUT / "iteration-3-custom-symbols.png"
    window.grab().save(str(p3))
    rows.append(evaluate("3 · Final customizable UI", Image.open(p3), "panel", ref))
    comparison = save_reference_comparison(options.reference_image, p3) if options.reference_image else None
    report = {
        "comparison_image": comparison,
        "mode": "DEMONSTRATION – screenshot prayer times are not live",
        "concept": "Approved NamazFlow gold / teal / dark floating widget",
        "reference_image_provided": bool(ref),
        "limitations": [
            "Palette/structural checks are not human visual sign-off.",
            "A true screenshot-to-original comparison requires supplying the approved source image.",
            "Always-on-top, tray, autostart and DPI require validation on Windows.",
        ],
        "stages": rows,
    }
    (OUT / "visual-qa.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    window.hide()
    window.tray.hide()
    if options.strict and not all(r["pass"] for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
