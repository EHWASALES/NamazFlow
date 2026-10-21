"""Official published-calendar integrity, cache and Turkish presentation regressions."""

from datetime import date
import pytest
from namazflow.diyanet import calendar_key, get_calendar, parse_calendar
from namazflow.config import normalize
from namazflow.prayers import LABELS

HTML = """<table><tbody>
<tr><td>21 Ekim 2026 Çarşamba</td><td>10 Cemaziyelevvel 1448</td>
<td>06:09</td><td>07:49</td><td>13:15</td><td>15:57</td><td>18:31</td><td>19:59</td></tr>
<tr><td>22 Ekim 2026 Perşembe</td><td>11 Cemaziyelevvel 1448</td>
<td>06:11</td><td>07:50</td><td>13:15</td><td>15:56</td><td>18:29</td><td>19:58</td></tr>
</tbody></table>"""
TODAY = date(2026, 10, 21)


def test_official_calendar_columns_and_sunrise():
    days = parse_calendar(HTML, "darmstadt")
    day = days[TODAY]
    assert day.times["Fajr"].strftime("%H:%M") == "06:09"
    assert day.times["Asr"].strftime("%H:%M") == "15:57"
    assert day.sunrise.strftime("%H:%M") == "07:49"
    assert day.source == "Diyanet-Kalender · Darmstadt"
    assert "/11079/" in day.source_url
    assert day.timezone == "Europe/Berlin"


def test_rejects_bad_clock_and_conflicting_duplicate():
    with pytest.raises(ValueError):
        parse_calendar(HTML.replace("15:57", "25:57"), "darmstadt")
    with pytest.raises(ValueError):
        parse_calendar(HTML + HTML.replace("15:57", "15:58"), "darmstadt")
    with pytest.raises(ValueError):
        parse_calendar("<p>unavailable</p>", "darmstadt")


def test_official_cache_is_city_scoped_and_date_checked(tmp_path):
    config = normalize({"location": "darmstadt"})
    days = get_calendar(config, tmp_path, transport=lambda url: HTML, today=TODAY)
    assert not days[0].cached

    def fails(url):
        raise OSError("offline")

    cached = get_calendar(config, tmp_path, transport=fails, today=TODAY)
    assert cached[0].cached
    with pytest.raises(ConnectionError):
        get_calendar(
            normalize({"location": "niederhoechstadt"}),
            tmp_path,
            transport=fails,
            today=TODAY,
        )
    with pytest.raises(ConnectionError):
        get_calendar(config, tmp_path, transport=fails, today=date(2026, 11, 5))


def test_new_default_and_legacy_darmstadt_use_official_calendar():
    assert normalize({})["time_source"] == "ditib"
    assert calendar_key(normalize({"city": "Darmstadt"})) == "darmstadt"
    with pytest.raises(ValueError):
        calendar_key(normalize({"city": "Köln"}))


def test_turkish_prayer_names():
    assert list(LABELS.values()) == ["Sabah", "Öğle", "İkindi", "Akşam", "Yatsı"]
