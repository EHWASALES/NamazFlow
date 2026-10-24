# NamazFlow

A calm, elegant **floating prayer-times companion for Windows 10/11**, inspired by an approved dark-glass, gold-and-teal desktop concept.

![NamazFlow visual concept](docs/namazflow-concept.svg)

> **Status:** v0.2 desktop interaction update. The illustration shows **demonstration values**, not actual prayer times. Never use the concept graphic to plan prayers.

## Features

- A single draggable floating orb, always on top, with an elegant progress ring and live countdown.
- Click to expand into an ornamental translucent panel with **Sabah, Öğle, İkindi, Akşam and Yatsı**, today's Gregorian/Hijri dates and a reminder.
- Current-prayer highlighting, tomorrow's Fajr after Isha, and DST-aware countdowns.
- Crisp drawn vector symbols, individual editable prayer icons, floating-icon style, three themes.
- City/country, calculation method (Diyanet, MWL, ISNA, Umm Al-Qura, etc.) and Hanafi/standard Asr.
- System tray, optional autostart, optional prayer-start notifications, locally saved settings.
- Validated cached days for offline use **without inventing times**. If current-day data is unavailable, display a warning.
- After a failed or cached prayer-time response, retry automatically every 30 seconds after request completion. Successful complete responses restore the normal 30-minute refresh interval. Retry timing uses a monotonic clock and requests run in the background.
- Validated Diyanet cache data appears immediately at startup while the network refresh runs. Failed refreshes retain matching verified dates in memory; cache write failures do not discard valid live responses. Duplicate refresh clicks are coalesced. Bounded diagnostic logs are saved under `%APPDATA%\NamazFlow\NamazFlow.log`.

## Installation (development)

Requires **Python 3.10+**, Windows 10 or 11.

~~~powershell
git clone https://github.com/EHWASALES/NamazFlow.git
cd NamazFlow
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
~~~

For a packaged executable, use the **Windows build** artifact from GitHub Actions once the workflow succeeds.

## Controls

- **Click orb** to open/close the panel; **drag orb** to move it.
- **Gear** opens settings; **×** or **Escape** collapses the panel; **pencil** changes a prayer icon.
- **Click a prayer row** for its time and location. **Zitat & Quelle ansehen** opens the full, unabridged source text.
- **Right-click** for separate open, collapse, hide, restore and exit actions. The tray icon or a second launch restores a hidden Flow.
- The widget stores configuration under %APPDATA%\NamazFlow on Windows.
- Enable **Mit Windows starten** in settings to launch NamazFlow automatically when you sign in to Windows. The preference is stored locally for your Windows account.

Each prayer has its own gold calligraphic emblem with a teal highlight for the current prayer. The Turkish labels remain beside them. The floating orb shows the upcoming prayer's emblem; a 650ms fade and slight vertical motion accompany each change. The current prayer's emblem tint also transitions smoothly. Disabling animations makes changes immediate. Turn off “Arabische Gebetsnamen mit goldenen Ornamenten” in settings to return to editable symbols. The bundled [Amiri](https://github.com/aliftype/amiri) typeface provides fallback lettering under the SIL Open Font License; its license is included in `namazflow/fonts/OFL.txt`. Emblem art and its generation notes live in `namazflow/assets/calligraphy/`.

## Calculation and reliability

Optional calculated times are fetched from the [AlAdhan Prayer Times API](https://aladhan.com/prayer-times-api) for the configured **city, country, method and Asr school**, or explicit coordinates for the Darmstadt / Niederhöchstadt (Eschborn) presets. They can differ from your local mosque/DITIB timetable. Configure the method and verify local differences. Yesterday, today and tomorrow are loaded on a background thread. Validated replies are cached per date and method. If the service fails, **only previously validated cached data** is displayed with an offline indication; missing values stay blank.

Network use: city/country or the selected preset coordinates are sent to AlAdhan. QuranEnc and HadeethEnc receive requests for selected public text IDs. No ads, tracking, analytics, account, GPS access or API key.

## Tests

~~~bash
pip install -r requirements-dev.txt
pytest -q
# On a machine with a Qt platform:
python scripts/visual_audit.py --strict
~~~

CI tests logic on Linux/Windows, renders Qt offscreen, captures three reproducible screenshot stages and publishes PNG/JSON artifacts.

## Visual quality and concept parity

- Reference: the approved image in the original ChatGPT project conversation. A vector concept is included as docs/namazflow-concept.svg.
- Targets: elevated translucent dark panel, compact moon/mosque orb, gold Islamic-inspired linework, teal progress/accent, readable typography, five prayer rows and a countdown.
- Three-stage QA: orb, expanded glass panel, custom-symbol variant. Generated by scripts/visual_audit.py.
- Optional palette comparison with approved screenshot: python scripts/visual_audit.py --reference-image path/to/concept.png. This is not a pixel-perfect similarity score.
- Human review on a **real Windows 11 desktop at 100% and 150% scaling** is required before declaring production readiness.

Read docs/quality-review.md for limitations and acceptance criteria.

## Packaging

CI publishes an unsigned Windows executable. Tagged builds v* trigger a Windows setup via PyInstaller and Inno Setup. Without code signing, Windows SmartScreen may show a warning. Managed machines should respect their security policy.

## License

No open-source license is granted yet. Copyright belongs to the repository owner.

## v0.2 desktop update

- The orb and panel are independent windows: opening the panel never moves the orb.
- Drag the visible orb to move it; its position is retained and kept inside an available screen.
- Switch directly between **Darmstadt** and **Niederhöchstadt · Eschborn** using the dropdown or right-click menu. By default these locations use the published Diyanet calendars for Darmstadt and Eschborn, respectively. The optional AlAdhan mode uses representative town-centre coordinates. Caches remain isolated by city and source. Existing custom cities remain supported.
- The orb reads **bis Öğle · 3h 33m**, for example: remaining hours and minutes, not a clock time. The panel spells out units and shows the target time.
- The new crescent and five-point star replace the crossed minaret strokes. All toolbar icons are vectors and do not depend on symbol fonts.
- The panel fades/slides in, the orb responds to hover with a soft halo, and prayer rows animate on hover. Animations can be disabled in settings.
- Native layouts handle spacing; prayer times scroll on small or highly scaled displays while the quote and its source controls stay visible at the bottom of the open panel.

### Quran and hadith reminders

German source texts are loaded in the background from [QuranEnc](https://quranenc.com/en/home/api/) (Bubenheim/Elyas) and the official [HadeethEnc API](https://github.com/islamhouse-dev/hadith-api). Select Quran, hadith, or alternating sources in settings. The refresh button advances the selection; automatic rotation runs every five minutes. Six verses and six curated hadith entries are available in this version.

Each text has its verse reference or collection attribution, publisher, and a direct source link. HadeethEnc entry IDs are not collection hadith numbers. Translated collection names are shown for readability; the original API attribution remains in the detail view. The full text appears in a scrollable quote area, and the detail view includes the full source information. API responses are validated against the requested ID before display or caching. On failure the matching cached response is used and marked; without one, the UI displays an unavailable message, never an invented quote.

### Update checks

`python -m pytest -q` includes regression checks for dragging, click/close/Escape, hide/restore, location switching, stale replies, coordinate requests, separate caches, source identity, full-text preservation and layout boundaries. `python scripts/visual_audit.py --strict` captures the real orb and panel in three demonstration states; these screenshots do not contain live prayer data or real religious quotations.


### DİTİB Deutschland: published prayer calendar (default)

The default source is the **published Diyanet calendar for German cities**, as linked by DİTİB communities such as [DITIB Heidelberg](https://ditib-hd.de/gebetszeiten/). This app is independent and is not an official DİTİB product.

- Darmstadt: [Diyanet calendar 11079](https://namazvakitleri.diyanet.gov.tr/tr-TR/11079/darmstadt-namaz-vakitleri).
- Niederhöchstadt: [Eschborn calendar 11000](https://namazvakitleri.diyanet.gov.tr/tr-TR/11000/eschborn-namaz-vakitleri), explicitly labeled as Eschborn.
- Turkish display names: **Sabah, Öğle, İkindi, Akşam, Yatsı**. Sabah uses the calendar's **İmsak** column. Its detail view also shows **Güneş** (sunrise).
- The complete public calendar table is fetched in the background, parsed without executing page scripts, checked for valid dates and chronological times, and cached per city. Current/tomorrow rows drive the widget. On service failure only a valid matching cached calendar is accepted. No silent switch to approximate calculated times.
- Selecting this source ignores AlAdhan calculation method and Asr-school controls, which are disabled. Users may explicitly choose AlAdhan in settings.

The published timetable defines prayer beginnings, not a mosque's separately scheduled congregational prayer. Parser changes may be necessary if the publisher changes the table format.

### Reproducible Windows packaging

Run `python scripts/build_windows.py` before compiling `build/NamazFlow.iss`. The build isolates its native-library lookup from unrelated applications on the host PATH, then runs the packaged `--smoke-test` to verify Qt startup and a clean explicit exit. CI uses the same build entrypoint.
