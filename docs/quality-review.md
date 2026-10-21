# NamazFlow 0.2 — verification record

## Requested desktop changes

The user's installed version could not reliably drag or close its menus. The new version separates the orb and panel into independent windows, replaces painted hit areas with native controls, adds distinct collapse/hide/restore/exit actions, and retains the orb position when opening its panel. The crescent/star replaces crossed minaret strokes. Countdown labels specify the target prayer and remaining hours/minutes. Native layout and scroll handling keep controls reachable on smaller displays. Toolbar icons are drawn vectors rather than font glyphs.

Turkish display names are Sabah, Öğle, İkindi, Akşam and Yatsı. Sabah uses İmsak; its detail view includes Güneş (sunrise). The user requested DİTİB Deutschland times, so the default is the published Diyanet calendar for Darmstadt, or Eschborn for Niederhöchstadt. The source city is shown in the panel. AlAdhan remains an explicit alternative.

## Checks performed on 21 October 2026

- 31 regression tests pass locally on Windows: original prayer calculations/DST, drag vs click, stable orb placement, close/Escape, separate hide/restore/exit, preset switching, stale asynchronous responses, layout boundaries, small-screen scrolling, Turkish labels, source identity, official calendar parsing, chronology and city/date-isolated offline caches.
- Three screenshot states pass the strict palette/transparency gates: orb, expanded panel and personalized symbols. These are real Qt renders with labeled demonstration data, not real religious quotations or current prayer times. Screenshot gates were also run with 150% offscreen scaling; small logical screens use scrolling.
- Native Windows pointer QA exercised orb opening, dragging twice, closing via ×, right-click menu, Flow hiding, and selecting Niederhöchstadt. The accessibility tree confirmed Turkish labels and the live Eschborn calendar after the switch.
- Live checks cover both official calendars and both optional coordinate profiles; all six QuranEnc verses and six HadeethEnc entries return attributed German source text.
- Example of the source distinction: on 21 October 2026 Darmstadt's official İkindi is 15:57, while the earlier AlAdhan Hanafi setting produced 16:39. Merely renaming the calculation method would not satisfy the user's calendar request.
- The first packaged launch exposed a mismatched ICU DLL collected from another application's PATH. The Windows build now isolates native-library discovery and must pass packaged startup/exit smoke testing. The corrected executable passes. A second normal launch exits successfully and restores the existing instance without adding another application process.
- Inno Setup compiles 0.2.0. Local update returns success; the Windows uninstall entry is 0.2.0 and the installed executable hash matches the tested build. No restart is required.

## Sources and limitations

Published calendars: https://namazvakitleri.diyanet.gov.tr/tr-TR/11079/darmstadt-namaz-vakitleri and https://namazvakitleri.diyanet.gov.tr/tr-TR/11000/eschborn-namaz-vakitleri. The app is independent, not an official DİTİB product. These are prayer beginning times, not separately scheduled congregational times.

Quotes come from QuranEnc (Bubenheim/Elyas) and HadeethEnc. Previews may be shortened with an ellipsis; the detail view preserves the complete text and source. Original API attribution is retained alongside translated collection names. Network failure never generates substitute religious text or switches the selected prayer-time source silently.

The original generated concept photograph is not in this repository. Palette gates are not a pixel-perfect similarity score. Code signing, broad Windows hardware coverage, and mosque-specific congregational schedules are outside these checks. The public calendar parser may need maintenance if its publisher changes the table format.
