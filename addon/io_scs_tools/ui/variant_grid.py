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

"""Variant grid: every variant against every part of an SCS root, edited like a spreadsheet.

It's a view on the existing data (Object.scs_object_variant_inventory[*].parts[*].include),
so nothing changes in the file format or on export.
"""

import bpy
import fnmatch
from bpy.props import BoolProperty, IntProperty, StringProperty, PointerProperty
from ..utils import object as _object_utils

BASE_PARTS = ("vis", "vis_tran", "coll")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _match(name, pattern):
    """Case-insensitive match; plain text matches as substring, '*' and '?' as wildcards.
    Several patterns may be given separated by commas."""
    if not pattern.strip():
        return True
    name = name.lower()
    for pat in pattern.lower().split(","):
        pat = pat.strip()
        if not pat:
            continue
        if any(c in pat for c in "*?["):
            if fnmatch.fnmatch(name, pat):
                return True
        elif pat in name:
            return True
    return False


def get_root(context):
    obj = context.active_object
    return _object_utils.get_scs_root(obj) if obj else None


def get_part_names(root):
    return [p.name for p in root.scs_object_part_inventory]


def get_variant_part(variant, part_name, create=False):
    """Get variant's part inclusion entry, optionally creating it."""
    for part in variant.parts:
        if part.name == part_name:
            return part
    if create:
        part = variant.parts.add()
        part.name = part_name
        part.include = False
        return part
    return None


def is_included(variant, part_name):
    part = get_variant_part(variant, part_name)
    return bool(part and part.include)


_STASH_KEY = "scs_vgrid_stash"


def _load_stash(root):
    import json
    try:
        return json.loads(root.get(_STASH_KEY, "{}"))
    except (ValueError, TypeError):
        return {}


def _save_stash(root, stash):
    import json
    if stash.get("variant") or stash.get("part"):
        root[_STASH_KEY] = json.dumps(stash)
    elif _STASH_KEY in root:
        del root[_STASH_KEY]


def has_stash(root):
    stash = _load_stash(root)
    return bool(stash.get("variant") or stash.get("part"))


def get_filtered(root, settings):
    """Return (variant indices, part names) after filters."""
    parts = [p for p in get_part_names(root)
             if _match(p, settings.part_filter) and not (settings.hide_base and p in BASE_PARTS)]
    variants = [i for i, v in enumerate(root.scs_object_variant_inventory) if _match(v.name, settings.variant_filter)]
    return variants, parts


def get_warnings(root):
    """Return list of warning strings for the grid."""
    warnings = []
    variants = root.scs_object_variant_inventory
    parts = get_part_names(root)

    used = {p.name for v in variants for p in v.parts if p.include}
    unused = [p for p in parts if p not in used]
    if unused:
        warnings.append("%d part(s) in no variant: %s%s (fine for road look additional parts and overlays)" % (
            len(unused), ", ".join(unused[:6]), ", ..." if len(unused) > 6 else ""))

    seen = {}
    for v in variants:
        key = tuple(sorted(p.name for p in v.parts if p.include))
        if not key:
            warnings.append("Variant %r shows no parts" % v.name)
            continue
        if key in seen:
            warnings.append("Variants %r and %r are identical" % (seen[key], v.name))
        else:
            seen[key] = v.name
    return warnings


def refresh_preview(root):
    """Re-apply variant preview after edits, if preview is on."""
    try:
        if root.scs_props.scs_root_variant_preview:
            _object_utils.apply_variant_visibility(root, root.scs_props.active_scs_variant)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------

class SCS_TOOLS_VariantGridSettings(bpy.types.PropertyGroup):
    part_filter: StringProperty(
        name="Part Filter",
        description="Show only parts whose name contains this text. Wildcards (* ?) and several patterns "
                    "separated by commas work, e.g. 'brk*, sng*'",
        default="",
    )
    variant_filter: StringProperty(
        name="Variant Filter",
        description="Show only variants whose name contains this text (wildcards and commas work)",
        default="",
    )
    hide_base: BoolProperty(
        name="Hide Base Parts",
        description="Hide vis, vis_tran and coll columns (they are in every variant of a road template)",
        default=False,
    )
    columns: IntProperty(
        name="Columns",
        description="How many part columns to show at once (0 = as many as fit the panel width); "
                    "use the arrows to page through the rest",
        default=0, min=0, max=60,
    )
    page: IntProperty(name="Page", default=0, min=0)


# ---------------------------------------------------------------------------
# operators
# ---------------------------------------------------------------------------

class SCS_TOOLS_OT_VariantGridToggle(bpy.types.Operator):
    """Include or exclude this part in this variant"""
    bl_idname = "object.scs_tools_vgrid_toggle"
    bl_label = "Toggle Part in Variant"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    variant_index: IntProperty()
    part_name: StringProperty()

    def execute(self, context):
        root = get_root(context)
        if not root or not (0 <= self.variant_index < len(root.scs_object_variant_inventory)):
            return {'CANCELLED'}
        part = get_variant_part(root.scs_object_variant_inventory[self.variant_index], self.part_name, create=True)
        part.include = not part.include
        refresh_preview(root)
        return {'FINISHED'}


class SCS_TOOLS_OT_VariantGridTogglePart(bpy.types.Operator):
    """Include this part in every shown variant. Click again to go back to how the column was before"""
    bl_idname = "object.scs_tools_vgrid_toggle_part"
    bl_label = "Toggle Part in All Variants"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    part_name: StringProperty()

    def execute(self, context):
        root = get_root(context)
        if not root:
            return {'CANCELLED'}
        settings = context.window_manager.scs_variant_grid
        variant_ids, _ = get_filtered(root, settings)
        variants = [root.scs_object_variant_inventory[i] for i in variant_ids]
        stash = _load_stash(root)
        part_stash = stash.setdefault("part", {})
        all_in = all(is_included(v, self.part_name) for v in variants)
        previous = part_stash.pop(self.part_name, None)
        if all_in and previous is not None:
            # second click: go back to how the column looked before "all" was switched on
            for v in variants:
                get_variant_part(v, self.part_name, create=True).include = bool(previous.get(v.name, False))
        else:
            if not all_in:
                part_stash[self.part_name] = {v.name: is_included(v, self.part_name) for v in variants}
            for v in variants:
                get_variant_part(v, self.part_name, create=True).include = not all_in
        _save_stash(root, stash)
        refresh_preview(root)
        return {'FINISHED'}


class SCS_TOOLS_OT_VariantGridToggleVariant(bpy.types.Operator):
    """Include every shown part in this variant. Click again to go back to the parts it had before"""
    bl_idname = "object.scs_tools_vgrid_toggle_variant"
    bl_label = "Toggle All Shown Parts in Variant"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    variant_index: IntProperty()

    def execute(self, context):
        root = get_root(context)
        if not root or not (0 <= self.variant_index < len(root.scs_object_variant_inventory)):
            return {'CANCELLED'}
        settings = context.window_manager.scs_variant_grid
        _, part_names = get_filtered(root, settings)
        variant = root.scs_object_variant_inventory[self.variant_index]
        stash = _load_stash(root)
        var_stash = stash.setdefault("variant", {})
        all_in = all(is_included(variant, p) for p in part_names)
        previous = var_stash.pop(variant.name, None)
        if all_in and previous is not None:
            # second click: go back to the parts this variant had before "all" was switched on
            for p in part_names:
                get_variant_part(variant, p, create=True).include = p in previous
        else:
            if not all_in:
                var_stash[variant.name] = [p for p in part_names if is_included(variant, p)]
            for p in part_names:
                get_variant_part(variant, p, create=True).include = not all_in
        _save_stash(root, stash)
        refresh_preview(root)
        return {'FINISHED'}


class SCS_TOOLS_OT_VariantGridRestore(bpy.types.Operator):
    """Undo every "all" toggle in the grid: put the variants back to the parts they had before"""
    bl_idname = "object.scs_tools_vgrid_restore"
    bl_label = "Restore Variants"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        root = get_root(context)
        if not root:
            return {'CANCELLED'}
        stash = _load_stash(root)
        inventory = root.scs_object_variant_inventory
        by_name = {v.name: v for v in inventory}
        for part_name, states in stash.get("part", {}).items():
            for vname, state in states.items():
                if vname in by_name:
                    get_variant_part(by_name[vname], part_name, create=True).include = bool(state)
        for vname, parts in stash.get("variant", {}).items():
            v = by_name.get(vname)
            if not v:
                continue
            for part in v.parts:
                part.include = part.name in parts
        _save_stash(root, {})
        refresh_preview(root)
        return {'FINISHED'}


class SCS_TOOLS_OT_VariantGridSelect(bpy.types.Operator):
    """Make this the active variant (and preview it if variant preview is on)"""
    bl_idname = "object.scs_tools_vgrid_select"
    bl_label = "Select Variant"
    bl_options = {'INTERNAL'}

    variant_index: IntProperty()

    def execute(self, context):
        root = get_root(context)
        if not root:
            return {'CANCELLED'}
        root.scs_props.active_scs_variant = self.variant_index
        return {'FINISHED'}


class SCS_TOOLS_OT_VariantGridDuplicate(bpy.types.Operator):
    """Duplicate this variant with the same parts (rename the copy in the variant list)"""
    bl_idname = "object.scs_tools_vgrid_duplicate"
    bl_label = "Duplicate Variant"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    variant_index: IntProperty()

    def execute(self, context):
        root = get_root(context)
        inv = root.scs_object_variant_inventory if root else None
        if not inv or not (0 <= self.variant_index < len(inv)):
            return {'CANCELLED'}
        src = inv[self.variant_index]
        included = {p.name: p.include for p in src.parts}
        base_name = src.name
        new = inv.add()
        new.name = base_name + "_copy"
        for part_name in get_part_names(root):
            part = new.parts.add()
            part.name = part_name
            part.include = included.get(part_name, False)
        # place the copy right after its source
        inv.move(len(inv) - 1, self.variant_index + 1)
        root.scs_props.active_scs_variant = self.variant_index + 1
        return {'FINISHED'}


class SCS_TOOLS_OT_VariantGridPage(bpy.types.Operator):
    """Show previous / next page of part columns"""
    bl_idname = "object.scs_tools_vgrid_page"
    bl_label = "Page Columns"
    bl_options = {'INTERNAL'}

    step: IntProperty(default=1)

    def execute(self, context):
        settings = context.window_manager.scs_variant_grid
        settings.page = max(0, settings.page + self.step)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# panel
# ---------------------------------------------------------------------------

class SCS_TOOLS_PT_VariantGrid(bpy.types.Panel):
    """Variant grid sub-panel of SCS Variants."""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = "SCS_TOOLS_PT_Variants"
    bl_label = "Variant Grid"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.scs_props.empty_object_type == 'SCS_Root'

    def draw(self, context):
        layout = self.layout
        root = get_root(context)
        settings = context.window_manager.scs_variant_grid
        variants = root.scs_object_variant_inventory

        if not variants or not root.scs_object_part_inventory:
            layout.label(text="No variants or parts on this SCS root.", icon='INFO')
            return

        # filters
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(settings, "part_filter", text="", icon='VIEWZOOM', placeholder="Parts: e.g. brk*, sng*")
        row.prop(settings, "hide_base", text="", icon='HIDE_ON' if settings.hide_base else 'HIDE_OFF')
        row = col.row(align=True)
        row.prop(settings, "variant_filter", text="", icon='FILTER', placeholder="Variants: e.g. *_hw")
        row.prop(settings, "columns", text="Columns (0 = fit)")
        if has_stash(root):
            row = col.row(align=True)
            row.operator("object.scs_tools_vgrid_restore", text="Restore before 'all' toggles", icon='LOOP_BACK')

        variant_ids, part_names = get_filtered(root, settings)
        if not part_names or not variant_ids:
            layout.label(text="Nothing matches the filters.", icon='INFO')
            return

        # column widths in UI units, sized to their header text
        ui_scale = context.preferences.system.ui_scale or 1.0
        region_units = (context.region.width / (20.0 * ui_scale)) if context.region else 30.0
        longest_variant = max(len(variants[i].name) for i in variant_ids)
        name_units = min(max(longest_variant * 0.5 + 3.0, 7.0), 13.0)

        def part_units(name):
            return min(max(len(name) * 0.55 + 0.8, 1.6), 6.0)

        # split part columns into pages: fixed count, or as many as fit the panel
        pages = []
        if settings.columns > 0:
            for i in range(0, len(part_names), settings.columns):
                pages.append(part_names[i:i + settings.columns])
        else:
            available = max(region_units - name_units - 2.0, 4.0)
            current, used = [], 0.0
            for name in part_names:
                w = part_units(name)
                if current and used + w > available:
                    pages.append(current)
                    current, used = [], 0.0
                current.append(name)
                used += w
            if current:
                pages.append(current)

        page = min(settings.page, len(pages) - 1)
        shown_parts = pages[page]
        first = sum(len(p) for p in pages[:page])
        if len(pages) > 1:
            row = layout.row(align=True)
            sub = row.row(align=True)
            sub.enabled = page > 0
            sub.operator("object.scs_tools_vgrid_page", text="", icon='TRIA_LEFT').step = -1
            row.label(text="Parts %d-%d of %d (page %d/%d)" % (first + 1, first + len(shown_parts), len(part_names),
                                                              page + 1, len(pages)))
            sub = row.row(align=True)
            sub.enabled = page < len(pages) - 1
            sub.operator("object.scs_tools_vgrid_page", text="", icon='TRIA_RIGHT').step = 1

        box = layout.box()
        table = box.row(align=False)
        active = root.scs_props.active_scs_variant

        # first column: variant names with row tools
        name_col = table.column(align=True)
        name_col.ui_units_x = name_units
        name_col.label(text="Variant / Part")
        for vi in variant_ids:
            variant = variants[vi]
            name_row = name_col.row(align=True)
            op = name_row.operator("object.scs_tools_vgrid_select", text=variant.name, depress=(vi == active))
            op.variant_index = vi
            name_row.operator("object.scs_tools_vgrid_toggle_variant", text="", icon='CHECKMARK').variant_index = vi
            name_row.operator("object.scs_tools_vgrid_duplicate", text="", icon='DUPLICATE').variant_index = vi

        # one column per part: header (toggle in all variants) + one checkbox per variant
        for part_name in shown_parts:
            col = table.column(align=True)
            col.ui_units_x = part_units(part_name)
            all_in = all(is_included(variants[i], part_name) for i in variant_ids)
            op = col.operator("object.scs_tools_vgrid_toggle_part", text=part_name, depress=all_in)
            op.part_name = part_name
            for vi in variant_ids:
                inc = is_included(variants[vi], part_name)
                op = col.operator("object.scs_tools_vgrid_toggle", text="",
                                  icon='CHECKBOX_HLT' if inc else 'CHECKBOX_DEHLT', depress=inc)
                op.variant_index = vi
                op.part_name = part_name

        # warnings
        warnings = get_warnings(root)
        if warnings:
            box = layout.box().column(align=True)
            for w in warnings[:8]:
                box.label(text=w, icon='ERROR')
            if len(warnings) > 8:
                box.label(text="... %d more" % (len(warnings) - 8))

        layout.label(text="Rename parts in the SCS Parts list; the grid and every variant follow.", icon='INFO')


classes = (
    SCS_TOOLS_VariantGridSettings,
    SCS_TOOLS_OT_VariantGridToggle,
    SCS_TOOLS_OT_VariantGridTogglePart,
    SCS_TOOLS_OT_VariantGridToggleVariant,
    SCS_TOOLS_OT_VariantGridRestore,
    SCS_TOOLS_OT_VariantGridSelect,
    SCS_TOOLS_OT_VariantGridDuplicate,
    SCS_TOOLS_OT_VariantGridPage,
    SCS_TOOLS_PT_VariantGrid,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.scs_variant_grid = PointerProperty(type=SCS_TOOLS_VariantGridSettings)


def unregister():
    del bpy.types.WindowManager.scs_variant_grid
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
