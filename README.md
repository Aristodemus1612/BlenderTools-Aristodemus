# SCS Tools (Aristodemus)

![Version](https://img.shields.io/badge/version-2.5.1-blue)
![Status](https://img.shields.io/badge/status-test%20release-orange)
![Blender](https://img.shields.io/badge/Blender-5.0%2B-e87d0d)
![Game](https://img.shields.io/badge/ETS2%20%2F%20ATS-1.61-2b6cb0)
![Licence](https://img.shields.io/badge/licence-GPL--3.0-green)

An unofficial update of **SCS Blender Tools**, the Blender add-on for creating models for
Euro Truck Simulator 2 and American Truck Simulator. It is built on Michaleczeq's fork of the
original tools by SCS Software. It adds Universal (UN) road support, a new way to manage
variants, and support for current game materials.

> [!IMPORTANT]
> **This is a test release.** Expect bugs, and please report them (see [Reporting
> problems](#reporting-problems)). Support is limited: this is a spare-time project.
>
> **Not made, endorsed or supported by SCS Software.** Please don't contact SCS about this
> version. Use the official tools if you need the official release.

> **AI Disclaimer** Claude by Anthropic has been used as a coding tool for this update. It is used as a support tool only, I do not support AI as a creative replacment.

## Contents

- [Requirements](#requirements)
- [Features](#features)
- [Installation](#installation)
- [Setting up your folders](#setting-up-your-folders)
- [Getting game models into Blender](#getting-game-models-into-blender)
- [Exporting](#exporting)
- [What to test](#what-to-test)
- [Known issues and limitations](#known-issues-and-limitations)
- [Roadmap](#roadmap)
- [Reporting problems](#reporting-problems)
- [Credits](#credits)
- [Licence](#licence)

Full instructions for every new feature are in the **[User Guide](docs/guide.md)**. Every
change is listed in the **[Changelog](CHANGELOG.md)**.

## Requirements

| | |
|---|---|
| **Blender** | 5.0 or newer. Tested on **Blender 5.2.0**. Blender 4.x and older are not supported. |
| **Game** | Euro Truck Simulator 2 / American Truck Simulator **1.61** |
| **Model conversion** | [ConverterPIX](https://github.com/mwl4/ConverterPIX) is included for bringing game models into Blender. SCS's own conversion tool is needed for your exports. |

## Features

### Universal (UN) roads
- **Road Look Preview.** Reads the game's road looks (`/def/world/road_look*.sii`) and shows,
  for the model you have open:
  - which road looks use it;
  - the lane variants and the line variants each one allows;
  - the additional parts (edge lines, rumble strips, collision);
  - the overlay schemes (sparse, light, medium...), exactly as the map editor offers them.
- **Road line preview.** UN road lines display correctly in the viewport. You can choose which
  country's line textures to preview.

### Variants
- **Variant Grid.** A table of every part against every variant, with:
  - filters and column paging;
  - one-click toggles;
  - warnings about empty or duplicate variants.
- **Variant preview.** Click a variant to see only its parts. Switching preview off restores your
  previous view, and **Reset View** shows everything.
- **Tidier panel.** SCS Variants is organised into collapsible sub-panels.

### Materials
- **Current game materials are kept intact.** Edge blend / heightmap, secondary diffuse and
  terrain settings (used since game version 1.47) are preserved on import. The AutoMat export
  writes them back.
- **Export warning.** The export settings warn when the legacy material format would drop any of
  these settings.
- **Binary TOBJ support.** Texture files straight from the game archives can be read.
- **Game texture paths kept.** Textures that aren't in your project keep their game path on
  export.

### Importing from game archives
- **Import straight from `.scs` archives.** **File > Import > SCS Models from Game Archives (*.scs)**
  browses the game's archives, converts the model you pick (with its animations, if you want them)
  and imports it. ConverterPIX is included, so nothing else needs installing. Based on
  50keda's ConverterPIX Wrapper.

### Data folders
- **Additional Data Folders.** Use extracted game archives or other mods as read-only sources of
  textures and definitions, without copying them into your project.

### Fixes
- Crashes in Blender 5 (creating looks, closing the preferences window, road edge models).
- Panels staying greyed out after paths load.
- The file browser losing its buttons on the first import.
- An AutoMat export crash on materials with texture generation.
- Python 3.12+ warnings.

## Installation

### 1. Remove any previous SCS Tools

This version uses the same internal add-on name as the official SCS Tools. Files left over from an
older install can mix with the new ones, so remove any existing copy first. That means the official
release, Michaleczeq's fork or an earlier test build.

> [!WARNING]
> **Note down your paths before uninstalling.** The tools store their settings (Project Base
> Path, shader presets and so on) in a `config.txt` inside the add-on folder. Uninstalling deletes
> them, and you will need to set them again.

1. In Blender, open **Edit > Preferences > Add-ons** and search for **SCS Tools**.
2. Expand the SCS Tools entry and click **Uninstall** (**Remove** in older Blender versions).
3. **Close and restart Blender.** An enabled add-on stays loaded until Blender restarts.
4. *If SCS Tools still appears, or was installed by copying files:* delete the `io_scs_tools`
   folder from Blender's add-ons folder. On Windows this is
   `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\`.

### 2. Install this version

1. Download `scs_tools_aristodemus_2.5.1.zip` from the
   [Releases](../../releases) page. Don't unpack it.
2. In **Edit > Preferences > Add-ons**, open the drop-down menu at the top right and choose
   **Install from Disk**. Select the zip.
3. Enable **SCS Tools (Aristodemus)**.
4. **Restart Blender** so the add-on starts cleanly.
5. Open the 3D view sidebar (**N**) and go to **Tool > SCS Global Settings > Path Settings**. Set
   your **SCS Project Base Path**, and optionally your **Additional Data Folders**. Read
   [Setting up your folders](#setting-up-your-folders) first: the folders you choose decide which
   features work.

### Installing from source

The add-on's source is in `addon/io_scs_tools`. To build your own installable zip, zip the
`io_scs_tools` folder itself (so the zip contains `io_scs_tools/...`), then install it as above.

### Going back to the official tools

Uninstall this version, restart Blender and install the official release. Blend files saved with
this version still open with the official tools. However, the official tools don't know the newer
material settings, and materials using the edge-blend / heightmap flavour may show their shader
preset as missing.

## Setting up your folders

### How the add-on finds files

Every path inside a game model or definition starts at the **top of the game data**, not at the
model itself. For example:
- a road line material asks for `/road_template/un/default/lines_local_difopa.tobj`;
- an asphalt material asks for `/material/road/...`;
- road looks live in `/def/world/road_look*.sii`.

The add-on looks for each file in the following order. **The first folder that contains the file
wins.**

1. Your **SCS Project Base Path**.
2. Folders named `base`, `base_share` or `base_vehicle` next to it or one level above it. These
   are the original tools' *alternative bases*, switched on and off with the magnet button next
   to the path.
3. Your **Additional Data Folders**, in the order listed.

Additional Data Folders are **read only**. The add-on never writes TOBJ files or anything else
into them.

If you point an Additional Data Folder at a `road_template/un` or `road_template` folder, the
add-on uses the folder that *contains* `road_template`, because game paths start from there. For
example, `E:/Lines/road_template/un` is read as `E:/Lines`.

### What each feature needs

| Feature | Files it needs, in any of the folders above |
|---|---|
| Import, export, looks, variants, Variant Grid | Nothing extra. Everything comes from the model's own files. |
| UN road line preview and the line country list | `road_template/un/...` |
| Road Look Preview | `def/world/road_look*.sii` |
| Textures in the viewport (asphalt, shoulders, props...) | The textures and TOBJs they use, mostly under `material/` |

Nothing else is required. Folders that don't exist are simply skipped.

### Common setups

**Recommended: your mod as the project, the extracted game as an additional folder.**
Extract the game's `base` and `def` archives (and any DLC you use) into one folder. Add the folder
that contains `def` and `material` as an Additional Data Folder. Every feature works, and nothing
from the game is copied into your mod.

**A project containing only your own `road_template/un`.** For example, the project is
`E:/Project` and contains only `E:/Project/road_template/un`.

| Works | Doesn't work |
|---|---|
| Import and export | Road Look Preview: it reports that no road looks were found |
| Looks, variants, Variant Grid | Asphalt, shoulder and other non-line textures in the viewport |
| Line preview and line countries | |

To get the Road Look Preview working, copy the game's `road_look*.sii` files into
`E:/Project/def/world/`. The other textures are listed on import as "Can't find texture nor TOBJ".
Export still writes their game paths (with a warning), so the game finds them.

**An Additional Data Folder pointing into the project.** For example,
`E:/Project/road_template/un` when the project is `E:/Project`. This is harmless but has no
effect. It resolves to the project folder, which is already searched first. TOBJs are still
written into your project as normal.

> [!NOTE]
> **Custom road lines.** The project is always searched before Additional Data Folders, so a file
> in your project hides a file with the same path in an additional folder. Keep custom line
> textures in your project, or give them a country folder name the game doesn't use.

See the [User Guide](docs/guide.md#1-setting-up-paths) for more examples.

## Getting game models into Blender

Use **File > Import > SCS Models from Game Archives (*.scs)**:
1. Set your **SCS Project Base Path** first. Converted files are written there.
2. Pick one or more archives, for example `base.scs`, `base_share.scs`, `def.scs` and the DLC
   archives the model needs. Add archives you always use with **Add Archives to List**.
3. In the next window, browse to the model (`.pmg`) on the left. For an animated model, browse to
   its animations (`.pma`) on the right and click each one to tick it.
4. Click **OK**. The model is converted into your project and imported. Tick **Only convert?** to
   convert without importing.

The included [ConverterPIX](https://github.com/mwl4/ConverterPIX) by mwl4 does the conversion. The
download button in the import window gets its latest version from GitHub; if that fails, the
included one keeps being used. If you prefer, you can still convert with ConverterPIX yourself and
import the `.pim` through **File > Import > SCS Game Object (.pim)**.

If you have 50keda's separate **ConverterPIX Wrapper** add-on installed, you can remove it: it
does the same job.

## Exporting

The export setting **Output Format** offers two material formats:

| Format | Use it for |
|---|---|
| **Game Data Format, ver. 5 (AutoMat)**, the default | **Anything based on current game materials.** Writes every setting, including edge blend / heightmap, secondary diffuse and terrain. |
| **Game Data Format, ver. 5 (Material)** | Older models only. This legacy format can't store the newer settings. It leaves them out and warns in the export settings and in the export report. |

Exported models are converted with SCS's own conversion tool, as with the official tools.

## What to test

This is a test release. Please try the following and report anything that's wrong:

- **Exports, fully checked for bugs.** Export models in both material formats, convert them with
  SCS's conversion tool, and load them in the game and in the map editor. Check:
  - geometry, parts and variants;
  - materials and textures;
  - looks;
  - collision and locators.
- **Round trips.** Import a game model, export it unchanged and compare it with the original.
- **Current game materials.** Edge blend / heightmap, secondary diffuse and terrain materials,
  exported with AutoMat.
- **UN roads.** Line variants, additional parts and overlay schemes in the Road Look Preview,
  compared with what the map editor offers for the same road.
- **Variants.** Preview, Reset View and the Variant Grid on your own models.
- **Folders.** The setups above with your own folder layout.
- **Blender versions.** Blender 5.x versions other than 5.2.0.

## Known issues and limitations

- Tested with ETS2 1.61 game data.
- The legacy material format can't store newer material settings. Use AutoMat (see
  [Exporting](#exporting)).
- Editing an edge-blend / heightmap setting changes it in the active look only. Change it in each
  look if your model has several.
- Texture sampler settings from TOBJ files (anisotropic filtering and similar) aren't exported
  back yet.
- Car and truck interior and paint shaders added to the game in recent years aren't supported
  yet.

## Roadmap

Planned for future updates, without dates:
- UN road line tools;
- road template and road look generators;
- junction and roundabout prefab helpers.

## Reporting problems

Open an issue in the [Issues](../../issues) tab and include:
- the model, or a small file that shows the problem;
- the steps you took;
- the Blender version;
- the output of Blender's system console (**Window > Toggle System Console** on Windows).

## Credits

| | |
|---|---|
| **Simon Lusenc (50keda)** and **Milos Zajic (4museman)**, SCS Software | The original SCS Blender Tools |
| **Michal (Michaleczeq)** | The unofficial fork this update is built on |
| **Simon Lusenc (50keda)** | ConverterPIX Wrapper, the base of the game archive importer |
| **mwl4** | ConverterPIX, included for bringing game models into Blender |
| **Aristodemus** | This update |

## Licence

Released under the **GNU General Public License, version 3**. See [LICENSE](LICENSE).

The original SCS Blender Tools files are licensed GPL-2.0 *or later*. Since 2.5.1 the add-on includes
code from 50keda's [ConverterPIX Wrapper](https://github.com/simon50keda/ConverterPIXWrapper)
(GPL-3.0), so the add-on as a whole is distributed under GPL-3.0.

The included ConverterPIX executables (`io_scs_tools/bin/`) are by mwl4, licensed under the
GNU Lesser General Public License, version 3. Their source code is at
https://github.com/mwl4/ConverterPIX; see `io_scs_tools/bin/README.md`.

Euro Truck Simulator 2, American Truck Simulator and their game data are the property of SCS
Software. No game data is included in this repository.
