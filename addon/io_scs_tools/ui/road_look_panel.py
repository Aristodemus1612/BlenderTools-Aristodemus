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

"""Road look panel: preview a road template the way the map editor combines it.

Pick one of the road looks that use this template, then a lane variant (which limits the
allowed line variants), switch road look additional parts (edge lines, rumble strips) on/off
and preview overlay schemes. Data comes from /def/world/road_look*.sii in the data folders.
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty, PointerProperty
from ..utils import object as _object_utils
from ..utils import road_look as _road_look

_ENUM_CACHE = {"looks": [], "variants": []}
NONE = "__none__"  # empty identifiers act as separators in dynamic enums, so use a real one


def _root(context):
    obj = context.active_object
    return _object_utils.get_scs_root(obj) if obj else None


def _model_parts(root):
    return {p.name for p in root.scs_object_part_inventory}


def _extra_parts(root):
    return [p for p in root.scs_props.scs_root_preview_extra_parts.split(";") if p]


def _set_extra_parts(root, parts):
    unique = []
    for p in parts:
        if p and p not in unique:
            unique.append(p)
    root.scs_props.scs_root_preview_extra_parts = ";".join(unique)


def get_selected_look(context):
    settings = context.window_manager.scs_road_look
    root = _root(context)
    if not root or settings.road_look in ("", NONE):
        return None
    looks, _ = _road_look.load_road_looks()
    return looks.get(settings.road_look)


def get_selected_template_variant(context):
    look = get_selected_look(context)
    settings = context.window_manager.scs_road_look
    if not look or settings.lane_variant in ("", NONE):
        return None
    _, variants = _road_look.load_road_looks()
    return variants.get(settings.lane_variant)


def _look_items(self, context):
    items = [(NONE, "(choose road look)", "No road look selected", 0)]
    root = _root(context)
    if root:
        looks = _road_look.looks_for_template(root.name, show_all=self.show_all)
        for i, look in enumerate(looks, start=1):
            label = "%s  (%s)" % (look.ui_name or look.name, look.name)
            items.append((look.name, label, "Templates: %s" % ", ".join(look.template_names()), i))
    _ENUM_CACHE["looks"] = items
    return items


def _variant_items(self, context):
    items = [(NONE, "(all variants)", "No lane variant: any line variant can be used", 0)]
    look = get_selected_look(context)
    if look:
        _, variants = _road_look.load_road_looks()
        for i, name in enumerate(look.lane_variants, start=1):
            tv = variants.get(name)
            short = name.split(".")[-2:] if name.count(".") >= 2 else [name]
            label = "%s: %s" % (tv.lane_variant if tv else "?", ".".join(short))
            items.append((name, label, name, i))
    _ENUM_CACHE["variants"] = items
    return items


def _on_look_change(self, context):
    self.lane_variant = NONE


class SCS_TOOLS_RoadLookSettings(bpy.types.PropertyGroup):
    show_all: BoolProperty(
        name="Show All Road Looks",
        description="List every road look found, not only the ones using a template named like this SCS root",
        default=False,
    )
    road_look: EnumProperty(
        name="Road Look",
        description="Road look (from /def/world/road_look*.sii) to preview this template with",
        items=_look_items,
        update=_on_look_change,
    )
    lane_variant: EnumProperty(
        name="Lane Variant",
        description="Road template variant: sets AI lanes and limits which line variants the editor allows",
        items=_variant_items,
    )


class SCS_TOOLS_OT_RoadLookSetParts(bpy.types.Operator):
    """Show or hide road look additional parts during variant preview"""
    bl_idname = "object.scs_tools_road_look_set_parts"
    bl_label = "Set Road Look Parts"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    mode: EnumProperty(items=(("ALL", "All", ""), ("NONE", "None", ""), ("TOGGLE", "Toggle", ""), ("SCHEME", "Scheme", "")))
    part_name: StringProperty()
    scheme: StringProperty()

    def execute(self, context):
        root = _root(context)
        look = get_selected_look(context)
        if not root or not look:
            return {'CANCELLED'}
        existing = _model_parts(root)
        add_parts = [p for p in look.add_parts if p in existing]
        overlay_parts = {p for _, _, parts in look.parsed_overlay_schemes() for p, _ in parts}
        current = _extra_parts(root)

        if self.mode == "ALL":
            before = [p for p in current if p in add_parts]
            if add_parts and all(p in current for p in add_parts) and "scs_preview_parts_before_all" in root:
                # second click on All: go back to the selection from before
                previous = [p for p in root["scs_preview_parts_before_all"].split(";") if p]
                current = [p for p in current if p not in add_parts] + [p for p in previous if p in add_parts]
                del root["scs_preview_parts_before_all"]
            else:
                root["scs_preview_parts_before_all"] = ";".join(before)
                current = [p for p in current if p not in add_parts] + add_parts
        elif self.mode == "NONE":
            current = [p for p in current if p not in add_parts]
        elif self.mode == "TOGGLE":
            if self.part_name in current:
                current.remove(self.part_name)
            else:
                current.append(self.part_name)
        elif self.mode == "SCHEME":
            scheme_parts = []
            for name, _, parts in look.parsed_overlay_schemes():
                if name == self.scheme:
                    scheme_parts = [p for p, _ in parts if p in existing]
            # one scheme at a time; schemes share parts (light is a subset of medium),
            # so the active one is remembered by name rather than guessed from the parts shown
            already = root.get("scs_preview_overlay_scheme", "") == self.scheme
            current = [p for p in current if p not in overlay_parts]
            if already:
                if "scs_preview_overlay_scheme" in root:
                    del root["scs_preview_overlay_scheme"]
            else:
                current += scheme_parts
                root["scs_preview_overlay_scheme"] = self.scheme

        _set_extra_parts(root, current)
        if not root.scs_props.scs_root_variant_preview:
            root.scs_props.scs_root_variant_preview = True
        return {'FINISHED'}


class SCS_TOOLS_OT_RoadLookFilterGrid(bpy.types.Operator):
    """Limit the Variant Grid (and its warnings) to the line variants this lane variant allows"""
    bl_idname = "object.scs_tools_road_look_filter_grid"
    bl_label = "Filter Variant Grid"
    bl_options = {'INTERNAL'}

    clear: BoolProperty(default=False)

    def execute(self, context):
        grid = getattr(context.window_manager, "scs_variant_grid", None)
        if grid is None:
            return {'CANCELLED'}
        tv = get_selected_template_variant(context)
        if self.clear or not tv or not tv.model_variants:
            grid.variant_filter = ""
        else:
            # exact names: wildcard-free patterns would also match longer names, so anchor them
            grid.variant_filter = ", ".join("[%s]%s" % (n[0], n[1:]) if n else n for n in tv.model_variants)
        return {'FINISHED'}


class SCS_TOOLS_OT_RoadLookReload(bpy.types.Operator):
    """Re-read road look definitions from the data folders"""
    bl_idname = "object.scs_tools_road_look_reload"
    bl_label = "Reload Road Looks"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        looks, variants = _road_look.load_road_looks(force=True)
        self.report({'INFO'}, "Road looks: %d, template variants: %d" % (len(looks), len(variants)))
        return {'FINISHED'}


class SCS_TOOLS_PT_RoadLook(bpy.types.Panel):
    """Road look preview sub-panel of SCS Variants."""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "SCS_TOOLS_PT_Variants"
    bl_label = "Road Look Preview"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.scs_props.empty_object_type == 'SCS_Root'

    def draw(self, context):
        layout = self.layout
        root = _root(context)
        settings = context.window_manager.scs_road_look

        row = layout.row(align=True)
        row.prop(settings, "road_look", text="")
        row.prop(settings, "show_all", text="", icon='WORLD')
        row.operator("object.scs_tools_road_look_reload", text="", icon='FILE_REFRESH')

        looks, _ = _road_look.load_road_looks()
        if not looks:
            layout.label(text="No road_look*.sii found in data folders (def/world).", icon='ERROR')
            return

        look = get_selected_look(context)
        if not look:
            if not _road_look.looks_for_template(root.name):
                layout.label(text="No road look uses a template named %r." % root.name, icon='INFO')
            return

        info = layout.box().column(align=True)
        info.label(text="Templates: %s" % ", ".join(look.template_names()), icon='MOD_ARRAY')
        details = []
        if look.road_offset is not None:
            details.append("road offset %.2f m" % look.road_offset)
        if look.shoulder_space_left is not None:
            details.append("shoulder space %.2f / %.2f m" % (look.shoulder_space_left, look.shoulder_space_right or 0.0))
        if details:
            info.label(text=", ".join(details))
        info.label(text="Compatible edges: %d right, %d left" % (len(look.compatible_edges_right), len(look.compatible_edges_left)))

        # lane variant -> allowed line variants
        layout.label(text="Lane variant (limits line variants):")
        layout.prop(settings, "lane_variant", text="")
        tv = get_selected_template_variant(context)
        inventory = root.scs_object_variant_inventory
        if tv:
            box = layout.box().column(align=True)
            if tv.model_variants:
                box.label(text="Allowed line variants (click to preview):")
                flow = box.grid_flow(columns=2, even_columns=True, align=True)
                for name in tv.model_variants:
                    idx = next((i for i, v in enumerate(inventory) if v.name == name), -1)
                    sub = flow.row(align=True)
                    sub.enabled = idx >= 0
                    op = sub.operator("object.scs_tools_vgrid_select", text=name if idx >= 0 else name + " (missing)",
                                      depress=(idx == root.scs_props.active_scs_variant))
                    op.variant_index = max(idx, 0)
            else:
                box.label(text="Any line variant allowed.")
            lanes = "AI lanes: %d left, %d right" % (len(tv.lanes_left), len(tv.lanes_right))
            box.label(text=lanes)
            row = box.row(align=True)
            row.operator("object.scs_tools_road_look_filter_grid", text="Filter Variant Grid", icon='FILTER')
            row.operator("object.scs_tools_road_look_filter_grid", text="", icon='X').clear = True

        # additional parts
        existing = _model_parts(root)
        shown = set(_extra_parts(root))
        add_parts = look.add_parts
        if add_parts:
            box = layout.box().column(align=True)
            row = box.row(align=True)
            row.label(text="Additional parts (editor 'Misc'):", icon='MOD_BUILD')
            all_on = all(p in shown for p in add_parts if p in existing) and any(p in existing for p in add_parts)
            row.operator("object.scs_tools_road_look_set_parts", text="All", depress=all_on).mode = "ALL"
            row.operator("object.scs_tools_road_look_set_parts", text="None").mode = "NONE"
            flow = box.grid_flow(columns=3, even_columns=True, align=True)
            for part in add_parts:
                sub = flow.row(align=True)
                sub.enabled = part in existing
                op = sub.operator("object.scs_tools_road_look_set_parts", text=part, depress=part in shown)
                op.mode = "TOGGLE"
                op.part_name = part

        # overlay schemes
        schemes = look.parsed_overlay_schemes()
        if schemes:
            box = layout.box().column(align=True)
            box.label(text="Overlay schemes (shows all parts of one scheme):", icon='TEXTURE')
            flow = box.grid_flow(columns=3, even_columns=True, align=True)
            for name, prob, parts in schemes:
                present = [p for p, _ in parts if p in existing]
                active = (root.get("scs_preview_overlay_scheme", "") == name
                          and all(p in shown for p in present))
                op = flow.operator("object.scs_tools_road_look_set_parts", text="%s (%d)" % (name, len(present)),
                                   depress=active)
                op.mode = "SCHEME"
                op.scheme = name

        layout.label(text="Source: %s" % look.source.replace("\\", "/").split("/def/")[-1], icon='FILE_TEXT')


classes = (
    SCS_TOOLS_RoadLookSettings,
    SCS_TOOLS_OT_RoadLookSetParts,
    SCS_TOOLS_OT_RoadLookFilterGrid,
    SCS_TOOLS_OT_RoadLookReload,
    SCS_TOOLS_PT_RoadLook,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.scs_road_look = PointerProperty(type=SCS_TOOLS_RoadLookSettings)


def unregister():
    del bpy.types.WindowManager.scs_road_look
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
