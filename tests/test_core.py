from datetime import date, datetime, timedelta
import json
from zoneinfo import ZoneInfo

import pytest

from namazflow.config import normalize, load, save
from namazflow.prayers import (
    PRAYERS, PrayerDay, countdown_text, current_prayer, get_day, next_prayer, parse_day,
)


def sample_payload(day=date(2026, 10, 21)):
    return {
        "code": 200, "status": "OK",
        "data": {
            "date": {
                "gregorian": {"date": day.strftime("%d-%m-%Y")},
                "hijri": {"date": "09-05-1448"},
            },
            "meta": {"timezone": "Europe/Berlin"},
            "timings": {
                "Fajr": "06:03 (CEST)", "Dhuhr": "13:01 (CEST)",
                "Asr": "16:05 (CEST)", "Maghrib": "18:21 (CEST)",
                "Isha": "19:44 (CEST)",
            },
        },
    }


def test_parsing_verifies_all_five_prayers():
    day = date(2026, 10, 21)
    result = parse_day(sample_payload(day), day)
    assert result.timezone == "Europe/Berlin"
    assert list(result.times) == list(PRAYERS)
    assert result.times["Asr"].utcoffset() == timedelta(hours=2)


def test_rejects_wrong_day_and_missing_prayer():
    payload = sample_payload()
    with pytest.raises(ValueError, match="mismatch"):
        parse_day(payload, date(2026, 10, 22))
    del payload["data"]["timings"]["Isha"]
    with pytest.raises(KeyError):
        parse_day(payload, date(2026, 10, 21))


def test_rejects_malformed_time_and_nonchronological():
    payload = sample_payload()
    payload["data"]["timings"]["Fajr"] = "24:30"
    with pytest.raises(ValueError):
        parse_day(payload, date(2026, 10, 21))
    payload["data"]["timings"]["Fajr"] = "14:00"
    with pytest.raises(ValueError, match="chronological"):
        parse_day(payload, date(2026, 10, 21))


def test_countdown_and_current():
    day = parse_day(sample_payload(), date(2026, 10, 21))
    now = datetime(2026, 10, 21, 17, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    name, when, seconds, ratio = next_prayer(now, [day])
    assert name == "Maghrib"
    assert countdown_text(seconds) == "01:21"
    assert current_prayer(now, [day]) == "Asr"
    assert 0 < ratio < 1


def test_tomorrow_after_isha():
    today = parse_day(sample_payload(), date(2026, 10, 21))
    tomorrow = parse_day(sample_payload(date(2026, 10, 22)), date(2026, 10, 22))
    now = datetime(2026, 10, 21, 23, 59, tzinfo=ZoneInfo("Europe/Berlin"))
    result = next_prayer(now, [today, tomorrow])
    assert result[0] == "Fajr"
    assert result[1].date() == date(2026, 10, 22)


def test_no_fake_upcoming_time_and_aware_now():
    day = parse_day(sample_payload(), date(2026, 10, 21))
    now = datetime(2026, 10, 22, 23, 59, tzinfo=ZoneInfo("Europe/Berlin"))
    assert next_prayer(now, [day]) is None
    with pytest.raises(ValueError):
        next_prayer(datetime(2026, 10, 21, 17, 0), [day])


def test_cache_fallback_after_network_error(tmp_path):
    config = {"city": "Darmstadt", "country": "Germany", "method": 13, "school": 1}
    day = date(2026, 10, 21)
    first = get_day(day, config, tmp_path, transport=lambda _: sample_payload(day))
    assert not first.cached

    def fails(_):
        raise OSError("network is down")

    cached = get_day(day, config, tmp_path, transport=fails)
    assert cached.cached
    assert cached.times == first.times
    assert len(list(tmp_path.glob("*.json"))) == 1
    with pytest.raises(ConnectionError):
        get_day(day + timedelta(days=3), config, tmp_path, transport=fails)


def test_settings_roundtrip_with_custom_icons(tmp_path):
    file = tmp_path / "settings.json"
    original = normalize({"city": "  Köln  ", "icons": {"Asr": "lantern"}, "school": 0})
    save(original, file)
    restored = load(file)
    assert restored["city"] == "Köln"
    assert restored["icons"]["Asr"] == "lantern"
    assert restored["icons"]["Maghrib"] == "sunset"
    assert restored["school"] == 0
    assert normalize({"method": 999})["method"] == 13


def test_timezone_dst_instants():
    zone = ZoneInfo("Europe/Berlin")
    before = datetime(2026, 10, 25, 1, 30, tzinfo=zone)
    after = datetime(2026, 10, 25, 3, 30, tzinfo=zone)
    # Clocks move back 1 hour; elapsed time in UTC is 3 hours.
    assert int((after.astimezone(ZoneInfo("UTC")) -
                before.astimezone(ZoneInfo("UTC"))).total_seconds()) == 10800
