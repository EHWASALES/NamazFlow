"""Pixel-drawn floating desktop interface for NamazFlow.

No paid fonts, external images or browser dependencies are required.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
import math
import sys
import threading
from zoneinfo import ZoneInfo

from PySide6.QtCore import Qt, QPoint, QRectF, Signal, QTimer, QEvent
from PySide6.QtGui import (
    QColor, QBrush, QFont, QIcon, QLinearGradient, QPainter, QPainterPath,
    QPen, QPixmap, QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QMenu,
    QMessageBox, QSystemTrayIcon, QVBoxLayout, QWidget,
)
from .config import SYMBOLS, THEMES, data_path, load, save, set_windows_autostart
from .prayers import METHODS, PRAYERS, countdown_text, current_prayer, get_day, next_prayer

GOLD = "#DBAE67"
TEAL = "#56E4CE"
WHITE = "#F6F1E9"
MUTED = "#A7ACB2"
ICONS = ("sunrise", "sun", "afternoon", "sunset", "crescent", "mosque", "star", "lantern")
DEFAULT_ICONS = dict(zip(PRAYERS, ICONS[:5]))
QUOTES = {
    "Fajr": ("Mit dem Morgen beginnt eine neue Möglichkeit.", "Erinnerung"),
    "Dhuhr": ("Und verrichte das Gebet zu Meinem Gedenken.", "Koran 20:14 – sinngemäß"),
    "Asr": ("Gewiss, im Gedenken Allahs finden die Herzen Ruhe.", "Koran 13:28 – sinngemäß"),
    "Maghrib": ("Gewiss, im Gedenken Allahs finden die Herzen Ruhe.", "Koran 13:28 – sinngemäß"),
    "Isha": ("Und Er ist es, Der die Nacht zum Ruhen machte.", "Koran 6:96 – sinngemäß"),
}
MONTHS = ("Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember")
WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")


def c(value: str, alpha: int = 255) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color


def font(size: float, weight: int = 400, family: str = "Segoe UI") -> QFont:
    result = QFont(family)
    result.setPointSizeF(size)
    result.setWeight(QFont.Weight.Bold if weight >= 600 else (QFont.Weight.Medium if weight >= 500 else QFont.Weight.Normal))
    return result


def draw_text(p: QPainter, x: float, y: float, txt: str, size=12,
              color=WHITE, weight=400, family="Segoe UI", align=None, width=300):
    p.setFont(font(size, weight, family))
    p.setPen(c(color))
    p.drawText(QRectF(x, y, width, 32), align or (Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), txt)


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
            p.drawLine(round(math.cos(ang) * 10), round(8 - math.sin(ang) * 10),
                       round(math.cos(ang) * 13), round(8 - math.sin(ang) * 13))
        if kind == "sunrise":
            p.drawLine(-13, 12, -5, 12)
            p.drawLine(5, 12, 13, 12)
        if kind == "sunset":
            p.drawLine(-13, 13, 13, 13)
    elif kind == "sun":
        p.drawEllipse(QRectF(-7, -7, 14, 14))
        for a in range(0, 360, 45):
            ang = math.radians(a)
            p.drawLine(round(math.cos(ang) * 11), round(math.sin(ang) * 11),
                       round(math.cos(ang) * 14), round(math.sin(ang) * 14))
    elif kind == "crescent":
        path = QPainterPath()
        path.arcMoveTo(QRectF(-10, -12, 24, 24), 65)
        path.arcTo(QRectF(-10, -12, 24, 24), 65, 275)
        path.cubicTo(-8, 9, -3, -7, 3, -12)
        p.setBrush(c(color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(path)
    elif kind == "star":
        path = QPainterPath()
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            radius = 13 if i % 2 == 0 else 5.6
            point = QPoint(int(math.cos(angle) * radius), int(math.sin(angle) * radius))
            if i == 0: path.moveTo(point)
            else: path.lineTo(point)
        path.closeSubpath()
        p.setBrush(c(color, 170))
        p.drawPath(path)
    elif kind == "mosque":
        p.drawLine(-14, 12, 14, 12)
        p.drawLine(-9, 12, -9, 1)
        p.drawArc(QRectF(-9, -10, 18, 22), 0, 180 * 16)
        p.drawLine(9, 12, 9, 1)
        p.drawLine(12, 11, 12, -11)
        p.drawLine(10, -8, 14, -8)
        p.drawLine(12, -11, 12, -15)
        p.drawEllipse(QRectF(-1, -15, 2, 2))
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


def current_palette(name: str):
    if name == "emerald":
        return {"panel": "#102B2A", "row": "#1A3B39", "halo": "#245B4F", "accent": "#60E6C7"}
    if name == "sand":
        return {"panel": "#312923", "row": "#40342A", "halo": "#70543F", "accent": "#E8B872"}
    return {"panel": "#161D24", "row": "#203137", "halo": "#1F4F51", "accent": TEAL}


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NamazFlow · Einstellungen")
        self.setMinimumWidth(390)
        self.setStyleSheet("""
          QDialog { background:#182127; color:#F6F1E9; }
          QLabel, QCheckBox { color:#EDE5D8; font:12px 'Segoe UI'; }
          QLineEdit, QComboBox { padding:9px; background:#26343B;
            border:1px solid #465157; border-radius:7px; color:white; }
          QPushButton { background:#267267; color:white; padding:10px;
            border-radius:7px; min-width:82px; }
        """)
        layout = QVBoxLayout(self)
        title = QLabel("Gebetszeiten & Erscheinungsbild")
        title.setStyleSheet("font: 600 19px 'Segoe UI'; color:#DBAE67; margin-bottom:10px;")
        layout.addWidget(title)
        form = QFormLayout()
        self.city = QLineEdit(config["city"])
        self.country = QLineEdit(config["country"])
        self.method = QComboBox()
        for key, value in METHODS.items():
            self.method.addItem(value, key)
        self.method.setCurrentIndex(max(0, self.method.findData(config["method"])))
        self.school = QComboBox()
        self.school.addItem("Hanafi", 1)
        self.school.addItem("Shafi / Standard", 0)
        self.school.setCurrentIndex(max(0, self.school.findData(config["school"])))
        self.theme = QComboBox()
        for value, label in (("midnight", "Mitternacht · Gold & Türkis"),
                             ("emerald", "Smaragd"), ("sand", "Sand & Bronze")):
            self.theme.addItem(label, value)
        self.theme.setCurrentIndex(max(0, self.theme.findData(config["theme"])))
        self.symbol = QComboBox()
        for value, label in (("crescent", "Halbmond"), ("mosque", "Moschee"),
                             ("star", "Stern"), ("lantern", "Laterne")):
            self.symbol.addItem(label, value)
        self.symbol.setCurrentIndex(max(0, self.symbol.findData(config["symbol"])))
        form.addRow("Stadt", self.city)
        form.addRow("Land (Englisch)", self.country)
        form.addRow("Berechnungsmethode", self.method)
        form.addRow("Asr-Rechtsschule", self.school)
        form.addRow("Design", self.theme)
        form.addRow("Schwebendes Symbol", self.symbol)
        layout.addLayout(form)
        self.notifications = QCheckBox("Dezente Gebetsbenachrichtigungen")
        self.notifications.setChecked(config["notifications"])
        self.autostart = QCheckBox("Mit Windows starten")
        self.autostart.setChecked(config["autostart"])
        self.quote = QCheckBox("Erinnerungsvers anzeigen")
        self.quote.setChecked(config["quote"])
        layout.addWidget(self.notifications)
        layout.addWidget(self.autostart)
        layout.addWidget(self.quote)
        note = QLabel("Zeiten können je nach Berechnungsmethode von deiner Moschee abweichen.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#B0B7BB; font-size:10px; margin:10px 0;")
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "city": self.city.text().strip(),
            "country": self.country.text().strip(),
            "method": self.method.currentData(),
            "school": self.school.currentData(),
            "theme": self.theme.currentData(),
            "symbol": self.symbol.currentData(),
            "notifications": self.notifications.isChecked(),
            "autostart": self.autostart.isChecked(),
            "quote": self.quote.isChecked(),
        }


class NamazWidget(QWidget):
    loaded = Signal(object, str, int)
    COLLAPSED = (108, 108)
    EXPANDED = (462, 732)

    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("NamazFlow")
        self.settings = load()
        self.days = []
        self.error = "Gebetszeiten werden geladen …"
        self.online = False
        self.expanded = False
        self._drag_start = None
        self._was_dragged = False
        self._generation = 0
        self._last_refresh = datetime.now()
        self._last_day = None
        self._loading = False
        self._last_notification = None
        self._demo = False
        self.loaded.connect(self._received)
        self._icon = self.make_icon()
        self.tray = QSystemTrayIcon(self._icon, self)
        self.tray.setToolTip("NamazFlow · Gebetszeiten")
        self.tray.activated.connect(lambda reason: self.toggle() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray_menu = self.menu()
        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()
        self.resize(*self.COLLAPSED)
        screen = QApplication.primaryScreen().availableGeometry()
        x = self.settings["x"] if self.settings["x"] is not None else screen.right() - 135
        y = self.settings["y"] if self.settings["y"] is not None else screen.top() + 55
        self.move(max(screen.left(), min(int(x), screen.right() - 108)),
                  max(screen.top(), min(int(y), screen.bottom() - 108)))
        self.tick = QTimer(self)
        self.tick.timeout.connect(self._tick)
        self.tick.start(1000)
        self.refresh()

    def make_icon(self) -> QIcon:
        icon = QPixmap(64, 64)
        icon.fill(Qt.GlobalColor.transparent)
        p = QPainter(icon)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(c("#16252A"))
        p.setPen(QPen(c(GOLD), 2))
        p.drawEllipse(QRectF(3, 3, 58, 58))
        draw_symbol(p, self.settings.get("symbol", "crescent"), 32, 32, 39, GOLD)
        p.end()
        return QIcon(icon)

    def menu(self):
        menu = QMenu()
        menu.addAction("Gebetszeiten anzeigen", self.toggle)
        menu.addAction("Einstellungen", self.configure)
        menu.addAction("Zeiten aktualisieren", self.refresh)
        menu.addSeparator()
        menu.addAction("NamazFlow beenden", QApplication.quit)
        return menu

    def toggle(self):
        self.expanded = not self.expanded
        if self.expanded:
            screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
            geo = screen.availableGeometry()
            self.move(max(geo.left(), min(self.x(), geo.right() - self.EXPANDED[0] + 1)),
                      max(geo.top(), min(self.y(), geo.bottom() - self.EXPANDED[1] + 1)))
        self.setFixedSize(*(self.EXPANDED if self.expanded else self.COLLAPSED))
        self.update()

    def refresh(self):
        self._generation += 1
        generation = self._generation
        config = dict(self.settings)
        self._last_refresh = datetime.now()
        self._loading = True
        self.error = "Aktualisiere Gebetszeiten …" if not self.days else self.error
        self.update()
        def task():
            days = []
            errors = []
            # Get three days so countdown works before Fajr and after Isha.
            now = datetime.now()
            for offset in (-1, 0, 1):
                try:
                    days.append(get_day(now.date() + timedelta(days=offset), config, data_path() / "cache"))
                except (ConnectionError, ValueError) as exc:
                    errors.append(str(exc))
            message = "; ".join(errors) if errors else ""
            self.loaded.emit(days, message, generation)
        threading.Thread(target=task, daemon=True).start()

    def _received(self, days, error: str, generation: int):
        if generation != self._generation:
            return
        self.days = days
        self._loading = False
        self.error = error
        self.online = any(not x.cached for x in days)
        self._last_day = self._now().date()
        if not days:
            self.error = error or "Keine gültigen Gebetszeiten verfügbar."
        self.update()

    def _zone(self):
        return ZoneInfo(self.days[0].timezone) if self.days else datetime.now().astimezone().tzinfo

    def _now(self):
        return datetime.now(self._zone())

    def _today(self):
        today = self._now().date()
        return next((d for d in self.days if d.day == today), None)

    def _next(self):
        return next_prayer(self._now(), self.days) if self.days else None

    def _tick(self):
        now = self._now()
        if not self._loading and (self._last_day != now.date() or (datetime.now() - self._last_refresh).total_seconds() > 1800):
            self.refresh()
        upcoming = self._next()
        if upcoming and self.settings["notifications"] and not self._demo:
            name, when, remaining, _ = upcoming
            # Notify only when a prayer actually begins; next_prayer has already rolled on.
            events = [(n, dt) for day in self.days for n, dt in day.times.items()]
            for prayer, dt in events:
                elapsed = (now.astimezone(ZoneInfo("UTC")) - dt.astimezone(ZoneInfo("UTC"))).total_seconds()
                marker = f"{dt.date()}:{prayer}"
                if 0 <= elapsed < 2 and marker != self._last_notification:
                    self._last_notification = marker
                    self.tray.showMessage("NamazFlow", f"Zeit für {prayer} · {dt:%H:%M}", QSystemTrayIcon.MessageIcon.Information, 9000)
                    break
        self.update()

    def configure(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        changes = dialog.values()
        if not changes["city"] or not changes["country"]:
            QMessageBox.warning(self, "NamazFlow", "Bitte Stadt und Land eingeben.")
            return
        previous = self.settings.copy()
        self.settings.update(changes)
        try:
            set_windows_autostart(self.settings["autostart"])
        except OSError as exc:
            self.settings["autostart"] = previous["autostart"]
            QMessageBox.warning(self, "Autostart", f"Windows-Autostart konnte nicht geändert werden: {exc}")
        save(self.settings)
        self._icon = self.make_icon()
        self.tray.setIcon(self._icon)
        self.tray.setContextMenu(self.menu())
        self.update()
        if any(previous[k] != self.settings[k] for k in ("city", "country", "method", "school")):
            self.days = []
            self.refresh()

    def edit_icon(self, prayer):
        current = self.settings.get("icons", DEFAULT_ICONS).get(prayer, DEFAULT_ICONS[prayer])
        chosen, accepted = QInputDialog.getItem(self, f"{prayer} · Symbol", "Symbol auswählen",
                                                 list(ICONS), list(ICONS).index(current), False)
        if accepted:
            self.settings.setdefault("icons", DEFAULT_ICONS.copy())[prayer] = chosen
            save(self.settings)
            self.update()

    def contextMenuEvent(self, event):
        self.menu().exec(event.globalPos())

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pt = event.position()
        if QRectF(12, 5, 100, 102).contains(pt):
            self._drag_start = (event.globalPosition().toPoint(), self.pos())
            self._was_dragged = False
        event.accept()

    def mouseMoveEvent(self, event):
        if not self._drag_start or not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        global_start, origin = self._drag_start
        delta = event.globalPosition().toPoint() - global_start
        if delta.manhattanLength() > 5:
            self._was_dragged = True
            self.move(origin + delta)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pt = event.position()
        if self._drag_start:
            self._drag_start = None
            if self._was_dragged:
                self.settings.update(x=self.x(), y=self.y())
                save(self.settings)
                return
            self.toggle()
            return
        if not self.expanded:
            return
        if QRectF(364, 124, 37, 32).contains(pt):
            self.configure()
        elif QRectF(402, 124, 30, 32).contains(pt):
            self.toggle()
        elif QRectF(33, 246, 405, 257).contains(pt):
            index = int((pt.y() - 247) // 51)
            if 0 <= index < 5:
                if pt.x() >= 362:
                    self.edit_icon(PRAYERS[index])
                else:
                    self.show_detail(PRAYERS[index])
        elif QRectF(37, 630, 370, 65).contains(pt):
            self.show_detail(current_prayer(self._now(), self.days) or "Asr")

    def show_detail(self, prayer):
        desc = QUOTES.get(prayer, QUOTES["Asr"])
        QMessageBox.information(self, f"NamazFlow · {prayer}",
                                f"{prayer}\n\n{desc[0]}\n\n{desc[1]}")

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        color = current_palette(self.settings["theme"])
        if self.expanded:
            self._draw_panel(p, color)
        self._draw_orb(p, color)
        p.end()

    def _draw_orb(self, p, colors):
        center_x = 60 if self.expanded else 54
        center_y = 55 if self.expanded else 54
        for r, alpha in ((49, 24), (46, 40), (43, 60)):
            p.setPen(QPen(c(GOLD, alpha), 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(center_x-r, center_y-r, 2*r, 2*r))
        gradient = QRadialGradient(center_x - 10, center_y - 15, 65)
        gradient.setColorAt(0, c("#29424A"))
        gradient.setColorAt(1, c("#111B22"))
        p.setPen(QPen(c(GOLD, 185), 1.8))
        p.setBrush(QBrush(gradient))
        p.drawEllipse(QRectF(center_x-41, center_y-41, 82, 82))
        upcoming = self._next()
        pct = upcoming[3] if upcoming else 0
        p.setPen(QPen(c(colors["accent"]), 4.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(center_x-43, center_y-43, 86, 86), 90 * 16, -int(pct * 360 * 16))
        draw_symbol(p, self.settings.get("symbol", "crescent"), center_x, center_y-8, 31, GOLD)
        draw_text(p, center_x-31, center_y+15,
                  countdown_text(upcoming[2]) if upcoming else "--:--", 11, WHITE, 600,
                  align=Qt.AlignmentFlag.AlignCenter, width=62)

    def _draw_panel(self, p, colors):
        rect = QRectF(17, 111, 426, 596)
        # Three-layer lifted shadow and translucent glass, with gold hairline.
        for d, a in ((12, 9), (8, 16), (4, 25)):
            round_rect(p, rect.translated(1, d), 21, c("#000000", a))
        fill = QLinearGradient(15, 115, 443, 707)
        fill.setColorAt(0, c(colors["panel"], 247))
        fill.setColorAt(0.55, c("#11191F", 247))
        fill.setColorAt(1, c("#241F20", 249))
        round_rect(p, rect, 21, fill, c("#A89173", 108), 1.2)
        # Fine clipped ornamental stars: understated, not competing with data.
        p.save()
        clip = QPainterPath()
        clip.addRoundedRect(rect, 21, 21)
        p.setClipPath(clip)
        for i in range(6):
            xx, yy = 403 + (i % 3) * 19, 182 + (i // 3) * 19
            p.setPen(QPen(c(GOLD, 28), 1))
            p.drawEllipse(QRectF(xx-12, yy-12, 24, 24))
            p.drawLine(xx-13, yy, xx+13, yy)
            p.drawLine(xx, yy-13, xx, yy+13)
        # Soft teal bloom behind countdown.
        glow = QRadialGradient(379, 555, 160)
        glow.setColorAt(0, c(colors["halo"], 85))
        glow.setColorAt(1, c(colors["halo"], 0))
        p.fillRect(QRectF(235, 445, 208, 194), glow)
        p.restore()
        draw_symbol(p, "star", 47, 141, 14, GOLD)
        draw_text(p, 64, 128, self.settings["city"], 11, WHITE, 500, width=252)
        draw_text(p, 373, 127, "⚙", 16, MUTED, 500, align=Qt.AlignmentFlag.AlignCenter, width=22)
        draw_text(p, 406, 127, "×", 19, MUTED, 400, align=Qt.AlignmentFlag.AlignCenter, width=22)
        draw_text(p, 36, 168, "Gebetszeiten heute", 23, WHITE, 500, family="Georgia", width=355)
        today = self._today()
        now = self._now()
        display_day = today.day if today else now.date()
        date_line = f"{WEEKDAYS[display_day.weekday()]}, {display_day.day}. {MONTHS[display_day.month-1]} {display_day.year}"
        draw_text(p, 38, 208, date_line, 10, MUTED, width=365)
        draw_text(p, 38, 228, (today.hijri + " H") if today and today.hijri else
                  "Islamisches Datum nicht verfügbar", 9, "#869496", width=370)
        p.setPen(QPen(c("#718080", 45), 1))
        p.drawLine(38, 247, 422, 247)
        active = current_prayer(now, self.days)
        icons = self.settings.get("icons", DEFAULT_ICONS)
        for i, prayer in enumerate(PRAYERS):
            y = 251 + 51 * i
            if active == prayer:
                round_rect(p, QRectF(35, y, 389, 46), 12, c(colors["row"], 210), c(colors["accent"], 185), 1.2)
            elif i < 4:
                p.setPen(QPen(c("#6A7477", 35), 1))
                p.drawLine(42, y + 48, 418, y + 48)
            draw_symbol(p, icons.get(prayer, DEFAULT_ICONS[prayer]), 59, y+23, 25,
                        colors["accent"] if active == prayer else GOLD)
            text_color = colors["accent"] if active == prayer else WHITE
            draw_text(p, 91, y+6, prayer, 12, text_color, 600 if active == prayer else 450, width=180)
            value = today.times[prayer].strftime("%H:%M") if today else "–:–"
            draw_text(p, 300, y+6, value, 12, text_color, 600 if active == prayer else 400,
                      width=62, align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            draw_text(p, 381, y+6, "✎", 15, MUTED, width=24,
                      align=Qt.AlignmentFlag.AlignCenter)
        countdown_rect = QRectF(36, 519, 388, 104)
        box_gradient = QLinearGradient(36, 519, 424, 623)
        box_gradient.setColorAt(0, c("#1E3236", 238))
        box_gradient.setColorAt(1, c("#294A45", 205))
        round_rect(p, countdown_rect, 15, box_gradient, c(colors["accent"], 100), 1)
        draw_symbol(p, "lantern", 57, 548, 22, GOLD)
        draw_text(p, 82, 529, "NÄCHSTES GEBET", 9, MUTED, 600, width=300)
        upcoming = self._next()
        countdown = countdown_text(upcoming[2]) if upcoming else "--:--"
        draw_text(p, 82, 554, countdown, 27, colors["accent"], 600, family="Georgia", width=200)
        next_label = f"Bis {upcoming[0]} · {upcoming[1]:%H:%M}" if upcoming else "Zeiten derzeit nicht verfügbar"
        draw_text(p, 83, 589, next_label, 10, MUTED, width=313)
        if not self.online:
            draw_text(p, 365, 529, "CACHE" if today and today.cached else "OFFLINE",
                      8, GOLD, 500, width=55)
        if self.settings.get("quote", True):
            draw_text(p, 40, 637, "“", 26, GOLD, 600, family="Georgia", width=30)
            quote = QUOTES.get(active or "Asr", QUOTES["Asr"])
            draw_text(p, 70, 639, quote[0], 9.1, GOLD, 450, family="Georgia", width=350)
            draw_text(p, 70, 665, quote[1], 8, MUTED, width=340)
        if self._demo:
            draw_text(p, 347, 691, "DESIGN-DEMO", 8, GOLD, 600, width=88)
        if self.error and not today:
            draw_text(p, 38, 692, "Keine aktuellen Daten – Verbindung / Standort prüfen",
                      8, "#E7BC8A", width=390)

    def closeEvent(self, event):
        # Deliberate exit via tray menu only; close requests hide the panel.
        if self.expanded:
            self.toggle()
            event.ignore()
        else:
            event.accept()
