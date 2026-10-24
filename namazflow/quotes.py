"""German source texts, fetched verbatim with attribution and validated offline cache.

QuranEnc (Bubenheim/Elyas) and HadeethEnc official public APIs. No invented texts.
"""

from dataclasses import dataclass, replace
import html
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

QURAN_REFS = ((94, 5), (94, 6), (2, 152), (20, 14), (13, 28), (93, 5))
HADITH_IDS = (66520, 66538, 66541, 3716, 3591, 66511)
# Translated collection names from the corresponding API attribution fields.
# Entry IDs are HadeethEnc IDs, not hadith numbers within these collections.
HADITH_COLLECTIONS = {
    66520: "Al-Bukhari und Muslim",
    66511: "Al-Bukhari und Muslim",
    66538: "Ahmad, at-Tirmidhi, an-Nasa'i, Ibn Majah, Ibn Hibban und al-Hakim",
    66541: "Ahmad, at-Tirmidhi, Ibn Majah und Ibn Hibban",
    3716: "Al-Bukhari",
    3591: "Muslim",
}


@dataclass(frozen=True)
class Quote:
    text: str
    reference: str
    url: str
    kind: str
    publisher: str
    cached: bool = False
    original_attribution: str = ""


def clean(value):
    if not isinstance(value, str):
        raise ValueError("Missing source text")
    value = html.unescape(re.sub(r"<[^>]*>", "", value))
    value = " ".join(value.split())
    if not value or len(value) > 20000:
        raise ValueError("Invalid source text")
    return value


def quote_spec(index, source="mixed"):
    kind = (
        source
        if source in ("quran", "hadith")
        else ("quran" if index % 2 == 0 else "hadith")
    )
    slot = index // 2 if source == "mixed" else index
    if kind == "quran":
        sura, aya = QURAN_REFS[slot % len(QURAN_REFS)]
        return (
            kind,
            (sura, aya),
            f"https://quranenc.com/api/v1/translation/aya/german_bubenheim/{sura}/{aya}",
        )
    identifier = HADITH_IDS[slot % len(HADITH_IDS)]
    return (
        kind,
        identifier,
        f"https://hadeethenc.com/api/v1/hadeeths/one/?language=de&id={identifier}",
    )


def parse_quote(payload, kind, identity):
    if kind == "quran":
        row = payload["result"]
        sura, aya = identity
        if (int(row["sura"]), int(row["aya"])) != (sura, aya):
            raise ValueError("Verse identity mismatch")
        return Quote(
            clean(row["translation"]),
            f"Koran {sura}:{aya}",
            f"https://quranenc.com/de/browse/german_bubenheim/{sura}#{aya}",
            kind,
            "QuranEnc · Bubenheim / Elyas",
        )
    if int(payload["id"]) != identity:
        raise ValueError("Hadith identity mismatch")
    attribution = clean(payload["attribution"])
    grade = clean(payload["grade"])
    collection = HADITH_COLLECTIONS.get(identity, attribution)
    return Quote(
        clean(payload["hadeeth"]),
        f"Hadith · {collection} · {grade}",
        f"https://hadeethenc.com/de/browse/hadith/{identity}",
        "hadith",
        f"HadeethEnc · Eintrag {identity}",
        original_attribution=attribution,
    )


def get_quote(index: int, cache_dir: Path, source="mixed", *, transport=None):
    kind, identity, url = quote_spec(index, source)
    token = (
        "-".join(map(str, identity)) if isinstance(identity, tuple) else str(identity)
    )
    file = cache_dir / f"{kind}-{token}.json"
    try:
        if transport:
            payload = transport(url)
        else:
            request = Request(url, headers={"User-Agent": "NamazFlow/0.2"})
            with urlopen(request, timeout=8) as response:
                payload = json.load(response)
        quote = parse_quote(payload, kind, identity)
        cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = file.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(file)
        return quote
    except (OSError, ValueError, KeyError, TypeError) as exc:
        try:
            cached = parse_quote(
                json.loads(file.read_text(encoding="utf-8")), kind, identity
            )
            return replace(cached, cached=True)
        except (OSError, ValueError, KeyError, TypeError):
            raise ConnectionError(
                "Zitat derzeit nicht verfügbar. Bitte später erneut versuchen."
            ) from exc
