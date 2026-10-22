# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2026: Aristodemus

"""Reader for road look definitions (/def/world/road_look*.sii).

Road looks tie a template model to the editor's options: lane variants and the line variants
they allow (road_template_variant units, model_variants[]), compatible edges, additional parts
(add_parts_*[]) and overlay schemes. The data is read from the SCS Project Base Path, its
alternative bases and the Additional Data Folders.
"""

import os
import re
import time
from . import path as _path_utils

_CACHE = {"stamp": None, "data": None, "time": 0.0}

_UNIT_RE = re.compile(r'^\s*([a-z_0-9]+)\s*:\s*([.\w]+)\s*$')
_PROP_RE = re.compile(r'^\s*([a-z_0-9]+)(\[\d*\])?\s*:\s*(.*?)\s*$')


class RoadTemplateVariant:
    def __init__(self, name):
        self.name = name
        self.lane_variant = ""
        self.model_variants = []
        self.lanes_left = []
        self.lanes_right = []


class RoadLook:
    def __init__(self, name):
        self.name = name                 # unit name, e.g. road.un11
        self.ui_name = ""                # "un 1-1"
        self.template_right = ""
        self.template_left = ""
        self.road_offset = None
        self.lane_variant_default = ""
        self.lane_variants = []          # names of road_template_variant units
        self.compatible_edges_right = []
        self.compatible_edges_left = []
        self.add_parts_right = []
        self.add_parts_left = []
        self.overlay_schemes = []        # raw strings
        self.shoulder_space_left = None
        self.shoulder_space_right = None
        self.source = ""

    @property
    def add_parts(self):
        seen = []
        for p in self.add_parts_right + self.add_parts_left:
            if p not in seen:
                seen.append(p)
        return seen

    def template_names(self):
        names = []
        for t in (self.template_right, self.template_left):
            if t:
                names.append(os.path.splitext(os.path.basename(t))[0])
        return names

    def parsed_overlay_schemes(self):
        """Return list of (scheme name, probability, [(part, weight), ...])."""
        result = []
        for raw in self.overlay_schemes:
            fields = [f.strip() for f in raw.split(":")]
            if len(fields) < 2:
                continue
            name = fields[0]
            try:
                prob = float(fields[1])
            except ValueError:
                prob = 1.0
            parts = []
            for f in fields[2:]:
                if "|" in f:
                    part, weight = f.split("|", 1)
                    try:
                        parts.append((part.strip(), float(weight)))
                    except ValueError:
                        parts.append((part.strip(), 1.0))
                elif f:
                    parts.append((f, 1.0))
            result.append((name, prob, parts))
        return result


def _strip_value(value):
    value = value.split("#", 1)[0].strip() if not value.startswith('"') else value
    if value.startswith('"'):
        end = value.find('"', 1)
        return value[1:end] if end > 0 else value[1:]
    return value


def parse_sii_text(text, looks, variants, source=""):
    """Parse road_look and road_template_variant units out of SII text into given dicts."""
    current = None
    depth = 0
    base = 0          # depth of the SiiNunit wrapper block (units live directly inside it)
    pending_unit = None
    expect_wrapper_brace = False
    for raw_line in text.splitlines():
        line = raw_line.split("//", 1)[0] if "//" in raw_line and '"' not in raw_line else raw_line
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("SiiNunit"):
            expect_wrapper_brace = True
            stripped = stripped[len("SiiNunit"):].strip()
            if not stripped:
                continue
        if expect_wrapper_brace and stripped.startswith("{"):
            expect_wrapper_brace = False
            depth += 1
            base = depth
            stripped = stripped[1:].strip()
            if not stripped:
                continue

        if depth == base:
            m = _UNIT_RE.match(stripped.rstrip("{").strip())
            if m:
                cls, name = m.group(1), m.group(2)
                if cls == "road_look":
                    pending_unit = RoadLook(name)
                    pending_unit.source = source
                elif cls == "road_template_variant":
                    pending_unit = RoadTemplateVariant(name)
                else:
                    pending_unit = None
            if stripped == "}":
                depth -= 1
                continue
            if "{" in stripped:
                depth += 1
                current = pending_unit
                if isinstance(current, RoadLook):
                    looks[current.name] = current
                elif isinstance(current, RoadTemplateVariant):
                    variants[current.name] = current
            continue

        if "{" in stripped:
            depth += 1
        if "}" in stripped:
            depth -= 1
            if depth == base:
                current = None
            continue
        if current is None or depth != base + 1:
            continue

        m = _PROP_RE.match(stripped)
        if not m:
            continue
        key, is_array, value = m.group(1), m.group(2), _strip_value(m.group(3))

        if isinstance(current, RoadLook):
            if key == "name":
                current.ui_name = value
            elif key in ("template_right", "template_left", "lane_variant_default"):
                setattr(current, key, value)
            elif key in ("road_offset", "shoulder_space_left", "shoulder_space_right"):
                try:
                    setattr(current, key, float(value))
                except ValueError:
                    pass
            elif key in ("lane_variants", "compatible_edges_right", "compatible_edges_left",
                         "add_parts_right", "add_parts_left", "overlay_schemes") and is_array is not None:
                getattr(current, key).append(value)
        else:
            if key == "lane_variant":
                current.lane_variant = value
            elif key == "model_variants" and is_array is not None:
                current.model_variants.append(value)
            elif key == "lanes_left" and is_array is not None:
                current.lanes_left.append(value)
            elif key == "lanes_right" and is_array is not None:
                current.lanes_right.append(value)


def _find_road_look_files():
    files = []
    seen = set()
    for def_dir in _path_utils.get_abs_paths("//def/world", is_dir=True):
        try:
            names = sorted(os.listdir(def_dir))
        except OSError:
            continue
        for name in names:
            if name.startswith("road_look") and name.endswith(".sii"):
                full = os.path.join(def_dir, name)
                key = os.path.normcase(os.path.realpath(full))
                if key not in seen:
                    seen.add(key)
                    files.append(full)
    return files


def load_road_looks(force=False):
    """Load and cache all road looks and template variants found in data folders.

    :return: (dict name -> RoadLook, dict name -> RoadTemplateVariant)
    :rtype: (dict, dict)
    """
    now = time.time()
    if not force and _CACHE["data"] is not None and now - _CACHE["time"] < 5.0:
        return _CACHE["data"]

    files = _find_road_look_files()
    stamp = tuple((f, os.path.getmtime(f)) for f in files if os.path.isfile(f))
    if not force and stamp == _CACHE["stamp"] and _CACHE["data"] is not None:
        _CACHE["time"] = now
        return _CACHE["data"]

    looks, variants = {}, {}
    for f in files:
        try:
            with open(f, encoding="utf8", errors="replace") as fh:
                parse_sii_text(fh.read(), looks, variants, source=f)
        except OSError:
            continue

    _CACHE.update(stamp=stamp, data=(looks, variants), time=now)
    return looks, variants


def looks_for_template(template_name, show_all=False):
    """Road looks using given template model name (file name without extension), sorted by UI name."""
    looks, _ = load_road_looks()
    result = [lk for lk in looks.values() if show_all or template_name in lk.template_names()]
    return sorted(result, key=lambda lk: (lk.ui_name or lk.name).lower())
