# NamazFlow – quality review / design contract

## Original approved visual reference

The approved concept in the conversation shows a **small circular crescent / mosque icon with teal progress ring**, floating just outside the top-left of a **charcoal translucent prayer-times panel**. Five rows have thin gold glyphs, the active row has turquoise emphasis. Countdown card and Quran reminder sit underneath. Ornamentation is restrained and never harms readability.

The vector concept in this repository is an independent reconstruction, not the original generated photograph. Because the original source-photo bytes are not in GitHub, an exact pixel-level comparison against the original cannot presently be claimed.

## Three design evaluation rounds

The runner (scripts/visual_audit.py) renders **the actual Qt widget**, not HTML mockups. It captures:

| Iteration | UI state | Objective checks |
|---|---|---|
| 1 | Floating orb | transparent canvas, teal ring, gold icon, countdown |
| 2 | Expanded panel | dark glass, gold detail, accent, legible content area |
| 3 | Expanded after icon edit | customization visual change and repeated readability/palette gates |

The runner writes PNG screenshots and visual-qa.json. Optionally compare a *limited palette metric* with an exported original screenshot supplied via --reference-image. This is NOT a pixel-perfect similarity or human visual sign-off.

## Current release gates

- [x] Core implementation for five prayers, styles and icon editing.
- [x] Time data validation and explicit offline behavior.
- [x] Tests, screenshots and QA artifact scripts defined.
- [ ] GitHub Actions green; inspect after first successful run.
- [ ] Real Windows 10/11 drag, always-on-top, notifications, tray and autostart validated.
- [ ] Windows screenshots compared visually with the approved original at 100% and 150% DPI.
- [ ] Local mosque timetable differences resolved and configured.
- [ ] Code signing for public distribution.

**Verdict:** Initial app implementation and audit infrastructure; production-level Windows sign-off still open.
