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

# Copyright (C) 2015: SCS Software

from io_scs_tools.utils import path as _path
from io_scs_tools.utils.printout import lprint


_BINARY_TOBJ_MAGIC = 0x70b10a01
_BINARY_TOBJ_HEADER_SIZE = 40
_BINARY_ADDR = ("repeat", "clamp", "clamp_to_edge", "clamp_to_border", "mirror", "mirror_clamp", "mirror_clamp_to_edge")
_BINARY_FILTER = {0: "nearest", 1: "linear"}


def _parse_binary(filepath, raw):
    """Converts compiled (binary) TOBJ, as found in extracted game archives, into list of text records,
    equivalent to what text TOBJ parsing would return.

    Layout (40 byte header, then textures as: u32 length, u32 unknown, char[length]):
    +24 type (2 = generic/2d, 5 = cube), +26 mag filter, +27 min filter, +28 mip filter,
    +30..32 addr u/v/w, +33 compress (1 = no), +35 anisotropic (1 = no), +38 color space (1 = linear)

    :return: list of records or None if not binary TOBJ
    :rtype: list[str] | None
    """
    import struct

    if len(raw) < _BINARY_TOBJ_HEADER_SIZE or struct.unpack_from("<I", raw, 0)[0] != _BINARY_TOBJ_MAGIC:
        return None

    tex_type = raw[24]
    mag_filter, min_filter, mip_filter = raw[26], raw[27], raw[28]
    addr = raw[30:33]
    no_compress = raw[33] == 1
    no_anisotropic = raw[35] == 1
    color_space = raw[38]

    is_cube = tex_type == 5
    map_type = "cube" if is_cube else "2d"

    names = []
    offset = _BINARY_TOBJ_HEADER_SIZE
    while offset + 8 <= len(raw):
        length = struct.unpack_from("<I", raw, offset)[0]
        offset += 8
        if length <= 0 or offset + length > len(raw):
            break
        names.append(raw[offset:offset + length].decode("utf8", errors="replace"))
        offset += length

    if not names:
        return None

    data = ["map", map_type] + names

    addr_count = 3 if is_cube else 2
    data.append("addr")
    for i in range(addr_count):
        data.append(_BINARY_ADDR[addr[i]] if addr[i] < len(_BINARY_ADDR) else "repeat")

    if mag_filter in _BINARY_FILTER and min_filter in _BINARY_FILTER:
        data.extend(("filter", _BINARY_FILTER[mag_filter], _BINARY_FILTER[min_filter]))

    if mip_filter == 1:
        data.append("trilinear")
    elif mip_filter == 2:
        data.append("nomips")

    if no_compress:
        data.append("nocompress")
    if no_anisotropic:
        data.append("noanisotropic")
    if color_space == 1:
        data.extend(("color_space", "linear"))

    return data


def parse_file(filepath, print_info=False):
    """Reads data from TOBJ file and returns it's records as list.

    :param filepath: tobj file path
    :type filepath: str
    :param print_info: switch for printing parsing info
    :type print_info: bool
    :return: all TOBJ entries as list in the order they are saved in the file
    :rtype: list[str]
    """

    if print_info:
        print('** TOBJ Parser ...')
        print('   filepath: %r' % str(filepath))

    # compiled TOBJ from extracted game archives? convert it to text records directly
    try:
        with open(filepath, "rb") as bf:
            raw = bf.read()
        binary_data = _parse_binary(filepath, raw)
        if binary_data is not None:
            return binary_data
    except OSError:
        pass

    data = []
    with open(filepath, encoding="utf8") as f:

        try:

            for i, line in enumerate(f):
                line_split = line.strip().split()
                if len(line_split) != 0:

                    # ignore C-like comment lines
                    if line_split[0].startswith("//"):
                        continue

                    # ignore comment lines starting with #
                    if line_split[0].startswith("#"):
                        continue

                    for word in line_split:
                        data.append(word)

        except UnicodeDecodeError as e:

            # someone wants to open binary tobj, no go
            if e.reason == "invalid start byte":
                lprint("E Can't read TOBJ, most probably it's in binary version: %r", (_path.readable_norm(filepath),))

    f.close()

    return data
