"""Prayer-time retrieval, validation and timezone-aware countdown logic.

Times are obtained from AlAdhan; NEVER synthesize times when offline.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import re
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PRAYERS = ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
LABELS = {"Fajr": "Fajr", "Dhuhr": "Dhuhr", "Asr": "Asr", "Maghrib": "Maghrib", "Isha": "Isha"}
METHODS = {
    3: "Muslim World League",
    13: "Diyanet İşleri Başkanlığı",
    2: "Islamic Society of North America",
    4: "Umm Al-Qura",
    5: "Egyptian General Authority",
    12: "Union of Islamic Organisations of France",
}
CLOCK = re.compile(r"^\s*(\d{1,2}):(\d{2})(?:\s*\([^)]*\))?\s*$")


@dataclass(frozen=True)
class PrayerDay:
    day: date
    timezone: str
    times: dict[str, datetime]
    hijri: str = ""
    cached: bool = False

    def __post_init__(self):
        if set(self.times) != set(PRAYERS):
            raise ValueError("Incomplete prayer times")
        if sorted(self.times.values()) != list(self.times.values()):
            raise ValueError("Prayer times must be chronological")


def parse_day(payload: dict, requested: date, *, cached: bool = False) -> PrayerDay:
    """Validate the API response; reject corrupted, wrong-day and missing times."""
    data = payload["data"]
    timezone = data["meta"]["timezone"]
    zone = ZoneInfo(timezone)
    gregorian = data["date"]["gregorian"]["date"]
    if datetime.strptime(gregorian, "%d-%m-%Y").date() != requested:
        raise ValueError("API date mismatch")
    result = {}
    for prayer in PRAYERS:
        found = CLOCK.fullmatch(data["timings"][prayer])
        if not found:
            raise ValueError(f"Invalid time for {prayer}")
        hour, minute = map(int, found.groups())
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError("Invalid clock value")
        result[prayer] = datetime(requested.year, requested.month, requested.day, hour, minute, tzinfo=zone)
    hijri_date = data["date"].get("hijri", {})
    hijri = hijri_date.get("date", "")
    return PrayerDay(requested, timezone, result, hijri, cached)


def get_day(day: date, config: dict, cache_dir: Path, *, transport=None) -> PrayerDay:
    """Fetch with bounded network timeout; fall back to a verified local cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    method = int(config.get("method", 13))
    school = int(config.get("school", 1))
    city = config.get("city", "Darmstadt").strip()
    country = config.get("country", "Germany").strip()
    if not city or not country or method not in METHODS or school not in (0, 1):
        raise ValueError("Invalid prayer calculation settings")
    import hashlib
    key = hashlib.sha256(f"{day}|{city}|{country}|{method}|{school}".encode()).hexdigest()[:24]
    file = cache_dir / f"{key}.json"
    query = urlencode({"city": city, "country": country, "method": method, "school": school})
    url = f"https://api.aladhan.com/v1/timingsByCity/{day.strftime('%d-%m-%Y')}?{query}"
    try:
        if transport is None:
            req = Request(url, headers={"User-Agent": "NamazFlow/0.1 (prayer-widget)"})
            with urlopen(req, timeout=8) as response:
                payload = json.load(response)
        else:
            payload = transport(url)
        if payload.get("code") != 200:
            raise ValueError(f"Prayer time service returned: {payload.get('status')}")
        verified = parse_day(payload, day)
        temporary = file.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(file)
        return verified
    except (Exception) as error:
        if file.exists():
            try:
                return parse_day(json.loads(file.read_text(encoding="utf-8")), day, cached=True)
            except (ValueError, KeyError, OSError, TypeError):
                pass
        raise ConnectionError(f"Gebetszeiten für {day:%d.%m.%Y} nicht verfügbar: {error}") from error


def next_prayer(now: datetime, days: list[PrayerDay]):
    """Return (name, moment, seconds_remaining, fraction_of_interval) or None."""
    if now.tzinfo is None:
        raise ValueError("now must have timezone")
    items = sorted((moment, name) for entry in days for name, moment in entry.times.items())
    if not items:
        return None
    # Subtract UTC instants rather than wall time around DST transitions.
    utc = ZoneInfo("UTC")
    instant = now.astimezone(utc)
    past = [(dt, name) for dt, name in items if dt.astimezone(utc) <= instant]
    future = [(dt, name) for dt, name in items if dt.astimezone(utc) > instant]
    if not future:
        return None
    next_dt, name = future[0]
    remaining = max(0, int((next_dt.astimezone(utc) - instant).total_seconds()))
    if past:
        duration = (next_dt.astimezone(utc) - past[-1][0].astimezone(utc)).total_seconds()
        progress = 1 - remaining / duration if duration > 0 else 0.0
    else:
        progress = 0.0
    return (name, next_dt, remaining, max(0.0, min(1.0, progress)))


def countdown_text(seconds: int) -> str:
    seconds = max(0, seconds)
    h, rest = divmod(seconds, 3600)
    m = rest // 60
    return f"{h:02d}:{m:02d}" if h < 100 else f"{h}h"


def current_prayer(now: datetime, days: list[PrayerDay]) -> str | None:
    utc = ZoneInfo("UTC")
    events = sorted((dt, name) for entry in days for name, dt in entry.times.items()
                    if dt.astimezone(utc) <= now.astimezone(utc))
    return events[-1][1] if events else None
