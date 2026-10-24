"""Draw an original, compact dawn-prayer monogram from Arabic outlines and pen strokes."""
from pathlib import Path
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QFont, QFontDatabase, QPainter, QPainterPath, QPainterPathStroker, QPixmap, QTransform
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent

def stroke(start, segments):
    path = QPainterPath(QPointF(*start))
    for coordinates in segments:
        path.cubicTo(*coordinates)
    path.closeSubpath()
    return path

def main():
    app = QApplication.instance() or QApplication([])
    QFontDatabase.addApplicationFont(str(ROOT / "namazflow/fonts/Amiri-Regular.ttf"))
    body = QPainterPath()
    face = QFont("Amiri")
    face.setPixelSize(330)
    body.addText(QPointF(0, 0), face, "فجر")
    body.setFillRule(Qt.FillRule.WindingFill)
    body = QTransform().rotate(-8).map(body)
    bounds = body.boundingRect()
    transform = QTransform()
    transform.translate(145, 420)
    transform.scale(600 / bounds.width(), 350 / bounds.height())
    transform.translate(-bounds.x(), -bounds.y())
    body = transform.map(body)

    # The article's alif and lam form the tall crown, flowing into the shaped body.
    alif = stroke((820, 120), [
        (792, 198, 825, 290, 842, 350),
        (876, 472, 886, 618, 810, 739),
        (833, 626, 821, 489, 799, 384),
        (779, 288, 767, 209, 820, 120),
    ])
    lam = stroke((682, 70), [
        (633, 157, 714, 296, 726, 431),
        (746, 581, 691, 674, 548, 698),
        (437, 717, 349, 678, 328, 625),
        (381, 678, 500, 656, 574, 620),
        (682, 571, 690, 500, 671, 394),
        (655, 296, 605, 195, 634, 137),
        (648, 109, 666, 91, 682, 70),
    ])
    loop = stroke((650, 147), [
        (605, 252, 482, 321, 449, 405),
        (426, 464, 452, 508, 484, 534),
        (424, 508, 407, 455, 428, 400),
        (457, 320, 590, 245, 650, 147),
    ])
    tail = stroke((189, 669), [
        (142, 755, 252, 845, 431, 844),
        (642, 842, 797, 714, 820, 590),
        (813, 760, 665, 904, 433, 900),
        (258, 897, 114, 810, 150, 724),
        (161, 699, 176, 682, 189, 669),
    ])
    image = QPixmap(1024, 1024)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(512, 512)
    painter.scale(1.08, 1.08)
    painter.translate(-512, -512)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush("#DBAE67")
    for path in (alif, loop, lam, tail):
        painter.drawPath(path)
    # Fine open channels preserve the word and its dots where the pen strokes weave.
    separator = QPainterPathStroker()
    separator.setWidth(13)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    painter.drawPath(separator.createStroke(body).united(body))
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    painter.drawPath(body)
    painter.end()
    preview = ROOT / "qa-artifacts/fajr-native-refined.png"
    preview.parent.mkdir(exist_ok=True)
    image.save(str(preview))

if __name__ == "__main__":
    main()
