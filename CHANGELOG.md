# Changelog

## 0.2.0 — 2026-10-21

- Replace painted hit areas with native controls and independent orb/panel windows.
- Fix drag/click separation, stable orb anchoring, close/Escape and explicit hide/restore actions.
- Restore an existing application on a second launch instead of opening duplicate widgets.
- Add Darmstadt / Niederhöchstadt (Eschborn) coordinate presets with isolated prayer caches.
- Redraw the crescent/star and Windows icon; label countdown units and target prayer.
- Add opening, hover and breathing animations with an opt-out setting.
- Use layout-managed spacing, vector toolbar icons and scrolling on smaller screens.
- Add German QuranEnc / HadeethEnc reminders, rotation, complete source details and validated offline cache.
- Add interaction, location, source-integrity and layout regression tests; adapt screenshot QA.

- Display Turkish prayer names throughout rows, countdown, detail views and notifications.
- Default to the published Diyanet calendars used by German DİTİB communities; use Eschborn for Niederhöchstadt, with labeled source and source-specific offline cache.
- Disable calculation controls for published-calendar mode and retain explicit AlAdhan opt-in.
- Isolate Windows build library lookup to prevent incompatible third-party ICU DLLs from being bundled; add packaged startup/exit smoke test to CI.
