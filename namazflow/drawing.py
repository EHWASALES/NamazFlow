"""Scalable vector artwork for the NamazFlow desktop companion."""

import math
from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen

GOLD = "#DBAE67"
TEAL = "#56E4CE"
WHITE = "#F6F1E9"
MUTED = "#A7ACB2"


def c(value: str, alpha: int = 255) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color


def font(size: float, weight: int = 400, family: str = "Segoe UI") -> QFont:
    result = QFont(family)
    result.setPointSizeF(size)
    result.setWeight(
        QFont.Weight.Bold
        if weight >= 600
        else (QFont.Weight.Medium if weight >= 500 else QFont.Weight.Normal)
    )
    return result


def draw_text(
    p: QPainter,
    x: float,
    y: float,
    txt: str,
    size=12,
    color=WHITE,
    weight=400,
    family="Segoe UI",
    align=None,
    width=300,
    italic=False,
):
    text_font = font(size, weight, family)
    text_font.setItalic(italic)
    p.setFont(text_font)
    p.setPen(c(color))
    p.drawText(
        QRectF(x, y, width, 32),
        align or (Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
        txt,
    )


def round_rect(p: QPainter, rect: QRectF, radius: float, fill, stroke=None, line=1):
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    p.fillPath(path, fill)
    if stroke:
        p.setPen(QPen(stroke, line))
        p.drawPath(path)


def draw_symbol(p: QPainter, kind: str, x: float, y: float, size=25, color=GOLD):
    """Small, scalable vector symbols that stay crisp at 100–200% DPI."""
    p.save()
    p.translate(x, y)
    p.scale(size / 30, size / 30)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(c(color), 2.1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    if kind in ("sunrise", "sunset", "afternoon"):
        p.drawLine(-13, 8, 13, 8)
        p.drawArc(QRectF(-8, 0, 16, 16), 0, 180 * 16)
        for a in (0, 45, 90, 135, 180):
            ang = math.radians(a)
            p.drawLine(
                round(math.cos(ang) * 10),
                round(8 - math.sin(ang) * 10),
                round(math.cos(ang) * 13),
                round(8 - math.sin(ang) * 13),
            )
        if kind == "sunrise":
            p.drawLine(-13, 12, -5, 12)
            p.drawLine(5, 12, 13, 12)
        if kind == "sunset":
            p.drawLine(-13, 13, 13, 13)
    elif kind == "sun":
        p.drawEllipse(QRectF(-7, -7, 14, 14))
        for a in range(0, 360, 45):
            ang = math.radians(a)
            p.drawLine(
                round(math.cos(ang) * 11),
                round(math.sin(ang) * 11),
                round(math.cos(ang) * 14),
                round(math.sin(ang) * 14),
            )
    elif kind == "crescent":
        outer = QPainterPath()
        outer.addEllipse(QRectF(-13, -13, 26, 26))
        inner = QPainterPath()
        inner.addEllipse(QRectF(-3, -17, 23, 25))
        p.setPen(Qt.PenStyle.NoPen)
        p.fillPath(outer.subtracted(inner), c(color))
        star = QPainterPath()
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            radius = 3.6 if i % 2 == 0 else 1.6
            xx, yy = 11 + math.cos(angle) * radius, -7 + math.sin(angle) * radius
            if i == 0:
                star.moveTo(xx, yy)
            else:
                star.lineTo(xx, yy)
        star.closeSubpath()
        p.fillPath(star, c(color))
    elif kind == "star":
        path = QPainterPath()
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            radius = 13 if i % 2 == 0 else 5.6
            point = QPoint(int(math.cos(angle) * radius), int(math.sin(angle) * radius))
            if i == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        path.closeSubpath()
        p.setBrush(c(color, 170))
        p.drawPath(path)
    elif kind == "mosque":
        p.drawLine(-14, 12, 14, 12)
        p.drawLine(-9, 12, -9, 1)
        p.drawArc(QRectF(-9, -10, 18, 22), 0, 180 * 16)
        p.drawLine(9, 12, 9, 1)
        p.setBrush(c(color))
        p.drawRect(QRectF(12, -7, 3, 19))
        cap = QPainterPath()
        cap.moveTo(11, -7)
        cap.lineTo(13.5, -14)
        cap.lineTo(16, -7)
        cap.closeSubpath()
        p.drawPath(cap)
    elif kind == "lantern":
        p.drawLine(0, -14, 0, -11)
        p.drawLine(-5, -11, 5, -11)
        p.drawLine(-8, -9, 8, -9)
        p.drawLine(-8, -9, -10, 7)
        p.drawLine(8, -9, 10, 7)
        p.drawLine(-10, 7, 10, 7)
        p.drawLine(-7, 11, 7, 11)
        p.drawEllipse(QRectF(-3, -6, 6, 11))
    p.restore()


def mosque_etching(p: QPainter, x: float, y: float, scale: float = 1.0):
    """Etched domes/minaret from the approved concept; no external font/assets."""
    p.save()
    p.translate(x, y)
    p.scale(scale, scale)
    p.setPen(QPen(c(GOLD, 72), 1.0))
    p.setBrush(c(GOLD, 23))
    dome = QPainterPath()
    dome.moveTo(-41, 0)
    dome.lineTo(-41, -17)
    dome.cubicTo(-40, -35, -27, -47, -3, -54)
    dome.cubicTo(20, -47, 33, -34, 35, -17)
    dome.lineTo(35, 0)
    dome.closeSubpath()
    p.drawPath(dome)
    p.drawLine(-2, -54, -2, -71)
    p.drawEllipse(QRectF(-5, -76, 6, 6))
    for xx in (-26, -5, 16):
        p.drawArc(QRectF(xx, -20, 13, 20), 0, 180 * 16)
    minaret = QPainterPath()
    minaret.moveTo(43, 1)
    minaret.lineTo(43, -68)
    minaret.lineTo(40, -68)
    minaret.lineTo(40, -72)
    minaret.lineTo(53, -72)
    minaret.lineTo(53, -68)
    minaret.lineTo(50, -68)
    minaret.lineTo(50, 1)
    minaret.closeSubpath()
    p.drawPath(minaret)
    p.drawLine(39, -81, 54, -81)
    p.drawLine(46, -81, 46, -98)
    p.drawEllipse(QRectF(44, -103, 4, 4))
    p.restore()


def rosette_etching(p: QPainter, x: float, y: float, size: float = 44):
    """Eightfold geometric gold filigree, masked by the parent panel."""
    p.save()
    p.translate(x, y)
    p.setPen(QPen(c(GOLD, 40), 1.1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    for angle in (0, 45, 90, 135):
        p.save()
        p.rotate(angle)
        p.drawRect(QRectF(-size * 0.5, -size * 0.5, size, size))
        p.restore()
    p.drawEllipse(QRectF(-size * 0.51, -size * 0.51, size * 1.02, size * 1.02))
    p.drawEllipse(QRectF(-size * 0.33, -size * 0.33, size * 0.66, size * 0.66))
    p.restore()


def current_palette(name: str):
    if name == "emerald":
        return {
            "panel": "#102B2A",
            "row": "#1A3B39",
            "halo": "#245B4F",
            "accent": "#60E6C7",
        }
    if name == "sand":
        return {
            "panel": "#312923",
            "row": "#40342A",
            "halo": "#70543F",
            "accent": "#E8B872",
        }
    return {"panel": "#161D24", "row": "#203137", "halo": "#1F4F51", "accent": TEAL}
