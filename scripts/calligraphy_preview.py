"""Capture the real prayer emblems and a deterministic orb transition demo."""

from datetime import datetime, time
from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFontDatabase, QPainter, QPixmap, QImage
from PySide6.QtWidgets import QApplication

from namazflow.calligraphy import draw_emblem
from namazflow.drawing import GOLD, c, font
from namazflow.prayers import LABELS, PRAYERS
from namazflow.quotes import Quote
from namazflow.ui import NamazWidget
from scripts.visual_audit import ZONE, sample_days


OUT = Path(__file__).resolve().parent.parent / "qa-artifacts"


def main():
    app = QApplication.instance() or QApplication([])
    for name in ("segoeui.ttf", "georgia.ttf"):
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    OUT.mkdir(exist_ok=True)
    sheet = QPixmap(1000, 280)
    sheet.fill(c("#14252C"))
    p = QPainter(sheet)
    for index, prayer in enumerate(PRAYERS):
        draw_emblem(p, prayer, QRectF(index * 200 + 20, 12, 160, 195), GOLD)
        p.setPen(c("#E6D3AF"))
        p.setFont(font(13))
        p.drawText(QRectF(index * 200, 225, 200, 28), Qt.AlignmentFlag.AlignCenter, LABELS[prayer])
    p.end()
    sheet.save(str(OUT / "calligraphy-emblems.png"))

    NamazWidget.refresh = lambda self: None
    NamazWidget.load_quote = lambda self: None
    w = NamazWidget()
    for timer in (w.tick, w.motion, w.quote_timer):
        timer.stop()
    w.settings.update(animations=False, calligraphy=True, quote=True, location="darmstadt")
    w.panel.sync_city()
    day = datetime.now(ZONE).date()
    w.days = sample_days(day)
    w._now = lambda: datetime.combine(day, time(16, 47), tzinfo=ZONE)
    w.error = ""
    w._quote_received(Quote("Beispieltext zur Prüfung der vollständigen Anzeige. " * 9,
                            "DEMO · kein religiöses Zitat", "https://example.com",
                            "quran", "Testdaten"), "", w._quote_generation)
    w.show()
    w.open_panel()
    w.panel.setFixedHeight(960)
    app.processEvents()
    w.panel.grab().save(str(OUT / "calligraphy-panel-v2.png"))
    w.settings["animations"] = True
    frames = []
    w._set_orb_prayer("Isha")
    for prayer in PRAYERS:
        w._next = lambda prayer=prayer: (prayer, w._now(), 4500, 0.65)
        w._set_orb_prayer(prayer)
        for step in range(26):
            w.emblem_animation.setCurrentTime(min(step * 50, 650))
            capture = w.grab().scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
            image = capture.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
            raw = Image.frombytes("RGBA", (image.width(), image.height()), image.bits().tobytes())
            background = Image.new("RGBA", raw.size, "#14252C")
            background.alpha_composite(raw)
            frames.append(background.convert("RGB"))
    frames[0].save(OUT / "orb-transition.gif", save_all=True, append_images=frames[1:],
                   duration=50, loop=0, disposal=2)
    w.collapse()
    w.hide()
    w.tray.hide()


if __name__ == "__main__":
    main()
