"""Published German-city Diyanet calendars used by DITIB communities.

Read the public calendar table, validate every date/time and cache per city.
Never silently substitute a different calculation when the calendar is unavailable.
"""

from datetime import date, datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from .prayers import PRAYERS, PrayerDay

CITIES = {
    "darmstadt": (11079, "darmstadt", "Darmstadt"),
    "niederhoechstadt": (11000, "eschborn", "Eschborn"),
}
MONTHS = {
    name: index
    for index, name in enumerate(
        (
            "Ocak",
            "Şubat",
            "Mart",
            "Nisan",
            "Mayıs",
            "Haziran",
            "Temmuz",
            "Ağustos",
            "Eylül",
            "Ekim",
            "Kasım",
            "Aralık",
        ),
        1,
    )
}


class CalendarTable(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag == "td" and self.row is not None:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.row is not None and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if len(self.row) == 8:
                self.rows.append(self.row)
            self.row = self.cell = None


def calendar_key(config):
    key = config.get("location", "")
    if key in CITIES:
        return key
    if config.get("country", "Germany").casefold() in ("germany", "deutschland"):
        city = config.get("city", "").casefold()
        if city == "darmstadt":
            return "darmstadt"
        if city in ("niederhöchstadt", "eschborn"):
            return "niederhoechstadt"
    raise ValueError(
        "Für den DİTİB-/Diyanet-Kalender bitte Darmstadt oder Niederhöchstadt auswählen."
    )


def calendar_url(key):
    identifier, slug, _ = CITIES[key]
    return f"https://namazvakitleri.diyanet.gov.tr/tr-TR/{identifier}/{slug}-namaz-vakitleri"


def parse_calendar(html, key, *, cached=False):
    parser = CalendarTable()
    parser.feed(html)
    result = {}
    zone = ZoneInfo("Europe/Berlin")
    for row in parser.rows:
        pieces = row[0].split()
        if len(pieces) < 3 or pieces[1] not in MONTHS:
            continue
        day = date(int(pieces[2]), MONTHS[pieces[1]], int(pieces[0]))
        values = []
        for text in row[2:]:
            if not re.fullmatch(r"\d{2}:\d{2}", text):
                raise ValueError("Ungültige Zeit im Diyanet-Kalender")
            hour, minute = map(int, text.split(":"))
            values.append(
                datetime(day.year, day.month, day.day, hour, minute, tzinfo=zone)
            )
        if not all(a < b for a, b in zip(values, values[1:])):
            raise ValueError("Diyanet-Zeiten sind nicht chronologisch")
        # Columns are Imsak, Güneş, Öğle, İkindi, Akşam, Yatsı.
        times = dict(zip(PRAYERS, (values[0], *values[2:])))
        item = PrayerDay(
            day,
            "Europe/Berlin",
            times,
            row[1],
            cached,
            source=f"Diyanet-Kalender · {CITIES[key][2]}",
            source_url=calendar_url(key),
            sunrise=values[1],
        )
        if day in result and result[day].times != times:
            raise ValueError("Widersprüchliche Diyanet-Kalendereinträge")
        result[day] = item
    if not result:
        raise ValueError("Keine gültigen Kalenderzeilen gefunden")
    return result


def get_calendar(config, cache_dir: Path, *, transport=None, today=None):
    key = calendar_key(config)
    today = today or datetime.now(ZoneInfo("Europe/Berlin")).date()
    file = cache_dir / f"diyanet-{key}.json"
    try:
        if transport:
            html = transport(calendar_url(key))
        else:
            request = Request(
                calendar_url(key),
                headers={"User-Agent": "NamazFlow/0.2 (desktop calendar)"},
            )
            with urlopen(request, timeout=12) as response:
                html = response.read(2_000_000).decode("utf-8-sig")
        days = parse_calendar(html, key)
        if today not in days:
            raise ValueError("Der Kalender enthält das heutige Datum nicht")
        cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"city": key, "html": html}, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(file)
        return sorted(days.values(), key=lambda day: day.day)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
            if payload["city"] != key:
                raise ValueError("Calendar location mismatch")
            days = parse_calendar(payload["html"], key, cached=True)
            if today not in days:
                raise ValueError("Kein gespeicherter Kalender für heute vorhanden")
            return sorted(days.values(), key=lambda day: day.day)
        except (OSError, ValueError, TypeError, KeyError):
            raise ConnectionError(
                "DİTİB-/Diyanet-Zeiten derzeit nicht verfügbar. Bitte später aktualisieren."
            ) from exc
