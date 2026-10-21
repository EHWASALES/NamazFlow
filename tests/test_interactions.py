"""Regression checks for interaction, locations and source integrity."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pytest
from PySide6.QtCore import Qt, QPoint, QPointF, QEvent
from PySide6.QtGui import QMouseEvent, QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
import namazflow.ui as ui
from namazflow.config import normalize, load, save
from namazflow.locations import LOCATIONS
from namazflow.prayers import get_day
from namazflow.quotes import get_quote, parse_quote, quote_spec
from test_core import sample_payload


@pytest.fixture(scope="session")
def app():
    app = QApplication.instance() or QApplication([])
    # The Windows offscreen plugin needs explicit fonts; the normal desktop does not.
    if os.name == "nt":
        for name in ("segoeui.ttf", "georgia.ttf"):
            QFontDatabase.addApplicationFont(
                str(Path(os.environ["WINDIR"]) / "Fonts" / name)
            )
    yield app


@pytest.fixture
def widget(app, monkeypatch):
    monkeypatch.setattr(
        ui, "load", lambda: normalize({"animations": False, "location": "darmstadt"})
    )
    monkeypatch.setattr(ui, "save", lambda config: None)
    monkeypatch.setattr(ui.NamazWidget, "refresh", lambda self: None)
    monkeypatch.setattr(ui.NamazWidget, "load_quote", lambda self: None)
    w = ui.NamazWidget()
    for timer in (w.tick, w.motion, w.quote_timer):
        timer.stop()
    w.move(40, 40)
    w.show()
    app.processEvents()
    yield w
    w.collapse()
    w.hide()
    w.tray.hide()
    w.deleteLater()
    app.processEvents()


def test_click_close_escape_and_no_orb_jumping(widget, app):
    start = widget.pos()
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton, pos=QPoint(64, 64))
    app.processEvents()
    assert widget.expanded and widget.panel.isVisible()
    assert widget.pos() == start
    QTest.mouseClick(widget.panel.close_button, Qt.MouseButton.LeftButton)
    assert not widget.expanded and not widget.panel.isVisible()
    widget.open_panel()
    QTest.keyClick(widget.panel, Qt.Key.Key_Escape)
    assert not widget.expanded
    assert widget.pos() == start


def test_drag_changes_position_and_does_not_open(widget, app):
    start = widget.pos()
    local = QPointF(64, 64)
    global_start = QPointF(widget.mapToGlobal(QPoint(64, 64)))
    # Real mouse events with global positions preserve a held left button.
    events = [
        QMouseEvent(
            QEvent.Type.MouseButtonPress,
            local,
            global_start,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        ),
        QMouseEvent(
            QEvent.Type.MouseMove,
            local + QPointF(80, 45),
            global_start + QPointF(80, 45),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        ),
        QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            local,
            global_start + QPointF(80, 45),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        ),
    ]
    for event in events:
        app.sendEvent(widget, event)
    assert widget.pos() == start + QPoint(80, 45)
    assert not widget.expanded
    assert widget.settings["x"] == widget.x()
    assert widget.settings["y"] == widget.y()


def test_context_actions_hide_and_restore(widget):
    menu = widget.menu()
    actions = {action.text(): action for action in menu.actions()}
    actions["Flow ausblenden"].trigger()
    assert not widget.isVisible()
    actions["Flow wieder anzeigen"].trigger()
    assert widget.isVisible()
    actions["Gebetszeiten öffnen"].trigger()
    assert widget.expanded
    actions["Menü einklappen"].trigger()
    assert not widget.expanded
    menu.deleteLater()


def test_both_city_switches_clear_old_times(widget):
    widget.days = ["old"]
    widget.panel.city.setCurrentIndex(1)
    assert widget.settings["location"] == "niederhoechstadt"
    assert widget.settings["city"] == "Niederhöchstadt"
    assert widget.days == []
    widget.panel.city.setCurrentIndex(0)
    assert widget.settings["location"] == "darmstadt"
    assert widget.settings["city"] == "Darmstadt"


def test_stale_location_response_is_ignored(widget):
    widget._generation = 2
    widget._received(["stale"], "", 1)
    assert widget.days == []


@pytest.mark.parametrize("key", LOCATIONS)
def test_coordinates_and_location_cache_isolation(key, tmp_path):
    requests = []

    def transport(url):
        requests.append(url)
        return sample_payload()

    get_day(
        date(2026, 10, 21), normalize({"location": key}), tmp_path, transport=transport
    )
    query = parse_qs(urlparse(requests[0]).query)
    assert "/timings/" in requests[0]
    assert float(query["latitude"][0]) == LOCATIONS[key]["latitude"]
    assert float(query["longitude"][0]) == LOCATIONS[key]["longitude"]
    other = next(x for x in LOCATIONS if x != key)

    def fails(url):
        raise OSError("offline")

    with pytest.raises(ConnectionError):
        get_day(
            date(2026, 10, 21),
            normalize({"location": other}),
            tmp_path,
            transport=fails,
        )


def test_old_custom_city_is_preserved():
    assert normalize({"city": "Köln"})["location"] == ""
    assert normalize({"location": "invalid"})["location"] == ""


def test_quran_cache_rejects_wrong_verse_and_works_offline(tmp_path):
    payload = {
        "result": {
            "sura": "94",
            "aya": "5",
            "translation": "Testtext aus einer Testantwort",
        }
    }
    quote = get_quote(0, tmp_path, "quran", transport=lambda url: payload)
    assert quote.reference == "Koran 94:5"

    def fails(url):
        raise OSError("offline")

    cached = get_quote(0, tmp_path, "quran", transport=fails)
    assert cached.cached and cached.text == quote.text
    with pytest.raises(ValueError):
        parse_quote(payload, "quran", (94, 6))
    with pytest.raises(ConnectionError):
        get_quote(1, tmp_path, "quran", transport=fails)


def test_hadith_attribution_and_no_html_execution(tmp_path):
    payload = {
        "id": "66520",
        "hadeeth": "<b>Testtext</b> &amp; Quelle",
        "attribution": "Überlieferer",
        "grade": "Authentisch",
    }
    quote = get_quote(0, tmp_path, "hadith", transport=lambda url: payload)
    assert quote.text == "Testtext & Quelle"
    assert quote.original_attribution == "Überlieferer"
    assert (
        "Al-Bukhari und Muslim" in quote.reference and "Authentisch" in quote.reference
    )
    assert quote.url.endswith("/66520")
    with pytest.raises(ValueError):
        parse_quote(payload, "hadith", 66538)


def test_sources_rotate_and_settings_persist(tmp_path):
    assert [quote_spec(n)[0] for n in range(4)] == [
        "quran",
        "hadith",
        "quran",
        "hadith",
    ]
    config = normalize(
        {"location": "niederhoechstadt", "animations": False, "quote_source": "hadith"}
    )
    save(config, tmp_path / "settings.json")
    assert load(tmp_path / "settings.json") == config


def test_quote_full_text_preserved_and_stale_response_ignored(widget):
    from namazflow.quotes import Quote

    quote = Quote(
        "Ein langer Testtext. " * 50,
        "Testquelle",
        "https://quranenc.com",
        "quran",
        "Test",
    )
    widget._quote_generation = 2
    widget._quote_received(quote, "", 1)
    assert widget.quote is None
    widget._quote_received(quote, "", 2)
    assert widget.quote.text == quote.text
    assert len(widget.panel.quote_text.text()) < len(quote.text)
    assert widget.panel.quote_detail.isEnabled()


def test_layout_fits_long_location_and_source(widget, app):
    widget.switch_location("niederhoechstadt")
    widget.open_panel()
    app.processEvents()
    assert widget.panel.content.width() <= widget.panel.scroll.viewport().width()
    for row in widget.panel.rows.values():
        assert row.time.geometry().right() < row.edit.geometry().left()
        assert row.detail.geometry().right() < row.time.geometry().left()
    assert widget.panel.close_button.isVisible()


def test_small_screen_scroll_keeps_quote_controls_reachable(widget, app):
    widget.open_panel()
    widget.panel.setFixedHeight(420)
    app.processEvents()
    bar = widget.panel.scroll.verticalScrollBar()
    assert bar.maximum() > 0
    bar.setValue(bar.maximum())
    app.processEvents()
    point = widget.panel.quote_detail.mapTo(
        widget.panel.scroll.viewport(), widget.panel.quote_detail.rect().center()
    )
    assert widget.panel.scroll.viewport().rect().contains(point)


def test_disabled_quotes_reclaim_layout_space(widget, app):
    widget.open_panel()
    widget.settings["quote"] = False
    widget._render_state()
    app.processEvents()
    assert widget.panel.quote_box.isHidden()


def test_rows_use_turkish_names(widget):
    assert [row.detail.text() for row in widget.panel.rows.values()] == [
        "Sabah",
        "Öğle",
        "İkindi",
        "Akşam",
        "Yatsı",
    ]


def test_explicit_exit_is_different_from_hide(widget, monkeypatch):
    exits = []
    monkeypatch.setattr(ui.QApplication, "exit", lambda code: exits.append(code))
    widget.open_panel()
    widget.quit_app()
    assert exits == [0]
    assert not widget.isVisible() and not widget.panel.isVisible()
    assert not widget.tray.isVisible()
