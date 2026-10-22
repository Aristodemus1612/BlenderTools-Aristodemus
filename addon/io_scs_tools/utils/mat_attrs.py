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

"""Helpers for material attributes that have no dedicated Blender property.

Newer game materials (1.47+ format) use attributes the original tools never knew:
heightmap_*, diffuse_secondary, is_terrain_material and others. They are kept so
that nothing is lost between import and export:

* attributes defined by the shader preset but without a dedicated RNA property
  (e.g. heightmap_*) are stored as ID properties "shader_attribute_<tag>";
* attributes the preset doesn't define at all are stored on the material in
  material["scs_extra_attributes"] = {tag: {"Format": str, "Value": [..]}} and
  written back on export.

The legacy material output ("5") can't carry attributes from the newer format, so
those are skipped there with a warning; the AutoMat output ("5_AM") writes them.
"""

EXTRA_ATTRIBUTES_KEY = "scs_extra_attributes"

# attributes only representable in the newer (AutoMat) material format
NEW_FORMAT_ONLY_PREFIXES = ("heightmap_", "diffuse_secondary", "specular_secondary", "shininess_secondary",
                            "reflection_secondary", "is_terrain_material", "far_color", "far_specular_power")


def is_new_format_only(tag):
    """Tells if given attribute tag exists only in the newer (AutoMat) material format."""
    return tag.startswith(NEW_FORMAT_ONLY_PREFIXES)


def _plain(value):
    """Convert ID property values (IDPropertyArray etc.) to plain python values."""
    if hasattr(value, "to_list"):
        return value.to_list()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def get_attribute_value(material, tag, default=None):
    """Get value of shader attribute stored on material, from RNA property or ID property.

    :param material: blender material
    :type material: bpy.types.Material
    :param tag: attribute tag without "shader_attribute_" prefix and without brackets (e.g. "heightmap_feather_size")
    :type tag: str
    :param default: value returned if attribute isn't stored
    :return: attribute value
    """
    key = "shader_attribute_" + tag
    value = getattr(material.scs_props, key, None)
    if value is None:
        value = material.scs_props.get(key, None)
    if value is None:
        return default
    return _plain(value)


def store_attribute_value(material, tag, attribute_format, values):
    """Store attribute without dedicated RNA property as ID property on material SCS props.

    :param material: blender material
    :type material: bpy.types.Material
    :param tag: attribute tag
    :type tag: str
    :param attribute_format: SCS format string (FLOAT, FLOAT2, INT, ...)
    :type attribute_format: str
    :param values: list of values
    :type values: list | tuple
    """
    values = list(values) if isinstance(values, (list, tuple)) else [values]
    if attribute_format.startswith("INT"):
        conv = []
        for v in values:
            try:
                conv.append(int(round(float(v))))
            except (TypeError, ValueError):
                conv.append(0)
        values = conv
    elif attribute_format.startswith("FLOAT"):
        values = [float(v) for v in values]

    if attribute_format in ("FLOAT", "INT") and len(values) == 1:
        material.scs_props["shader_attribute_" + tag] = values[0]
    else:
        material.scs_props["shader_attribute_" + tag] = values


def set_extra_attributes(material, extras):
    """Store attributes unknown to the material's shader preset.

    :param material: blender material
    :type material: bpy.types.Material
    :param extras: dictionary {tag: (format, [values])}
    :type extras: dict
    """
    data = {}
    for tag, (attr_format, values) in extras.items():
        values = list(values) if isinstance(values, (list, tuple)) else [values]
        data[tag] = {"Format": str(attr_format), "Value": [v if isinstance(v, str) else float(v) for v in values]}
    if data:
        material[EXTRA_ATTRIBUTES_KEY] = data
    elif EXTRA_ATTRIBUTES_KEY in material:
        del material[EXTRA_ATTRIBUTES_KEY]


def get_extra_attributes(material):
    """Get attributes unknown to the material's shader preset.

    :param material: blender material
    :type material: bpy.types.Material
    :return: list of tuples (format, tag, values)
    :rtype: list[tuple[str, str, list]]
    """
    if EXTRA_ATTRIBUTES_KEY not in material:
        return []
    result = []
    data = _plain(material[EXTRA_ATTRIBUTES_KEY])
    for tag in sorted(data.keys()):
        entry = _plain(data[tag])
        attr_format = str(entry.get("Format", "FLOAT"))
        values = list(_plain(entry.get("Value", [])))
        if attr_format.startswith("INT"):
            values = [int(round(float(v))) for v in values]
        result.append((attr_format, tag, values))
    return result


def get_new_format_only_tags(material):
    """Tags of attributes on given material that only the newer (AutoMat) material format can carry.

    :param material: blender material
    :type material: bpy.types.Material
    :rtype: list[str]
    """
    tags = []
    scs_props = getattr(material, "scs_props", None)
    if scs_props is not None:
        for key in scs_props.keys():
            if key.startswith("shader_attribute_") and is_new_format_only(key[len("shader_attribute_"):]):
                tags.append(key[len("shader_attribute_"):])
    for _, tag, _ in get_extra_attributes(material):
        if is_new_format_only(tag) and tag not in tags:
            tags.append(tag)
    return tags


def get_materials_needing_automat(materials):
    """Names of materials whose settings would be partly lost in the legacy material output."""
    return [m.name for m in materials if m and get_new_format_only_tags(m)]
