# Changelog

All notable changes to SCS Tools (Aristodemus).

## 2.5.0a (2026-10-22), test release for ETS2 / ATS 1.61

The first public test release of this update. It is based on Michaleczeq's fork of
SCS Blender Tools (2.4, upstream commit aeadde03, unofficial update 9). Blend files saved with
any 2.4 version are migrated when opened.

### Universal (UN) roads
- New **Road Look Preview** panel (Object properties > SCS Variants). It reads
  `/def/world/road_look*.sii` from the project base path and the Additional Data Folders. It
  shows the road looks using the open template model, plus:
  - their lane variants and the line variants each one allows;
  - the additional parts;
  - the overlay schemes.
- The additional parts can be toggled one by one or all at once. Clicking **All** again goes
  back to your previous selection.
- Only one overlay scheme is shown as active at a time, even when schemes share parts.
- "Filter Variant Grid" limits the grid to the line variants a lane variant allows.
- UN road lines render in the viewport. The `is_dynamic_road` attribute is supported, and
  integer attributes from ConverterPIX are read as integers.
- **Road Line Country** setting, for previewing a country's line textures. Only folders that
  actually contain line textures are listed.

### Variants
- **Preview Active Variant**: clicking a variant shows only its parts in the viewport. Switching
  preview off restores the view from before it was switched on.
- **Reset View** shows every part and clears the preview's additional parts and overlay scheme.
- **Variant log**: writes every variant, part and object, with its visibility, to a text block
  (`SCS_variants_log`).
- New **Variant Grid** (every part against every variant):
  - part and variant filters with wildcards;
  - columns sized to the panel, with paging;
  - row and column toggles, where a second click restores what was there before;
  - "Restore before 'all' toggles";
  - variant duplication;
  - warnings for empty or duplicate variants and parts in no variant.
- SCS Variants is reorganised into closed-by-default sub-panels: Variant Grid, Road Look Preview,
  Additional Parts and Classic Part Table (the original variant-part table).

### Materials
- Attributes of newer game materials are kept on import: `heightmap_*`, `diffuse_secondary`,
  `is_terrain_material` and other attributes the shader preset doesn't define. They are shown in
  the material panel. They used to be dropped.
- The AutoMat export writes them back. The legacy material export skips them, with a warning in
  the export report.
- The export settings warn when the legacy material format is selected, list the materials that
  would lose settings, and offer a **Switch to AutoMat** button.
- Edge-blend / heightmap ("HMAP") shader flavour enabled in the shader presets.
- Binary TOBJ files are read.
- Textures that aren't found locally keep their game path on export instead of an empty path.

### Paths
- **Additional Data Folders**: extra folders (extracted game archives, other mods) searched for
  textures and definitions after the project base path. TOBJ files are never written into them.

### Fixes
- Blender 5:
  - crash creating looks;
  - crash on edge models (properties that can't be unset);
  - crash closing the preferences window.
- Panels staying greyed out: the config lock is always released and a watchdog clears a stuck
  lock.
- First import: the file browser no longer loses its Import / Cancel buttons.
- AutoMat export crash on materials with texture generation (`lod_switch_distance`).
- Child objects of nested SCS roots are found correctly.
- Invalid escape sequence warnings on Python 3.12+.
