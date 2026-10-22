# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2013-2014: SCS Software

from ..utils import name as _name_utils
from ..utils.printout import lprint
from ..internals.containers import pix as _pix_container
from ..internals.structure import SectionData as _SectionData


def _get_header(pit_container):
    """Receives PIT container and returns all its Header properties in its own variables.
    For any item that fails to be found, it returns None."""
    format_version = source = f_type = f_name = source_filename = author = None
    for section in pit_container:
        if section.type == "Header":
            for prop in section.props:
                if prop[0] in ("", "#"):
                    pass
                elif prop[0] == "FormatVersion":
                    format_version = prop[1]
                elif prop[0] == "Source":
                    source = prop[1]
                elif prop[0] == "Type":
                    f_type = prop[1]
                elif prop[0] == "Name":
                    f_name = prop[1]
                elif prop[0] == "SourceFilename":
                    source_filename = prop[1]
                elif prop[0] == "Author":
                    author = prop[1]
                else:
                    lprint('\nW Unknown property in "Header" data: "%s"!', prop[0])
    return format_version, source, f_type, f_name, source_filename, author


def _get_global(pit_container):
    """Receives PIT container and returns all its Global properties in its own variables.
    For any item that fails to be found, it returns None."""
    look_count = variant_count = part_count = material_count = None
    for section in pit_container:
        if section.type == "Global":
            for prop in section.props:
                if prop[0] in ("", "#"):
                    pass
                elif prop[0] == "LookCount":
                    look_count = prop[1]
                elif prop[0] == "VariantCount":
                    variant_count = prop[1]
                elif prop[0] == "PartCount":
                    part_count = prop[1]
                elif prop[0] == "MaterialCount":
                    material_count = prop[1]
                else:
                    lprint('\nW Unknown property in "Global" data: "%s"!', prop[0])
    return look_count, variant_count, part_count, material_count


_AUTOMAT_UNIT_RE = None


def _parse_automat_value(raw):
    """Parse a value from AutoMat SII content: string, number, bool or tuple."""
    raw = raw.strip()
    if raw.startswith('"'):
        end = raw.find('"', 1)
        return raw[1:end] if end > 0 else raw[1:]
    if raw.startswith("("):
        inner = raw.strip("()")
        out = []
        for part in inner.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(float(part))
            except ValueError:
                out.append(part)
        return tuple(out)
    if raw in ("true", "false"):
        return raw == "true"
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


def _automat_to_material_section(automat_section):
    """Convert an "AutoMat" look entry (newer material format, written by the AutoMat export)
    into the equivalent legacy "Material" section, so the rest of the importer handles both alike.

    :param automat_section: AutoMat section with Alias, Index and Content (SII text) properties
    :type automat_section: io_scs_tools.internals.structure.SectionData
    :return: Material section, or None if the content can't be read
    :rtype: io_scs_tools.internals.structure.SectionData | None
    """
    import re
    from ..internals.containers.parsers.mat_convert import AttributeConverter

    global _AUTOMAT_UNIT_RE
    if _AUTOMAT_UNIT_RE is None:
        _AUTOMAT_UNIT_RE = re.compile(r'([a-z_0-9]+)\s*:\s*([.\w]+)\s*\{([^{}]*)\}', re.S)

    alias = content = None
    for prop in automat_section.props:
        if prop[0] == "Alias":
            alias = prop[1]
        elif prop[0] == "Content":
            content = prop[1]
    if alias is None or not isinstance(content, str) or "xmat_auto_header" not in content:
        lprint("W AutoMat entry %r has no readable content, skipping it!", (alias,))
        return None

    effect = ""
    inputs = []     # (unit type, name, value)
    samplers = []   # (name, value)
    for unit_type, _unit_name, body in _AUTOMAT_UNIT_RE.findall(content):
        props = {}
        for line in body.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                props[key.strip()] = _parse_automat_value(val)
        if unit_type == "xmat_auto_header":
            effect = str(props.get("effect", ""))
        elif unit_type.startswith("xmat_input_"):
            inputs.append((unit_type[len("xmat_input_"):], props.get("name"), props.get("value")))
        elif unit_type == "xmat_sampler":
            samplers.append((props.get("name"), props.get("value")))

    if effect.endswith(".rfx"):
        effect = effect[:-4]

    # convert newer attribute names back to the legacy ones (additional_ambient -> add_ambient,
    # specular_secondary + shininess_secondary -> aux[3], ...); several inputs can fill one aux
    converter = AttributeConverter()
    attributes = {}   # tag -> (format, value tuple), insertion ordered
    for typ, name, value in inputs:
        if name is None:
            continue
        results = converter.effect_to_material(name, value)
        if not isinstance(results, list):
            results = [results]
        for tag, val in results:
            if typ == "str":
                attributes[tag] = ("STRING", (str(val),))
            elif typ == "int" and tag == name:
                attributes[tag] = ("INT", (int(val),))
            else:
                vals = tuple(float(v) for v in val) if isinstance(val, (tuple, list)) else (float(val),)
                attributes[tag] = ("FLOAT" if len(vals) == 1 else "FLOAT%d" % len(vals), vals)

    material = _SectionData("Material")
    material.props.append(["Alias", alias])
    material.props.append(["Effect", effect])
    material.props.append(["Flags", 0])
    material.props.append(["AttributeCount", len(attributes)])
    material.props.append(["TextureCount", len(samplers)])
    for tag, (fmt, val) in attributes.items():
        attr = _SectionData("Attribute")
        attr.props.append(["Format", fmt])
        attr.props.append(["Tag", tag])
        attr.props.append(["Value", val])
        material.sections.append(attr)
    for idx, (name, value) in enumerate(samplers):
        path = str(value or "")
        if path.endswith(".tobj"):
            path = path[:-5]
        tex = _SectionData("Texture")
        tex.props.append(["Tag", "texture[%d]:%s" % (idx, name)])
        tex.props.append(["Value", path])
        material.sections.append(tex)
    return material


def _get_look(section):
    """Receives a Look section and returns its properties in its own variables.
    For any item that fails to be found, it returns None."""
    look_name = None
    for prop in section.props:
        if prop[0] in ("", "#"):
            pass
        elif prop[0] == "Name":
            look_name = prop[1]
        else:
            lprint('\nW Unknown property in "Look" data: "%s"!', prop[0])
    look_mat_settings = {}

    # newer material format: "AutoMat" entries are converted to legacy "Material" sections
    if any(sec.type == "AutoMat" for sec in section.sections):
        converted = []
        for sec in section.sections:
            if sec.type == "AutoMat":
                sec = _automat_to_material_section(sec)
                if sec is None:
                    continue
            converted.append(sec)
        section.sections = converted

    for sec in section.sections:
        if sec.type == "Material":
            mat_alias = mat_effect = mat_flags = attribute_count = texture_count = None
            attributes = {}
            textures = {}
            for sec_prop in sec.props:
                if sec_prop[0] in ("", "#"):
                    pass
                elif sec_prop[0] == "Alias":
                    mat_alias = sec_prop[1]
                elif sec_prop[0] == "Effect":
                    mat_effect = sec_prop[1]
                elif sec_prop[0] == "Flags":
                    mat_flags = sec_prop[1]
                elif sec_prop[0] == "AttributeCount":
                    attribute_count = sec_prop[1]
                elif sec_prop[0] == "TextureCount":
                    texture_count = sec_prop[1]
                else:
                    lprint('\nW Unknown property in "Look/Material" data: "%s"!', sec_prop[0])
                for sec_section in sec.sections:
                    if sec_section.type == "Attribute":
                        atr_format = atr_tag = atr_value = None
                        for sec_section_prop in sec_section.props:
                            if sec_section_prop[0] in ("", "#"):
                                pass
                            elif sec_section_prop[0] == "Format":
                                atr_format = sec_section_prop[1]
                            elif sec_section_prop[0] == "Tag":
                                atr_tag = sec_section_prop[1]
                            elif sec_section_prop[0] == "Value":
                                atr_value = sec_section_prop[1]
                            else:
                                lprint('\nW Unknown property in "Look/Material/Attribute" data: "%s"!', sec_section_prop[0])
                        attributes[atr_tag] = (atr_format, atr_value)
                    elif sec_section.type == "Texture":
                        txr_tag = txr_value = None
                        for sec_section_prop in sec_section.props:
                            if sec_section_prop[0] in ("", "#"):
                                pass
                            elif sec_section_prop[0] == "Tag":
                                txr_tag = sec_section_prop[1].split(":")[1]
                            elif sec_section_prop[0] == "Value":
                                txr_value = sec_section_prop[1]
                            else:
                                lprint('\nW Unknown property in "Look/Material/Texture" data: "%s"!', sec_section_prop[0])
                        textures[txr_tag] = txr_value
            if len(attributes) != attribute_count:
                lprint("W Attribute count in PIT file doesn't match its declaration!")
            if len(textures) != texture_count:
                lprint("W Texture count in PIT file doesn't match its declaration!")

            # Extra treatment for eut2.truckpaint shader
            #
            # 1. Ignoring flip flake flavor
            # Flavor was never been visually implemented in Blender as it doesn't effect exported mesh data.
            # This means we can "silently" ignore it on import as this flavor
            # should be used only trough paint-job definitions for player vehicles.
            #
            # 2. Ignoring aux attributes & paintjob textures
            # This has to be done in case none of colormask, airbrush and flipflake is enabled
            if mat_effect.startswith("eut2.truckpaint"):

                has_flipflake = mat_effect.find(".flipflake") != -1
                has_airbrush = mat_effect.find(".airbrush") != -1
                has_colormask = mat_effect.find(".colormask") != -1

                # now strip flipflake flavor string, remove flipflake related texture & report it
                if has_flipflake:

                    if mat_effect.find(".flipflakeuv") != -1:
                        mat_effect = mat_effect.replace(".flipflakeuv", "")
                    else:
                        mat_effect = mat_effect.replace(".flipflake", "")
                    if textures.pop("texture_flakenoise", None):
                        sec.remove_section("Texture", "Tag", r"^[\w\[\]]+:texture_flakenoise$")

                    lprint("W Flipflake flavor detected in material %r, ignoring it!", (mat_alias,))

                # remove aux attributes used in flipflake and colormask
                # NOTE: in reality flipflake also defines it, but as we are ignoring flipflake we don't have to test it here
                if not has_colormask or has_airbrush:

                    for attr in ("aux[5]", "aux[6]", "aux[7]"):
                        if attributes.pop(attr, None) is not None:
                            lprint("W Needless truckpaint attribute: %r in current material configuration inside material %r, ignoring it!",
                                   (attr, mat_alias))

                # remove aux[8] attribute & paintjob texture if none of airbrush or colormask mode is enabled
                # NOTE: in reality flipflake also defines it, but as we are ignoring flipflake we don't have to test it here
                if not has_airbrush and not has_colormask:

                    if attributes.pop("aux[8]", None) is not None:
                        lprint("W Needless truckpaint attribute: 'aux[8]' in current material configuration inside material %r, ignoring it!",
                               (mat_alias,))

                    if textures.pop("texture_paintjob", None) is not None:
                        sec.remove_section("Texture", "Tag", r"^[\w\[\]]+:texture_paintjob$")
                        lprint("W Needless truckpaint texture: 'texture_paintjob' in current material configuration inside material %r, ignoring it!",
                               (mat_alias,))

            # Extra treatment for outdated env_factor in eut2.glass & eut2.truckpaint shaders
            # This attribute is outdated and is not used anymore, but it is still present in many materials.
            if mat_effect.startswith("eut2.glass") or mat_effect.startswith("eut2.truckpaint"):
                # remove env_factor attribute
                if attributes.pop("env_factor", None) is not None:
                        lprint("W Needless attribute: 'env_factor' in current material configuration inside material %r, ignoring it!",
                               (mat_alias,))

            # Extra treatment for building shaders
            #
            # If night version of it is detected, switch it to day one.
            if mat_effect.startswith("eut2.building") and mat_effect.endswith(".night"):

                mat_effect = mat_effect.replace(".night", ".day")
                lprint("W Night version of building shader detected in material %r, switching it to day!", (mat_alias,))

            # Extra treatment for deprecated/removed/unsupported shaders/flavors/attributes
            #
            # If day/night version of "window" shader is detected, switch it to "lit".
            if mat_effect.startswith("eut2.window") and mat_effect.endswith((".day", ".night")):

                mat_effect = mat_effect.replace(".day", ".lit").replace(".night", ".lit")
                lprint("W Outdated Day/Night version of window shader detected in material %r, switching it to lit!", (mat_alias,))

            # If tsnmap16/tsnmapuv16 flavor is detected, switch it to "tsnmap/tsnmapuv
            if any(x in mat_effect for x in (".tsnmap16", ".tsnmapuv16")):
                
                mat_effect = mat_effect.replace(".tsnmap16", ".tsnmap").replace(".tsnmapuv16", ".tsnmapuv")
                lprint('W Outdated tsnmap16/tsnmapuv16 flavor detected in material %r, switching it to tsnmap/tsnmapuv!', (mat_alias,))

            # If day/night version of "eut2.billboard" shader is detected, remove "day/night" and in "night" case, switch to "eut2.billboard.lit"
            if mat_effect.startswith("eut2.billboard") and mat_effect.endswith((".day", ".night")):
                
                if mat_effect.endswith(".night"):
                    mat_effect = mat_effect.replace("billboard", "billboard.lit")
                    lprint("W Night version of billboard shader detected in material %r, switching it to lit!", (mat_alias,))
                else:
                    mat_effect = mat_effect.replace(".day", "")
                    lprint("W Day version of billboard shader detected in material %r, removing it from effect!", (mat_alias,))


            # Extra treatment for removed attributes not supported anymore
            #
            # If "diffuse" attribute in "eut2.decalshadow" shader is detected, remove it
            if mat_effect.startswith("eut2.decalshadow"):
                if attributes.pop("diffuse", None) is not None:
                    lprint("I Deprecated attribute: 'diffuse' in current material configuration inside material %r, ignoring it!",
                           (mat_alias,))

            # If "shininess" attribute in "eut2.light.tex" or "eut2.lightmap" shaders is detected, remove it
            if mat_effect.startswith("eut2.light.tex") or mat_effect.startswith("eut2.lightmap"):
                if attributes.pop("shininess", None) is not None:
                    lprint("I Deprecated attribute: 'shininess' in current material configuration inside material %r, ignoring it!",
                           (mat_alias,))


            # NOTE: newer-format attributes (diffuse_secondary, is_terrain_material, heightmap_*, ...) are kept:
            # attributes unknown to the shader preset are stored aside on the material and written back on export.

            # NOTE: "is_dynamic_road" is now supported (universal road template line/overlay decals,
            # preset "dif.spec" with DEPTH flavor), so it's kept. ConverterPIX writes it as FLOAT; store it as INT.
            if "is_dynamic_road" in attributes:
                dyn_format, dyn_value = attributes["is_dynamic_road"]
                try:
                    dyn_int = int(round(float(dyn_value[0] if isinstance(dyn_value, (list, tuple)) else dyn_value)))
                except (TypeError, ValueError):
                    dyn_int = 0
                attributes["is_dynamic_road"] = ("INT", [dyn_int])

            look_mat_settings[mat_alias] = (mat_effect, mat_flags, attributes, textures, sec)

    return look_name, look_mat_settings


def _get_variant(section):
    """Receives a Variant section and returns its properties in its own variables.
    For any item that fails to be found, it returns None."""
    variant_name = None
    variantparts = []
    for prop in section.props:
        if prop[0] in ("", "#"):
            pass
        elif prop[0] == "Name":
            variant_name = prop[1]
        else:
            lprint('\nW Unknown property in "Variant" data: "%s"!', prop[0])

    for sec in section.sections:
        if sec.type == "Part":
            part_name = None
            for sec_prop in sec.props:
                if sec_prop[0] in ("", "#"):
                    pass
                elif sec_prop[0] == "Name":
                    part_name = sec_prop[1]
                elif sec_prop[0] == "AttributeCount":
                    '''
                    NOTE: skipped for now as no data needs to be readed
                    attribute_count = sec_prop[1]
                    '''
                    pass
                else:
                    lprint('\nW Unknown property in "Variant/Part" data: "%s"!', sec_prop[0])

            var_part_format = var_part_tag = var_part_value = None
            for sec_section in sec.sections:
                if sec_section.type == "Attribute":
                    for sec_section_prop in sec_section.props:
                        if sec_section_prop[0] in ("", "#"):
                            pass
                        elif sec_section_prop[0] == "Format":
                            var_part_format = sec_section_prop[1]
                        elif sec_section_prop[0] == "Tag":
                            var_part_tag = sec_section_prop[1]
                        elif sec_section_prop[0] == "Value":
                            var_part_value = sec_section_prop[1]
                        else:
                            lprint('\nW Unknown property in "Variant/Part/Attribute" data: "%s"!', sec_section_prop[0])

                if var_part_format == "INT" and var_part_tag == "visible":
                    if var_part_value[0] == 1:
                        variantparts.append(_name_utils.tokenize_name(part_name))
                else:
                    lprint('D ---var_part_value: %s', (str(var_part_value),))
    return variant_name, variantparts


def load(filepath):
    """Enty point for importing PIT file

    :param filepath: filepath of PIT file
    :type filepath: str
    """
    print("\n************************************")
    print("**      SCS PIT Importer          **")
    print("**      (c)2014 SCS Software      **")
    print("************************************\n")

    ind = '    '
    pit_container = _pix_container.get_data_from_file(filepath, ind)

    # TEST PRINTOUTS
    # ind = '  '
    # for section in pit_container:
    # print('SEC.: "%s"' % section.type)
    # for prop in section.props:
    # print('%sProp: %s' % (ind, prop))
    # for data in section.data:
    # print('%sdata: %s' % (ind, data))
    # for sec in section.sections:
    # print_section(sec, ind)
    # print('\nTEST - Source: "%s"' % pit_container[0].props[1][1])
    # print('')

    # TEST EXPORT
    # path, file = os.path.splitext(filepath)
    # export_filepath = str(path + '_reex' + file)
    # result = pix_write.write_data(pit_container, export_filepath, ind, dump_level)
    # if result == {'FINISHED'}:
    # Print(dump_level, '\nI Test export succesful! The new file:\n  "%s"', export_filepath)
    # else:
    # Print(dump_level, '\nE Test export failed! File:\n  "%s"', export_filepath)

    # LOAD HEADER
    '''
    NOTE: skipped for now as no data needs to be readed
    (format_version, source, f_type, f_name, source_filename, author) = _get_header(pit_container, dump_level)
    '''

    # LOAD GLOBALS
    '''
    NOTE: skipped for now as no data needs to be readed
    (look_count, variant_count, part_count, material_count) = _get_global(pit_container, dump_level)
    '''

    # LOAD LOOKS AND VARIANTS
    loaded_looks = []
    loaded_variants = []
    for section in pit_container:
        if section.type == 'Look':
            look_name, look_mat_settings = _get_look(section)
            look_record = (look_name, look_mat_settings)
            loaded_looks.append(look_record)
        elif section.type == 'Variant':
            variant_name, variantparts = _get_variant(section)
            variant_record = (variant_name, variantparts)
            # variant_record = (getVariant(section))
            loaded_variants.append(variant_record)
            # loaded_variants.append((getVariant(section)))

    print("************************************")
    return {'FINISHED'}, loaded_variants, loaded_looks
