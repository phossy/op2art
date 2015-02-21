"""Implementation of OP2_ART palette, including RIFF PAL conversion.
The RIFF format is documented here: http://www.aelius.com/njh/wavemetatools/doc/riffmci.pdf
"""

import collections
import struct

Color = collections.namedtuple('Color', ['r', 'g', 'b', 'flags'])

RIFF_HEADER = struct.Struct('<4s I')
PAL_HEADER = struct.Struct('<8s I hh')
PAL_ENTRY = struct.Struct('<4B')

PAL = 0  # Microsoft palette (RIFF PAL)
TEXT = 1  # Text format (Paint Shop Pro/'JASC-PAL' format)
ACT = 2  # Photoshop .act format

class PaletteLoadError(Exception):
    pass

class Palette(object):
    def __init__(self):
        self.colors = []

    def ReadColorTable(self, f, num_colors=256, reverse=False, file_format=PAL):
        """Reads the color table from open file f."""
        for i in xrange(num_colors):
            if file_format == PAL:
                rgba = PAL_ENTRY.unpack(f.read(4))
                if reverse:
                    self.colors.append(Color(r=rgba[2], g=rgba[1], b=rgba[0], flags=rgba[3]))
                else:
                    self.colors.append(Color(r=rgba[0], g=rgba[1], b=rgba[2], flags=rgba[3]))
            elif file_format == ACT:
                rgb = struct.unpack('<3B', f.read(3))
                if reverse:
                    self.colors.append(Color(r=rgb[2], g=rgb[1], b=rgb[0], flags=0))
                else:
                    self.colors.append(Color(r=rgb[0], g=rgb[1], b=rgb[2], flags=0))
            elif file_format == TEXT:
                rgb = f.readline().split(None, 3)
                self.colors.append(Color(r=int(rgb[0]), g=int(rgb[1]), b=int(rgb[2]), flags=0))
            else:
                raise ValueError('invalid format')

    def WriteColorTable(self, f, reverse=False, file_format=PAL):
        """Writes the color table to open file f."""
        # Color data (windows LOGPALETTE format)
        for color in self.colors:
            if file_format == PAL:
                if reverse:
                    packed_color = PAL_ENTRY.pack(color.b, color.g, color.r, color.flags)
                else:
                    packed_color = PAL_ENTRY.pack(color.r, color.g, color.b, color.flags)
                f.write(packed_color)
            elif file_format == ACT:
                if reverse:
                    f.write(struct.pack('<3B', color.b, color.g, color.r))
                else:
                    f.write(struct.pack('<3B', color.r, color.g, color.b))
            elif file_format == TEXT:
                f.write('%d %d %d\n' % (color.r, color.g, color.b))
            else:
                raise ValueError('invalid format')

    def LoadPAL(self, filename, file_format=TEXT):
        """Loads a palette from filename."""
        with open(filename, 'rb') as f:
            if file_format == PAL:
                riff_tag, riff_size = RIFF_HEADER.unpack(f.read(8))
                if riff_tag != 'RIFF':
                    raise PaletteLoadError('Palette file is not a RIFF file')
                if riff_size != 16:
                    raise PaletteLoadError('Invalid RIFF section size')
                pal_tag, pal_size, pal_ver, pal_colors = PAL_HEADER.unpack(f.read(16))
                if pal_tag != 'PAL data':
                    raise PaletteLoadError('PAL data section is missing')
                if pal_ver != 0x0300:
                    raise PaletteLoadError('Expected version 0x0300, got %x' % pal_ver)
                if pal_size != pal_colors * 4 + 4:
                    raise PaletteLoadError('Invalid palette size (%d, expected %d)' % (pal_size, pal_colors * 4 + 4))
                self.ReadColorTable(f, num_colors=pal_colors, reverse=True)
            elif file_format == TEXT:
                sig = f.readline().strip()
                if sig != 'JASC-PAL':
                    raise PaletteLoadError('Palette file is not a text palette')
                ver = f.readline().strip()
                if ver != '0100':
                    raise PaletteLoadError('Wrong version')
                num_colors = int(f.readline().strip())
                self.ReadColorTable(f, num_colors=num_colors, file_format=TEXT)
            elif file_format == ACT:
                # No header, just read raw RGB data
                self.ReadColorTable(f, num_colors=256, reverse=True, file_format=ACT)
            else:
                raise ValueError('invalid format')

    def WritePAL(self, filename, file_format=TEXT):
        """Writes the palette to filename."""
        with open(filename, 'wb') as f:
            if file_format == PAL:
                # RIFF format: fourcc ("RIFF"), length
                # PAL chunk format: fourcc ("PAL "), "data", length, version (0x0300), num colors
                data_header = PAL_HEADER.pack('PAL data', len(self.colors) * 4 + 4, 0x0300, len(self.colors))
                riff_header = RIFF_HEADER.pack('RIFF', len(data_header))
                f.write(riff_header)
                f.write(data_header)
                self.WriteColorTable(f, reverse=True)
            elif file_format == TEXT:
                f.write('JASC-PAL\n')
                f.write('0100\n')
                f.write('%d\n' % len(self.colors))
                self.WriteColorTable(f, file_format=TEXT)
            elif file_format == ACT:
                if len(self.colors) != 256:
                    raise ValueError('Photoshop ACT format supports only 256 colors')
                self.WriteColorTable(f, reverse=True, file_format=ACT)
            else:
                raise ValueError('invalid format')
