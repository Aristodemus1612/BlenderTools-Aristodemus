# SCS Tools (Aristodemus): User Guide

*Version 2.5.1a. Back to the [README](../README.md).*

This guide covers the features this update adds. For everything else (SCS roots, locators,
prefabs, export basics), the original documentation on the
[SCS modding wiki](http://modding.scssoft.com/wiki/Documentation/Tools/SCS_Blender_Tools) still
applies.

## Contents
1. [Setting up paths](#1-setting-up-paths)
2. [Looks and variants](#2-looks-and-variants)
3. [Variant preview](#3-variant-preview)
4. [Variant Grid](#4-variant-grid)
5. [Road Look Preview (UN roads)](#5-road-look-preview-un-roads)
6. [UN road lines](#6-un-road-lines)
7. [Newer material settings and exporting](#7-newer-material-settings-and-exporting)
8. [Importing from game archives](#8-importing-from-game-archives)

---

## 1. Setting up paths

Open the 3D view sidebar (N), go to the **Tool** tab and find **SCS Global Settings > Path
Settings**. There are three places the add-on can read from:

- **SCS Project Base Path**: your mod's working folder, as with the official tools. Exported
  files and new TOBJs are written here.
- **Alternative bases** (the magnet button next to the path): folders named `base`,
  `base_share` or `base_vehicle` next to your project folder, or one level above it. This is
  the original tools' way of reaching game data.
- **Additional Data Folders**: any extra folders, separated by `;`. Use the **+** button to add
  one. Typical choices are extracted game archives (`base`, `def`, DLC), another mod you build
  on, or a folder of your own road lines. **They are only read, never written to.**

### How a file is found

Paths inside models and definitions always start at the top of the game data, never at the model
itself:

| What | Path it asks for |
|---|---|
| UN road line texture | `/road_template/un/default/lines_local_difopa.tobj` |
| Road surface texture | `/material/road/...` |
| Road looks | `/def/world/road_look*.sii` |

For each one the add-on checks, in order:
1. the Project Base Path;
2. the alternative bases;
3. each Additional Data Folder, in the order listed.

**The first folder that has the file wins.** A folder that doesn't contain it is skipped. Nothing
is required to exist, and missing folders cause no errors.

**Pointing at `road_template/un`.** You may point an Additional Data Folder straight at a
`road_template/un` (or `road_template`) folder. Because paths start at the top of the data, the
add-on reads it as the folder that *contains* `road_template`. `E:/Lines/road_template/un`
becomes `E:/Lines`. Anything else in `E:/Lines` (a `def` folder, a `material` folder) is then
used too.

### What each feature needs

| Feature | Files it needs, in any of the folders above |
|---|---|
| Importing and exporting models | nothing extra |
| Looks, variants, variant preview, Variant Grid | nothing extra (read from the model's own PIM/PIT) |
| UN road lines in the viewport, Road Line Country list | `road_template/un/<country>/lines_*` |
| Road Look Preview panel | `def/world/road_look*.sii` |
| Textures of other materials in the viewport | those textures and TOBJs, mostly under `material/` |

What happens when something isn't found:
- **Road looks missing:** the Road Look Preview panel says no `road_look*.sii` was found. Every
  other feature still works.
- **A texture missing:**
  - the material shows untextured in the viewport;
  - import lists it as "Can't find texture nor TOBJ";
  - export keeps the material's game path and warns, so the game still finds its own texture.
- **Line textures missing:** the lines show the game's default (magenta) placeholder, or nothing
  if even that isn't found.

### Example setups

**A. Recommended: your mod plus the extracted game.**
- Project Base Path: `E:/Project` (your mod).
- Additional Data Folder: `E:/ETS2_extracted`, which contains `def`, `material`,
  `road_template`, ... from the game's archives.

Everything works. Your own files in `E:/Project` override the game's, and nothing from the game
is copied into your mod.

**B. A project containing only your own `road_template/un`.**
- Project Base Path: `E:/Project`, containing only `E:/Project/road_template/un/...`.

| Works | Doesn't work |
|---|---|
| Import / export | Road Look Preview (no road looks found) |
| Looks, variants, Variant Grid | Asphalt, shoulder and other non-line textures in the viewport |
| Line preview and line countries | |

To get the Road Look Preview working without the whole game, copy the game's
`def/world/road_look*.sii` files into `E:/Project/def/world/`. For textures, add an extracted
game folder as in setup A.

**C. An Additional Data Folder pointing into the project.**
- Project Base Path: `E:/Project`.
- Additional Data Folder: `E:/Project/road_template/un`.

The folder is read as `E:/Project`, the same as the project path. This is harmless, but it adds
nothing: the project is already searched first, so the second entry never finds anything new.
TOBJs are still written into your project as normal, and line countries and road looks aren't
listed twice. You can remove the entry. Setup B behaves exactly the same with or without it.

### Custom lines next to the game's

Since the first folder that has a file wins, a file in your project always beats a file with the
same path in an Additional Data Folder. With the game's data as an additional folder (setup A),
your project's `road_template/un/...` files override the game's. That's usually what you want.

The reverse doesn't work. If you keep custom lines in an *additional* folder while your project
or an alternative base already has the game's `road_template/un`, files with the same name are
taken from the project and your custom ones are hidden. Keep custom lines in the project, or
give them a country folder name the game doesn't use, so they never collide.

## 2. Looks and variants

A model (PIM) is made of **parts**, which are named groups of geometry. Its trait file (PIT)
adds two independent lists:

- **Looks** change *how* the model looks: material settings and textures, for example a clean
  and a dirty asphalt look. Every look has the same materials, just with different values.
- **Variants** change *which parts* are shown. Every variant lists every part as on or off, for
  example a variant with a dashed centre line and one with a solid line.

Any look can be combined with any variant. The game or the map editor picks one of each.

## 3. Variant preview

In **Object properties > SCS Object > SCS Variants**, with the SCS root selected:

- **Preview Active Variant**: when on, clicking a variant in the list shows only that variant's
  parts in the viewport. Turning it off restores the view you had before turning it on, including
  objects you had hidden yourself.
- **Reset View**: shows every part, turns preview off, and clears any additional parts or overlay
  scheme picked for the preview. It doesn't change the variants themselves.
- **Log** (text icon): writes every variant, its parts and each object's visibility to a text
  block called `SCS_variants_log`. Open it in Blender's Text Editor. It's useful when something
  doesn't show the way you expect.

Under the variant list, SCS Variants has four sub-panels. They are all closed by default; click a
header to open it, or drag the header to reorder them:
- **Variant Grid**: see section 4.
- **Road Look Preview**: see section 5. It is for road templates.
- **Additional Parts**: parts no variant uses. In road templates these are edge lines, rumble
  strips and overlays, which the road look adds. Click one to show it in the preview. It only
  shows when the model has such parts.
- **Classic Part Table**: the original tools' variant-part table. The Variant Grid does the same
  job.

## 4. Variant Grid

A sub-panel of SCS Variants. Think of it as a checklist table:

- **Each row is a variant.** **Each column is a part.**
- **A tick means "this variant shows this part".** Untick it and that variant stops showing it.

Controls:
- **Click a variant's name** to make it the active variant. It is also previewed, if preview is
  on.
- **Tick button next to a name**: turns on every part shown in the grid for that variant. Click
  it again to go back to the parts the variant had before.
- **Column header**: turns that part on in every variant shown. Click again to go back.
- **Duplicate button**: copies a variant with the same parts. Rename the copy in the variant
  list.
- **Restore before 'all' toggles** appears after using the buttons above. It undoes all of those
  changes at once.
- **Filters**: type part or variant names to narrow the table. `*` and `?` work as wildcards, and
  commas separate several patterns, e.g. `brk*, sng*` or `*_hw`. The eye button hides the base
  parts every road variant shares (`vis`, `vis_tran`, `coll`).
- **Columns (0 = fit)**: 0 fits as many part columns as the panel is wide. Use the arrows to page
  through the rest.

Warnings at the bottom point out:
- variants with no parts;
- variants with identical parts;
- parts no variant uses. These are normal for road look additional parts.

## 5. Road Look Preview (UN roads)

A sub-panel of SCS Variants. It reads the game's road looks (`/def/world/road_look*.sii`) from
your base path and Additional Data Folders. It shows road looks whose template has **the same
name as your SCS root**, so name the root after the template model, e.g. `un_1-1_local`. The
globe button (**Show All Road Looks**) lists all of them instead. Use the reload button next to
it after changing a `.sii` file.

For the selected road look it shows:
- **Templates, road offset, shoulder space and compatible edges** for that look.
- **Lane variant**: the editor's lane setup. It sets the AI lanes and limits which line variants
  are allowed. Click an allowed line variant to preview it. **Filter Variant Grid** narrows the
  grid to those variants.
- **Additional parts**: the editor's "Misc" options, such as edge lines, rumble strips and
  collision. Toggle them one by one, or use **All** and **None**. Clicking **All** a second time
  goes back to your previous selection.
- **Overlay schemes** (sparse, light, medium, heavy, city...): the patches and repairs the editor
  scatters over the road. Click one to show all of its parts, and click it again to hide them.
  One scheme is shown at a time.

Road edges (shoulders, curbs, sidewalks) are separate models. They are listed under compatible
edges but not placed in the preview.

## 6. UN road lines

UN road lines use the `eut2.dif.spec.decal.over` shader with the `is_dynamic_road` attribute.
Their textures are a 16-column atlas: a line's position across the texture picks which marking it
is. The lines work under any model or road look name, so your own road models can use them too.

The game's default line textures are **magenta on purpose**. The game replaces them per country.
To preview a country's lines, pick it in **SCS Global Settings > Path Settings > Road Line
Country**. The list only shows folders under `/road_template/un/` that actually contain line
textures. These come from your base path or Additional Data Folders.

## 7. Newer material settings and exporting

Since 1.47, game materials can carry settings the original tools didn't know:
- edge blend / heightmap (`heightmap_*`);
- secondary diffuse;
- terrain flags;
- a few others.

This update keeps them on import. Values from the shader preset are shown with the other
material attributes. Anything the preset doesn't define is listed in the material panel under
**Extra attributes from import**.

**Exporting:** in the export settings, choose **Game Data Format, ver. 5 (AutoMat)** to write
these settings back. The legacy **ver. 5 (Material)** format can't store them. When it's
selected, the export settings show a warning listing the affected materials, and the export
report repeats it for each material.

Textures that aren't found in your project are written with their game path, so a model can keep
using game textures without copying them.

## 8. Importing from game archives

**File > Import > SCS Models from Game Archives (*.scs)** converts a model straight out of the
game's `.scs` archives and imports it. It is based on 50keda's ConverterPIX Wrapper and uses the
included ConverterPIX by mwl4.

1. **Pick archives.** Select one or more `.scs` (or `.zip`) files. A model usually needs
   `base.scs` and `base_share.scs`; materials and textures may come from `def.scs`, `base_map.scs`
   or DLC archives. Archives you always need can be added once with **Add Archives to List** and
   reordered or removed there.
2. **Pick the model.** The next window shows the archives' folders. Browse to the model's `.pmg`
   on the left. For an animated model, browse to its `.pma` files on the right and click each one
   to bring along: a click ticks or unticks it. Only ticked animations are converted.
3. **Import.** Converted files go into your **SCS Project Base Path**, keeping their game folders,
   and the model is imported. **Only convert?** converts without importing. **Textures to Base?**
   puts textures into a sibling `base` folder, so they aren't packed into your mod.

The box at the top of the first window shows which ConverterPIX is used: **bundled** (included
with the add-on) or **downloaded**. The download button fetches the latest one from GitHub. A
failed download never replaces a working copy; the bundled one is used whenever the downloaded one
is missing or broken.
