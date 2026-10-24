# Changelog

All notable changes to SCS Tools (Aristodemus).

## 2.5.1a (2026-10-24), material fixes and a larger archive browser

### New
- **Larger archive browser.** The magnifier buttons at the top right of the game-archive browser
  make it larger or smaller (three sizes, with more rows in the larger ones). The size is kept for
  the next import.
- **Full names on hover.** Long file and folder names are cut off in the archive browser; hovering
  over an entry now shows its full name and its path in the archive.

### Fixes
- **Far colour of terrain-style materials is no longer almost black.** Models converted with
  ConverterPIX carry the far colour (`aux[2]` of `...tg0`/`tg1` materials) and `diffuse_secondary`
  in linear colour, while SCS's conversion tool expects them in sRGB like all other colours. After
  conversion they came out about ten times too dark (0.10 became 0.01). They are now converted on
  import, like ConverterPIX does for the other colours.
- **The legacy (Material) format writes the far colour in its own units.** The legacy format stores
  `aux[2]` far colour and far specular power as 0-255 values; the add-on wrote 0-1, which the
  conversion tool turned into black. Files in the legacy format are read the same way.
- **Leaves keep their LOD selector.** Re-importing an AutoMat export kept only the first value of
  `lod_selector` (`aux[1]` on `eut2.leaves`).
- **Texture generation keeps its LOD switch distance.** Re-importing an AutoMat export lost
  `lod_switch_distance` (the 4th value of `aux[0]` on `...tg0` materials).
- **Sun-bounce flares no longer get a depth bias.** `eut2.flare.sun.bounce` stores its animation
  sheet setup in `aux[0]`; AutoMat also wrote it as `depth_bias` (30), which the game's material
  doesn't have.
- **Animated water foam converts.** `animsheet_cfg_loop_offset_rnd`, used by newer `fadesheet`
  materials, isn't known to SCS's conversion tools (2.21), so the model's `.pmd` wasn't written. It
  is left out when 0 (as in the game's materials) and gets a warning otherwise.
- **Container decals in the legacy format convert.** The conversion tool can't read
  `amod_decal_blending_factors` (`aux[0]`) of `eut2.dif.spec.amod.dif.spec.add.env...` from the
  legacy format; it is now left out there with a warning. AutoMat keeps it.
- **Export no longer stops with "Unable to write unit property of type NoneType".** Materials
  imported with a shader the add-on has no preset for ("imported shader", for example the
  terrain transition `eut2.dif.spec.weight.weight.dif.spec.weight.fmtsnmapcalc.tg0.tg1.heightmap`
  in `heavy_machinery_service_01_at`) made the AutoMat export crash on their substance. The
  substance is written from the material's substance setting, and empty values are skipped with a
  warning.
- **Legacy export of imported shaders follows the same rules as other materials.** The edge-blend /
  heightmap flavour, its heightmap textures and settings of the newer material format are left
  out with a warning, so SCS's conversion tool accepts the material. Use AutoMat to keep them.
- **Warning for flavours SCS's conversion tools can't convert.** Some newer game materials use the
  `fmtsnmapcalc` flavour, which conversion tools 2.21 (the latest) can't decode, so the model's
  `.pmd` isn't written. The export now says so and names the material.

## 2.5.1 (2026-10-23), import from game archives

### New
- **Import straight from game archives.** **File > Import > SCS Models from Game Archives (*.scs)**
  browses `.scs` archives, converts the chosen model (and its animations) with ConverterPIX and
  imports it. Based on 50keda's ConverterPIX Wrapper, now built in, so the separate add-on isn't
  needed.
- **ConverterPIX is included** for Windows (64- and 32-bit) and Linux. It no longer has to be
  downloaded on first use; a newer version can still be downloaded from the import window.

### Fixes
- **No more "WinError 193: %1 is not a valid Win32 application".** The wrapper saved whatever
  GitHub returned as `converter_pix.exe`, so a failed download replaced the program with a web
  page. Downloads are now checked before they are used, and a broken copy falls back to the
  included one.
- **Animations can be picked again.** In the wrapper's archive browser, checkboxes couldn't be ticked
  in Blender 5, so animations were never converted. Animations are now ticked by clicking them.
- **Disabling or reloading the add-on removes its File menu entries.** The import and export
  entries were removed from the wrong menus, so they stayed behind.

### Licence
- The add-on is now distributed under **GPL-3.0**, because it includes ConverterPIX Wrapper code
  (GPL-3.0). The original SCS Blender Tools files are GPL-2.0 or later, which allows this.
  ConverterPIX is included under the LGPL-3.0.

## 2.5.0d (2026-10-23), AutoMat material fix

### Fixes
- **Traffic lights and other preset-less materials convert with AutoMat.** Materials whose effect
  has no shader preset in the add-on (for example the `eut2.lamp` traffic-light lenses) skipped the
  conversion to the newer format, so AutoMat wrote old setting names (`add_ambient`, `aux[n]`) and
  SCS's conversion tool stopped with "cannot read amat": the model's `.pmd` and collision weren't
  written. They now get the same conversion as all other materials. The default material used for
  faces without a material had the same problem.

## 2.5.0c (2026-10-23), prefab conversion fix

### Fixes
- **Exported models and prefabs convert again.** Several things in the exported material files
  stopped SCS's conversion tool, so only the `.pmg` was written:
  - AutoMat wrote some old slot names the game doesn't accept (`aux[0]`, `aux[2]`). They are now
    written as the game's names: `far_color` / `far_specular_power` on terrain-style materials
    and `amod_decal_blending_factors` on alpha-modulated decals.
  - AutoMat wrote whole-number settings (`queue_bias`, `is_terrain_material`, heightmap shape
    types and `is_dynamic_road`) as decimals. They are written as whole numbers now.
  - AutoMat no longer writes `is_dynamic_road` and `lod_switch_distance` when they are 0, which
    matches the game's own materials.
  - The legacy (Material) format kept the edge-blend / heightmap flavour in the effect name, but
    it can't store its settings. The flavour and its heightmap textures are now left out, with a
    warning. Use AutoMat to keep them.
  - The legacy format wrote `is_dynamic_road`, which the conversion tool can't read from that
    format. It is now left out (with a warning when it's set). Use AutoMat to keep it.
  - The legacy format could write more values than an `aux` setting holds (models converted with
    ConverterPIX carry four values where the game stores two, for example the mult UV scale on
    road materials). It now writes exactly as many values as the setting holds.
- **Prefab signs keep their model.** Sign models, semaphore profiles and trigger actions that
  aren't in the loaded sign / semaphore / trigger libraries used to be exported empty. They are
  now kept as imported.
- **Double-sided surfaces keep their back faces.** When a model had faces that share their
  vertices with a face pointing the other way (fences, signs, foliage), the import put those back
  faces in a separate object that was never exported. They are now joined to their object again.
  Back faces that use their own vertices at the same positions as the front face were thrown away
  as duplicates on import; they are now recognised as back faces too.
- **Spawn point flags are kept.** Only "Custom" spawn points read their depot type, parking
  difficulty, trailer length and rule on import, but every spawn point writes them on export, so
  the others came back with different flags (for example 0 became 1). They are now read for all
  spawn points.
- **Window interior materials export correctly.** Interior materials (`eut2.interior...`) wrote
  their room size into the wrong setting. The room size, atlas size and glass colour now go to
  the right settings.
- **Prefab curves only link to curves of the same prefab.** In some cases (for example after
  importing several prefabs into one file) export could stop with an error, or curves could be
  linked to curves from another prefab.
- **AutoMat is now the default export format.**

## 2.5.0b (2026-10-22), test release fix

### Fixes
- **Importing AutoMat files now works.** Models exported with the AutoMat format (and other files in
  the newer material format) used to import with empty materials: no values, textures or
  substances. AutoMat entries are now read and converted, so all looks come back as they were
  exported, including edge blend / heightmap and secondary diffuse settings.
- The file reader now understands multi-line text blocks (`"""..."""`), which AutoMat entries use.

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
