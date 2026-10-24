# Prayer calligraphy emblems

Created for NamazFlow: four emblems use the built-in ImageGen tool, and the dawn emblem uses native shaped Amiri lettering and original vector flourishes. Transparent PNG originals are shipped with the application. Qt scales and tints the artwork at runtime; no image service is needed to run the app.

The visible Turkish labels and accessible Arabic names identify each prayer. These are decorative calligraphy emblems, not scripture.

## Prompt set

Shared brief: A single sophisticated Arabic calligraphic monogram in the artistic direction of Assassin's Creed Mirage's Arabic emblems. Sculptural intertwined thuluth strokes, elongated tapering uprights, hooked descenders, nested curves, diamond dots and generous negative space. Correct right-to-left joining. Flat warm gold, no surrounding badge or frame, no Latin text, isolated on a transparent square canvas with safe margins.

- `fajr.png`: الفجر — original vector monogram with tall tapered alif/lam strokes, a nested returning curve and a sweeping tail woven around shaped Amiri outlines for فجر. Fine transparent channels retain the body and its dots at intersections. Run `python scripts/draw_fajr_emblem.py` to save the refined artwork to `qa-artifacts/fajr-native-refined.png`, then copy the selected output to this folder. The other four emblems are the visual reference for proportions and pen weight.
- `dhuhr.png`: الظهر — balanced upright silhouette, nested curves and a soaring central stroke. Refinement: one dot above ظ; remove the extra bottom diamond and stray speckles.
- `asr.png`: العصر — compact diagonal silhouette with a sweeping returning tail. No dots or diacritics; the letters ا ل ع ص ر contain no dots.
- `maghrib.png`: المغرب — wide layered flowing silhouette with a deep bowl and slender rising strokes. Refinement: one dot above غ and one below ب; remove extra dots and stray speckles.
- `isha.png`: العشاء — intricate ascending silhouette with intertwined arches. Refinement: three dots above ش; a real final hamza ء, no decorative bottom diamond or stray speckles.

## Rendering and behavior

- The panel uses `PrayerCalligraphy`; `calligraphy.py` shares the same artwork with the floating orb and tray icon.
- Gold is the resting state; the active prayer transitions to the theme accent over 520ms.
- The orb crossfades and shifts the outgoing/incoming emblems over 650ms using an eased curve.
- Reduced motion snaps to the final state. The first available prayer appears immediately.
- Missing artwork falls back to shaped Amiri lettering in the list and the user's selected symbol in the orb.

Run `python -m scripts.calligraphy_preview` to capture the emblem sheet, full panel and an animated orb demo using demonstration data.
