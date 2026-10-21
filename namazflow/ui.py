"""Native desktop controls with independent orb and panel windows."""

from datetime import datetime, timedelta
import math
import threading
from zoneinfo import ZoneInfo
from PySide6.QtCore import (
    Qt,
    QPoint,
    QRectF,
    QSize,
    QUrl,
    Signal,
    QTimer,
    QVariantAnimation,
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
)
from PySide6.QtGui import (
    QBrush,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
    QDesktopServices,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QMenu,
    QSystemTrayIcon,
    QDialog,
    QInputDialog,
    QMessageBox,
    QScrollArea,
    QTextBrowser,
)
from .config import data_path, load, save, set_windows_autostart
from .drawing import (
    GOLD,
    TEAL,
    WHITE,
    c,
    font,
    draw_symbol,
    round_rect,
    current_palette,
    rosette_etching,
)
from .locations import LOCATIONS, location_label
from .diyanet import get_calendar
from .prayers import LABELS, PRAYERS, current_prayer, get_day, next_prayer
from .quotes import get_quote
from .settings import SettingsDialog

ICONS = (
    "sunrise",
    "sun",
    "afternoon",
    "sunset",
    "crescent",
    "mosque",
    "star",
    "lantern",
)
ICON_LABELS = (
    "Sonnenaufgang",
    "Sonne",
    "Nachmittag",
    "Sonnenuntergang",
    "Halbmond",
    "Moschee",
    "Stern",
    "Laterne",
)
DEFAULT_ICONS = dict(zip(PRAYERS, ICONS[:5]))
WEEKDAYS = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag",
)
MONTHS = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
)
STYLE = """
QWidget { font-family:'Segoe UI'; color:#F6F1E9; font-size:13px; }
QLabel { background:transparent; }
QLabel#eyebrow { color:#DBAE67; font-size:10px; font-weight:600; letter-spacing:2px; }
QLabel#title { font:24px 'Georgia'; }
QLabel#muted { color:#A7ACB2; font-size:11px; }
QPushButton { border:1px solid #45504F; border-radius:8px; padding:6px 9px; color:#D5C5AA; background:transparent; min-height:20px; }
QPushButton:hover { background:#294440; border-color:#56E4CE; color:#F6F1E9; }
QPushButton:pressed { background:#356158; }
QPushButton:focus { border-color:#56E4CE; }
QPushButton:disabled { color:#7F8D90; border-color:#344143; }
QComboBox { background:#1E3035; color:#E3CFAC; border:1px solid #495550; border-radius:8px; padding:7px 9px; min-height:20px; }
QComboBox::drop-down { border:none; width:24px; }
QComboBox QAbstractItemView { background:#18282D; color:#F6F1E9; selection-background-color:#2B5149; min-width:265px; padding:5px; }
QScrollArea { background:transparent; border:none; }
QScrollBar:vertical { width:6px; background:transparent; margin:4px 0; }
QScrollBar::handle:vertical { background:#4C625C; border-radius:3px; min-height:24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
QToolTip { background:#1A2D32; color:#EAD4AD; border:1px solid #687267; padding:7px; }
QMenu { background:#19272C; color:#F6F1E9; border:1px solid #5C685E; padding:6px; }
QMenu::item { padding:8px 18px; }
QMenu::item:selected { background:#2B5149; }
QMenu::separator { height:1px; background:#44534E; margin:5px; }
"""


def icon_for(kind, size=32, color=GOLD):
    pix = QPixmap(size * 2, size * 2)
    pix.fill(Qt.GlobalColor.transparent)
    pix.setDevicePixelRatio(2)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    draw_symbol(p, kind, size / 2, size / 2, size * 0.78, color)
    p.end()
    return QIcon(pix)


def control_icon(kind):
    pix = QPixmap(40, 40)
    pix.fill(Qt.GlobalColor.transparent)
    pix.setDevicePixelRatio(2)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(c("#D4C4A8"), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    if kind == "close":
        p.drawLine(5, 5, 15, 15)
        p.drawLine(15, 5, 5, 15)
    elif kind == "edit":
        p.drawLine(5, 14, 13, 6)
        p.drawLine(7, 16, 15, 8)
        p.drawLine(13, 6, 15, 8)
        p.drawLine(5, 14, 4, 17)
        p.drawLine(4, 17, 7, 16)
        p.drawLine(11, 8, 13, 10)
    elif kind == "refresh":
        p.drawArc(QRectF(4, 4, 12, 12), 35 * 16, 290 * 16)
        p.drawLine(15, 3, 16, 7)
        p.drawLine(16, 7, 12, 6)
    else:
        p.drawEllipse(QRectF(5, 5, 10, 10))
        p.drawEllipse(QRectF(8, 8, 4, 4))
        for i in range(8):
            a = i * math.pi / 4
            p.drawLine(
                round(10 + math.cos(a) * 6),
                round(10 + math.sin(a) * 6),
                round(10 + math.cos(a) * 8),
                round(10 + math.sin(a) * 8),
            )
    p.end()
    return QIcon(pix)


def label(text, name=None):
    widget = QLabel(text)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if name:
        widget.setObjectName(name)
    return widget


def button(text, tooltip, callback):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setToolTip(tooltip)
    widget.setAccessibleName(tooltip)
    widget.clicked.connect(callback)
    return widget


class PrayerRow(QWidget):
    def __init__(self, owner, prayer):
        super().__init__()
        self.owner, self.prayer = owner, prayer
        self.active, self.hover = False, 0.0
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(160)
        self.animation.valueChanged.connect(self._hover_value)
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 6, 8, 6)
        row.setSpacing(8)
        self.detail = button(
            LABELS[prayer],
            f"Gebetszeit {LABELS[prayer]}",
            lambda: owner.show_detail(prayer),
        )
        self.detail.setStyleSheet(
            "QPushButton { border:none; text-align:left; padding:3px; background:transparent; }"
        )
        self.detail.setMinimumHeight(30)
        self.detail.setIconSize(QSize(26, 26))
        row.addWidget(self.detail, 1)
        self.time = label("–:–")
        self.time.setFont(font(12, 500))
        self.time.setMinimumWidth(52)
        self.time.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        row.addWidget(self.time)
        self.edit = button(
            "", f"Symbol für {LABELS[prayer]} ändern", lambda: owner.edit_icon(prayer)
        )
        self.edit.setIcon(control_icon("edit"))
        self.edit.setFixedSize(32, 32)
        row.addWidget(self.edit)

    def _hover_value(self, value):
        self.hover = float(value)
        self.update()

    def _animate(self, value):
        self.animation.stop()
        if not self.owner.settings["animations"]:
            self._hover_value(value)
            return
        self.animation.setStartValue(self.hover)
        self.animation.setEndValue(value)
        self.animation.start()

    def enterEvent(self, event):
        self._animate(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0.0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = current_palette(self.owner.settings["theme"])
        if self.active or self.hover:
            round_rect(
                p,
                QRectF(self.rect()).adjusted(1, 1, -1, -1),
                11,
                c(colors["row"], 215 if self.active else int(150 * self.hover)),
                c(colors["accent"], 160 if self.active else int(70 * self.hover)),
            )
        else:
            p.setPen(QPen(c("#718080", 35), 1))
            p.drawLine(10, self.height() - 1, self.width() - 10, self.height() - 1)
        p.end()


class CountdownCard(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("countdownCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(
            "#countdownCard {background:#203D3B; border:1px solid #467A6B; border-radius:14px;}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 14)
        layout.setSpacing(3)
        self.heading = label("NÄCHSTES GEBET", "eyebrow")
        self.time = label("–")
        self.time.setStyleSheet("font:28px 'Georgia'; color:#74E5CD;")
        self.next = label("Gebetszeiten werden geladen …", "muted")
        self.next.setWordWrap(True)
        for part in (self.heading, self.time, self.next):
            layout.addWidget(part)


class PrayerPanel(QWidget):
    def __init__(self, owner):
        super().__init__(
            owner,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.owner = owner
        self.setWindowTitle("NamazFlow · Gebetszeiten")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.setFixedWidth(416)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(self.scroll)
        self.content = QWidget()
        self.content.setObjectName("panelContent")
        self.content.setStyleSheet("#panelContent { background:transparent; }")
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(9)
        header = QHBoxLayout()
        header.addWidget(label("NAMAZFLOW", "eyebrow"), 1)
        self.gear = button("", "Einstellungen öffnen", owner.configure)
        self.close_button = button("", "Menü einklappen (Esc)", owner.collapse)
        self.gear.setIcon(control_icon("settings"))
        self.close_button.setIcon(control_icon("close"))
        self.gear.setFixedSize(32, 32)
        self.close_button.setFixedSize(32, 32)
        header.addWidget(self.gear)
        header.addWidget(self.close_button)
        layout.addLayout(header)
        layout.addWidget(label("Deine Gebetszeiten", "title"))
        self.city = QComboBox()
        self.city.setAccessibleName("Standort wechseln")
        for key, place in LOCATIONS.items():
            self.city.addItem(place["label"], key)
        self.city.currentIndexChanged.connect(
            lambda index: owner.switch_location(self.city.itemData(index))
        )
        layout.addWidget(self.city)
        self.date, self.hijri = label("", "muted"), label("", "muted")
        layout.addWidget(self.date)
        layout.addWidget(self.hijri)
        rows = QVBoxLayout()
        rows.setSpacing(4)
        self.rows = {}
        for prayer in PRAYERS:
            row = PrayerRow(owner, prayer)
            self.rows[prayer] = row
            rows.addWidget(row)
        layout.addLayout(rows)
        self.countdown = CountdownCard()
        layout.addWidget(self.countdown)
        self.quote_box = QWidget()
        quote_layout = QVBoxLayout(self.quote_box)
        quote_layout.setContentsMargins(0, 2, 0, 0)
        quote_layout.setSpacing(8)
        quote_header = QHBoxLayout()
        self.quote_heading = label("MOMENT DER BESINNUNG", "eyebrow")
        quote_header.addWidget(self.quote_heading, 1)
        self.next_quote = button("", "Nächstes Zitat laden", owner.next_quote)
        self.next_quote.setIcon(control_icon("refresh"))
        self.next_quote.setFixedSize(30, 30)
        quote_header.addWidget(self.next_quote)
        quote_layout.addLayout(quote_header)
        self.quote_text = label("Zitat wird geladen …")
        self.quote_text.setStyleSheet("font:italic 14px 'Georgia'; color:#E5C795;")
        self.quote_text.setWordWrap(True)
        self.quote_text.setMinimumHeight(44)
        self.quote_text.setMaximumHeight(84)
        quote_layout.addWidget(self.quote_text)
        self.quote_ref = label("", "muted")
        self.quote_ref.setWordWrap(True)
        quote_layout.addWidget(self.quote_ref)
        self.quote_detail = button(
            "Zitat & Quelle ansehen",
            "Vollständiges Zitat mit Quellenangabe",
            owner.show_quote,
        )
        self.quote_detail.setEnabled(False)
        quote_layout.addWidget(self.quote_detail)
        layout.addWidget(self.quote_box)
        self.status = label("", "muted")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.scroll.setWidget(self.content)
        self.animation = QParallelAnimationGroup(self)
        self.fade = QPropertyAnimation(self, b"windowOpacity")
        self.slide = QPropertyAnimation(self, b"pos")
        for anim in (self.fade, self.slide):
            anim.setDuration(210)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animation.addAnimation(anim)
        self.sync_city()

    def sync_city(self):
        self.city.blockSignals(True)
        while self.city.count() > len(LOCATIONS):
            self.city.removeItem(self.city.count() - 1)
        key = self.owner.settings["location"]
        if key:
            self.city.setCurrentIndex(self.city.findData(key))
        elif self.owner.settings["city"].casefold() == "darmstadt":
            self.city.setCurrentIndex(0)
        else:
            self.city.addItem(self.owner.settings["city"], "")
            self.city.setCurrentIndex(self.city.count() - 1)
        self.city.blockSignals(False)

    def open(self):
        self.animation.stop()
        screen = (
            QApplication.screenAt(self.owner.geometry().center())
            or QApplication.primaryScreen()
        )
        self.setFixedHeight(min(788, screen.availableGeometry().height() - 24))
        end = self.owner.panel_position()
        animate = (
            self.owner.settings["animations"]
            and QApplication.platformName() != "offscreen"
        )
        self.move(end + QPoint(0, 10) if animate else end)
        self.setWindowOpacity(0.0 if animate else 1.0)
        self.show()
        self.raise_()
        self.activateWindow()
        if animate:
            self.fade.setStartValue(0.0)
            self.fade.setEndValue(1.0)
            self.slide.setStartValue(self.pos())
            self.slide.setEndValue(end)
            self.animation.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.owner.collapse()
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.owner.collapse()
        event.ignore()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = current_palette(self.owner.settings["theme"])
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        for d, alpha in ((5, 12), (3, 22)):
            round_rect(p, rect.translated(0, d), 22, c("#000000", alpha))
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0, c(colors["panel"], 251))
        grad.setColorAt(1, c("#182322", 252))
        round_rect(p, rect, 22, QBrush(grad), c(GOLD, 105), 1)
        clip = QPainterPath()
        clip.addRoundedRect(rect, 22, 22)
        p.setClipPath(clip)
        rosette_etching(p, self.width() - 22, self.height() - 38, 65)
        p.end()


class NamazWidget(QWidget):
    loaded = Signal(object, str, int)
    quote_loaded = Signal(object, str, int)
    COLLAPSED = (128, 128)

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("NamazFlow")
        self.setStyleSheet(STYLE)
        self.setFixedSize(*self.COLLAPSED)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.settings = load()
        self.days = []
        self.error = "Gebetszeiten werden geladen …"
        self.online = self.expanded = False
        self._drag_start = None
        self._was_dragged = self._loading = False
        self._generation = 0
        self._last_day = self._last_notification = None
        self._last_refresh = datetime.now()
        self._demo = False
        self.quote = None
        self.quote_error = ""
        self._quote_index = datetime.now().date().toordinal() % 12
        self._quote_generation = 0
        self._quote_loading = False
        self._phase = self._hover = 0.0
        self.hover_animation = QVariantAnimation(self)
        self.hover_animation.setDuration(180)
        self.hover_animation.valueChanged.connect(self._hover_value)
        self.loaded.connect(self._received)
        self.quote_loaded.connect(self._quote_received)
        self.panel = PrayerPanel(self)
        self._icon = self.make_icon()
        self.setWindowIcon(self._icon)
        self.panel.setWindowIcon(self._icon)
        self.tray = QSystemTrayIcon(self._icon, self)
        self.tray.setToolTip("NamazFlow · Gebetszeiten")
        self.tray.activated.connect(self._tray_activated)
        self._tray_menu = self.menu()
        self.tray.setContextMenu(self._tray_menu)
        self.tray.show()
        screen = QApplication.primaryScreen().availableGeometry()
        x = (
            self.settings["x"]
            if self.settings["x"] is not None
            else screen.right() - 155
        )
        y = self.settings["y"] if self.settings["y"] is not None else screen.top() + 55
        self.move(self.clamped_position(QPoint(int(x), int(y))))
        self.tick = QTimer(self)
        self.tick.timeout.connect(self._tick)
        self.tick.start(1000)
        self.motion = QTimer(self)
        self.motion.timeout.connect(self._motion_tick)
        self.motion.start(40)
        self.quote_timer = QTimer(self)
        self.quote_timer.timeout.connect(self.next_quote)
        self.quote_timer.start(5 * 60 * 1000)
        self.refresh()
        if self.settings["quote"]:
            self.load_quote()

    def make_icon(self):
        pix = QPixmap(128, 128)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(c(GOLD), 2))
        p.setBrush(c("#182D32"))
        p.drawEllipse(QRectF(5, 5, 118, 118))
        p.setPen(QPen(c(TEAL), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawArc(QRectF(9, 9, 110, 110), 90 * 16, -125 * 16)
        draw_symbol(p, self.settings["symbol"], 61, 63, 66, GOLD)
        p.end()
        return QIcon(pix)

    def menu(self):
        menu = QMenu(self)
        menu.addAction("Gebetszeiten öffnen", self.open_panel)
        menu.addAction("Menü einklappen", self.collapse)
        menu.addAction("Flow ausblenden", self.hide_flow)
        menu.addAction("Flow wieder anzeigen", self.show_flow)
        places = menu.addMenu("Standort wechseln")
        for key, place in LOCATIONS.items():
            action = places.addAction(place["label"])
            action.setCheckable(True)
            action.setChecked(self.settings["location"] == key)
            action.triggered.connect(
                lambda checked=False, key=key: self.switch_location(key)
            )
        menu.addSeparator()
        menu.addAction("Einstellungen", self.configure)
        menu.addAction("Zeiten aktualisieren", self.refresh)
        menu.addSeparator()
        menu.addAction("NamazFlow beenden", self.quit_app)
        return menu

    def quit_app(self):
        # Window-manager close hides Flow; the explicit exit action must bypass it.
        self.collapse()
        self.hide()
        self.tray.hide()
        QApplication.exit(0)

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if not self.isVisible():
                self.show_flow()
            self.toggle()

    def show_flow(self):
        self.move(self.clamped_position(self.pos()))
        self.show()
        self.raise_()

    def hide_flow(self):
        self.collapse()
        self.hide()

    def open_panel(self):
        self.show_flow()
        self.expanded = True
        self._render_state()
        self.panel.open()
        self.update()

    def collapse(self):
        self.expanded = False
        self.panel.animation.stop()
        self.panel.hide()
        self.panel.setWindowOpacity(1.0)
        self.update()

    def toggle(self):
        self.collapse() if self.expanded else self.open_panel()

    def clamped_position(self, point):
        screen = (
            QApplication.screenAt(point + QPoint(64, 64))
            or self.screen()
            or QApplication.primaryScreen()
        )
        geo = screen.availableGeometry()
        return QPoint(
            max(geo.left(), min(point.x(), geo.right() - self.width() + 1)),
            max(geo.top(), min(point.y(), geo.bottom() - self.height() + 1)),
        )

    def panel_position(self):
        screen = (
            QApplication.screenAt(self.geometry().center())
            or QApplication.primaryScreen()
        )
        geo = screen.availableGeometry()
        right, left = self.x() + self.width() + 8, self.x() - self.panel.width() - 8
        x = right if right + self.panel.width() <= geo.right() + 1 else left
        return QPoint(
            max(geo.left(), min(x, geo.right() - self.panel.width() + 1)),
            max(geo.top(), min(self.y(), geo.bottom() - self.panel.height() + 1)),
        )

    def moveEvent(self, event):
        if hasattr(self, "panel") and self.panel.isVisible():
            self.panel.animation.stop()
            self.panel.setWindowOpacity(1.0)
            self.panel.move(self.panel_position())
        super().moveEvent(event)

    def refresh(self):
        self._generation += 1
        generation, config = self._generation, dict(self.settings)
        self._loading = True
        self._last_refresh = datetime.now()
        self._render_state()

        def task():
            days, errors = [], []
            today = datetime.now(ZoneInfo("Europe/Berlin")).date()
            if config["time_source"] == "ditib":
                try:
                    calendar = get_calendar(config, data_path() / "cache")
                    days = [
                        day for day in calendar if -1 <= (day.day - today).days <= 1
                    ]
                except (ConnectionError, ValueError) as exc:
                    errors.append(str(exc))
            else:
                for offset in (-1, 0, 1):
                    try:
                        days.append(
                            get_day(
                                today + timedelta(days=offset),
                                config,
                                data_path() / "cache",
                            )
                        )
                    except (ConnectionError, ValueError) as exc:
                        errors.append(str(exc))
            self.loaded.emit(days, "; ".join(errors), generation)

        threading.Thread(target=task, daemon=True).start()

    def _received(self, days, error, generation):
        if generation != self._generation:
            return
        self.days, self.error, self._loading = days, error, False
        self.online = any(not day.cached for day in days)
        self._last_day = self._now().date()
        self._render_state()

    def _now(self):
        return datetime.now(
            ZoneInfo(self.days[0].timezone if self.days else "Europe/Berlin")
        )

    def _today(self):
        return next((day for day in self.days if day.day == self._now().date()), None)

    def _next(self):
        return next_prayer(self._now(), self.days) if self.days else None

    def _tick(self):
        now = self._now()
        if not self._loading and (
            self._last_day != now.date()
            or (datetime.now() - self._last_refresh).total_seconds() > 1800
        ):
            self.refresh()
        if self.settings["notifications"] and not self._demo:
            for day in self.days:
                for prayer, moment in day.times.items():
                    elapsed = (
                        now.astimezone(ZoneInfo("UTC"))
                        - moment.astimezone(ZoneInfo("UTC"))
                    ).total_seconds()
                    marker = f"{moment.date()}:{prayer}"
                    if 0 <= elapsed < 2 and marker != self._last_notification:
                        self._last_notification = marker
                        self.tray.showMessage(
                            "NamazFlow",
                            f"Zeit für {LABELS[prayer]} · {moment:%H:%M}",
                            QSystemTrayIcon.MessageIcon.Information,
                            9000,
                        )
        self._render_state()

    def _motion_tick(self):
        if self.settings["animations"] and self.isVisible():
            self._phase += 0.045
            self.update()

    def _hover_value(self, value):
        self._hover = float(value)
        self.update()

    def _animate_hover(self, value):
        self.hover_animation.stop()
        if not self.settings["animations"]:
            self._hover_value(value)
            return
        self.hover_animation.setStartValue(self._hover)
        self.hover_animation.setEndValue(value)
        self.hover_animation.start()

    def enterEvent(self, event):
        self._animate_hover(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(0.0)
        super().leaveEvent(event)

    def _render_state(self):
        if not hasattr(self, "panel"):
            return
        panel = self.panel
        today, now, upcoming = self._today(), self._now(), self._next()
        panel.date.setText(
            f"{WEEKDAYS[now.weekday()]}, {now.day}. {MONTHS[now.month - 1]} {now.year}"
        )
        panel.hijri.setText(
            f"{today.hijri} H"
            if today and today.hijri
            else "Islamisches Datum nicht verfügbar"
        )
        active = current_prayer(now, self.days) if self.days else None
        accent = current_palette(self.settings["theme"])["accent"]
        for prayer, row in panel.rows.items():
            row.active = prayer == active
            row.time.setText(today.times[prayer].strftime("%H:%M") if today else "–:–")
            row.detail.setIcon(
                icon_for(
                    self.settings["icons"].get(prayer, DEFAULT_ICONS[prayer]),
                    color=accent if row.active else GOLD,
                )
            )
            row.time.setStyleSheet(f"color:{accent if row.active else WHITE};")
            row.update()
        if upcoming:
            hours, rest = divmod(upcoming[2], 3600)
            minutes = rest // 60
            duration = (
                f"{hours} Std. {minutes:02d} Min."
                if hours
                else f"{minutes} Min. {rest % 60:02d} Sek."
            )
            panel.countdown.time.setText(duration)
            panel.countdown.next.setText(
                f"bis {LABELS[upcoming[0]]} · {upcoming[1]:%H:%M} Uhr"
            )
            self.setToolTip(
                f"{location_label(self.settings)}\nNoch {duration} bis {LABELS[upcoming[0]]} ({upcoming[1]:%H:%M} Uhr)\nZiehen: verschieben · Klick: Gebetszeiten · Rechtsklick: Menü"
            )
        else:
            panel.countdown.time.setText("–")
            panel.countdown.next.setText(
                "Gebetszeiten werden geladen …"
                if self._loading
                else "Keine aktuellen Gebetszeiten verfügbar"
            )
            self.setToolTip(
                "NamazFlow\nZiehen: verschieben · Klick: Gebetszeiten · Rechtsklick: Menü"
            )
        panel.quote_box.setVisible(self.settings["quote"])
        if self._loading:
            panel.status.setText("Gebetszeiten werden aktualisiert …")
        elif not today:
            panel.status.setText(
                "Keine aktuellen Zeiten. Verbindung prüfen oder erneut aktualisieren."
            )
        elif self.error:
            panel.status.setText(
                "Zeiten teilweise verfügbar · Aktualisierung später erneut versuchen."
            )
        else:
            panel.status.setText(
                f"Gespeichert · {today.source}"
                if today.cached
                else f"Aktuell · {today.source}"
            )
        panel.status.setToolTip(self.error)
        self.update()

    def switch_location(self, key):
        if key not in LOCATIONS or self.settings["location"] == key:
            return
        preset = LOCATIONS[key]
        self.settings.update(
            location=key, city=preset["city"], country=preset["country"]
        )
        save(self.settings)
        self.days = []
        self.panel.sync_city()
        self._rebuild_menu()
        self.refresh()

    def _rebuild_menu(self):
        old = self._tray_menu
        self._tray_menu = self.menu()
        self.tray.setContextMenu(self._tray_menu)
        old.deleteLater()

    def configure(self):
        self.collapse()
        dialog = SettingsDialog(self.settings, self)
        dialog.setWindowIcon(self._icon)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        changes = dialog.values()
        if not changes["city"] or not changes["country"]:
            QMessageBox.warning(self, "NamazFlow", "Bitte Stadt und Land eingeben.")
            return
        previous = self.settings.copy()
        self.settings.update(changes)
        if previous["autostart"] != changes["autostart"]:
            try:
                set_windows_autostart(changes["autostart"])
            except OSError as exc:
                self.settings["autostart"] = previous["autostart"]
                QMessageBox.warning(self, "Autostart", str(exc))
        save(self.settings)
        self._icon = self.make_icon()
        self.setWindowIcon(self._icon)
        self.tray.setIcon(self._icon)
        self.panel.sync_city()
        self._rebuild_menu()
        if any(
            previous[k] != self.settings[k]
            for k in ("city", "country", "location", "time_source", "method", "school")
        ):
            self.days = []
            self.refresh()
        if previous["quote_source"] != self.settings["quote_source"]:
            self.quote = None
            self._quote_generation += 1
            self._quote_loading = False
        if self.settings["quote"] and (not self.quote or not previous["quote"]):
            self.load_quote()
        self.open_panel()

    def edit_icon(self, prayer):
        current = self.settings["icons"].get(prayer, DEFAULT_ICONS[prayer])
        chosen, accepted = QInputDialog.getItem(
            self.panel,
            f"{LABELS[prayer]} · Symbol",
            "Symbol auswählen",
            list(ICON_LABELS),
            ICONS.index(current),
            False,
        )
        if accepted:
            self.settings["icons"][prayer] = ICONS[ICON_LABELS.index(chosen)]
            save(self.settings)
            self._render_state()

    def load_quote(self):
        if self._quote_loading or not self.settings["quote"]:
            return
        self._quote_generation += 1
        generation = self._quote_generation
        index, source = self._quote_index, self.settings["quote_source"]
        self._quote_loading = True
        self.panel.next_quote.setEnabled(False)
        if self.quote is None:
            self.panel.quote_text.setText("Zitat wird geladen …")
            self.panel.quote_ref.setText("")
            self.panel.quote_detail.setEnabled(False)

        def task():
            try:
                quote = get_quote(index, data_path() / "quotes", source)
                self.quote_loaded.emit(quote, "", generation)
            except ConnectionError as exc:
                self.quote_loaded.emit(None, str(exc), generation)

        threading.Thread(target=task, daemon=True).start()

    def next_quote(self):
        if not self._quote_loading:
            self._quote_index += 1
            self.load_quote()

    def _quote_received(self, quote, error, generation):
        if generation != self._quote_generation:
            return
        self._quote_loading, self.quote_error = False, error
        self.panel.next_quote.setEnabled(True)
        if quote:
            self.quote = quote
        if self.quote:
            text = self.quote.text
            # Preview is marked with ellipsis; detail preserves the full source text.
            if len(text) > 165:
                text = text[:162].rsplit(" ", 1)[0] + " …"
            self.panel.quote_text.setText(text)
            self.panel.quote_heading.setText(
                "KORAN · ÜBERSETZUNG"
                if self.quote.kind == "quran"
                else "HADITH · ÜBERSETZUNG"
            )
            suffix = " · gespeichert" if self.quote.cached else ""
            if error:
                suffix += " · Aktualisierung fehlgeschlagen"
            self.panel.quote_ref.setText(
                f"{self.quote.reference}\n{self.quote.publisher}{suffix}"
            )
            self.panel.quote_ref.setToolTip(error)
        else:
            self.panel.quote_text.setText(error or "Zitat derzeit nicht verfügbar.")
            self.panel.quote_ref.setText("Mit ↻ erneut versuchen.")
        self.panel.quote_detail.setEnabled(self.quote is not None)

    def show_quote(self):
        if not self.quote:
            return
        quote = self.quote
        dialog = QDialog(self.panel)
        dialog.setWindowTitle("NamazFlow · Zitat & Quelle")
        dialog.setStyleSheet("QDialog { background:#18272B; }" + STYLE)
        dialog.resize(480, 430)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)
        layout.addWidget(
            label(
                "Koran · Übersetzung"
                if quote.kind == "quran"
                else "Hadith · Übersetzung",
                "eyebrow",
            )
        )
        text = QTextBrowser()
        source_text = quote.text
        if quote.original_attribution:
            source_text += (
                "\n\nOriginal-Quellenangabe des Anbieters:\n"
                + quote.original_attribution
            )
        text.setPlainText(source_text)
        text.setStyleSheet(
            "background:#203236; color:#EDD5AD; border:0; padding:12px; font:16px 'Georgia';"
        )
        layout.addWidget(text, 1)
        attribution = label(f"{quote.reference}\n{quote.publisher}", "muted")
        attribution.setWordWrap(True)
        layout.addWidget(attribution)
        layout.addWidget(
            button(
                "Quelle im Browser öffnen",
                "Originalquelle öffnen",
                lambda: QDesktopServices.openUrl(QUrl(quote.url)),
            )
        )
        layout.addWidget(button("Schließen", "Zitat schließen", dialog.accept))
        dialog.exec()

    def show_detail(self, prayer):
        today = self._today()
        value = (
            today.times[prayer].strftime("%H:%M") + " Uhr"
            if today
            else "Keine aktuelle Zeit verfügbar"
        )
        source = today.source if today else "Keine gültigen Daten"
        sunrise = (
            f"\nSabah beginnt mit İmsak. Güneş (Sonnenaufgang): {today.sunrise:%H:%M} Uhr"
            if today and today.sunrise and prayer == "Fajr"
            else ""
        )
        QMessageBox.information(
            self.panel,
            f"NamazFlow · {LABELS[prayer]}",
            f"{LABELS[prayer]} · {value}\n{location_label(self.settings)}\n\nQuelle: {source}{sunrise}",
        )

    def contextMenuEvent(self, event):
        self._context_menu = self.menu()
        self._context_menu.exec(event.globalPos())
        self._context_menu.deleteLater()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = (event.globalPosition().toPoint(), self.pos())
            self._was_dragged = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start and event.buttons() & Qt.MouseButton.LeftButton:
            start, origin = self._drag_start
            delta = event.globalPosition().toPoint() - start
            if delta.manhattanLength() >= QApplication.startDragDistance():
                self._was_dragged = True
            if self._was_dragged:
                self.move(self.clamped_position(origin + delta))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start:
            self._drag_start = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            if self._was_dragged:
                self.settings.update(x=self.x(), y=self.y())
                save(self.settings)
            else:
                self.toggle()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colors = current_palette(self.settings["theme"])
        center = 64
        pulse = (math.sin(self._phase) + 1) / 2 if self.settings["animations"] else 0.25
        for radius, alpha in ((59, 14),):
            p.setPen(QPen(c(GOLD, int(alpha + self._hover * 20 + pulse * 4)), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(
                QRectF(center - radius, center - radius, 2 * radius, 2 * radius)
            )
        grad = QRadialGradient(44, 28, 110)
        grad.setColorAt(0, c("#29444B"))
        grad.setColorAt(1, c("#101E25"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(c(GOLD, 195), 1.3))
        p.drawEllipse(QRectF(11, 11, 106, 106))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(c(colors["accent"], 35), 3))
        p.drawEllipse(QRectF(9, 9, 110, 110))
        upcoming = self._next()
        pct = upcoming[3] if upcoming else 0
        p.setPen(
            QPen(
                c(colors["accent"]),
                3.3 + self._hover * 0.8,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        p.drawArc(QRectF(9, 9, 110, 110), 90 * 16, -int(max(0.015, pct) * 360 * 16))
        draw_symbol(p, self.settings["symbol"], 62, 44 - self._hover * 2, 34, "#E9BE78")
        p.setPen(c("#C9D9D5"))
        p.setFont(font(8, 500))
        p.drawText(
            QRectF(20, 67, 88, 16),
            Qt.AlignmentFlag.AlignCenter,
            f"bis {LABELS[upcoming[0]]}" if upcoming else "Gebetszeiten",
        )
        p.setFont(font(10.3, 600))
        p.setPen(c(WHITE))
        if upcoming:
            hours, rest = divmod(upcoming[2], 3600)
            time_text = f"{hours}h {rest // 60:02d}m"
        else:
            time_text = "lädt …" if self._loading else "offline"
        p.drawText(QRectF(17, 84, 94, 22), Qt.AlignmentFlag.AlignCenter, time_text)
        p.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.collapse()
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.hide_flow()
        event.ignore()
