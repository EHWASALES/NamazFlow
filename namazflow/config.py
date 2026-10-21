"""Persistent, user-controlled settings and Windows autostart."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

DEFAULTS = {
    "city": "Darmstadt",
    "country": "Germany",
    "method": 13,
    "school": 1,
    "theme": "midnight",
    "symbol": "crescent",
    "notifications": True,
    "autostart": False,
    "pinned": True,
    "x": None,
    "y": None,
    "quote": True,
    "icons": {"Fajr": "sunrise", "Dhuhr": "sun", "Asr": "afternoon", "Maghrib": "sunset", "Isha": "crescent"},
}
THEMES = ("midnight", "emerald", "sand")
SYMBOLS = ("crescent", "mosque", "star", "lantern")


def data_path() -> Path:
    root = os.environ.get("APPDATA") or str(Path.home() / ".config")
    return Path(root) / "NamazFlow"


def normalize(raw: dict | None) -> dict:
    data = {**DEFAULTS, "icons": DEFAULTS["icons"].copy()}
    if not isinstance(raw, dict):
        return data
    for key in DEFAULTS:
        if key == "icons":
            continue
        if key in raw and type(raw[key]) is type(DEFAULTS[key]):
            data[key] = raw[key]
        elif key in ("x", "y") and (raw.get(key) is None or isinstance(raw.get(key), int)):
            data[key] = raw.get(key)
    data["city"] = data["city"].strip()[:120] or DEFAULTS["city"]
    data["country"] = data["country"].strip()[:120] or DEFAULTS["country"]
    if data["method"] not in (2, 3, 4, 5, 12, 13):
        data["method"] = 13
    if data["school"] not in (0, 1):
        data["school"] = 1
    if data["theme"] not in THEMES:
        data["theme"] = "midnight"
    if data["symbol"] not in SYMBOLS:
        data["symbol"] = "crescent"
    if isinstance(raw.get("icons"), dict):
        for prayer in DEFAULTS["icons"]:
            icon = raw["icons"].get(prayer)
            if icon in ("sunrise", "sun", "afternoon", "sunset", "crescent", "mosque", "star", "lantern"):
                data["icons"][prayer] = icon
    return data


def load(path: Path | None = None) -> dict:
    path = path or data_path() / "settings.json"
    try:
        return normalize(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {**DEFAULTS, "icons": DEFAULTS["icons"].copy()}


def save(settings: dict, path: Path | None = None) -> None:
    path = path or data_path() / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(normalize(settings), indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def set_windows_autostart(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    if getattr(sys, "frozen", False):
        command = f'"{sys.executable}"'
    else:
        module = Path(__file__).resolve().parent.parent / "main.py"
        command = f'"{sys.executable}" "{module}"'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, "NamazFlow", 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, "NamazFlow")
            except FileNotFoundError:
                pass
