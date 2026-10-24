"""Shared transparent prayer emblems, recolored for the current theme."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPixmap, QColor


ASSETS = Path(__file__).parent / "assets" / "calligraphy"


@lru_cache(maxsize=5)
def _source(prayer):
    image = QPixmap(str(ASSETS / f"{prayer.lower()}.png"))
    if image.isNull():
        return image
    return image.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)


@lru_cache(maxsize=32)
def emblem(prayer, color):
    image = _source(prayer).copy()
    if image.isNull():
        return image
    painter = QPainter(image)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), QColor(color))
    painter.end()
    return image


def draw_emblem(painter, prayer, rect, color):
    image = emblem(prayer, color)
    if image.isNull():
        return False
    size = image.size().scaled(rect.size().toSize(), Qt.AspectRatioMode.KeepAspectRatio)
    target = QRectF(0, 0, size.width(), size.height())
    target.moveCenter(rect.center())
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.drawPixmap(target, image, QRectF(image.rect()))
    painter.restore()
    return True
