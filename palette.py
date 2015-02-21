"""Implementation of OP2_ART palette, including RIFF PAL conversion.
The RIFF format is documented here: http://www.aelius.com/njh/wavemetatools/doc/riffmci.pdf
"""

import collections
import struct

Color = collections.namedtuple('Color', ['r', 'g', 'b', 'flags'])

RIFF_HEADER = struct.Struct('<4s I')
PAL_HEADER = struct.Struct('<8s I hh')
PAL_ENTRY = struct.Struct('<4B')

class PaletteLoadError(Exception):
    pass

class Palette(object):
    def __init__(self):
        self.colors = []

    def ReadColorTable(self, f, num_colors=256, reverse=False):
        """Reads the color table from open file f."""
        for i in xrange(num_colors):
            rgba = PAL_ENTRY.unpack(f.read(4))
            if reverse:
                self.colors.append(Color(r=rgba[2], g=rgba[1], b=rgba[0], flags=rgba[3]))
            else:
                self.colors.append(Color(r=rgba[0], g=rgba[1], b=rgba[2], flags=rgba[3]))

    def WriteColorTable(self, f, reverse=False):
        """Writes the color table to open file f."""
        # Color data (windows LOGPALETTE format)
        for color in self.colors:
            if reverse:
                packed_color = PAL_ENTRY.pack(color.b, color.g, color.r, color.flags)
            else:
                packed_color = PAL_ENTRY.pack(color.r, color.g, color.b, color.flags)
            f.write(packed_color)

    def LoadPAL(self, filename):
        """Loads a palette from filename in Microsoft PAL format."""
        with open(filename, 'rb') as f:
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

    def WritePAL(self, filename):
        """Writes the palette to filename in Microsoft PAL format."""
        with open(filename, 'wb') as f:
            # RIFF format: fourcc ("RIFF"), length
            # PAL chunk format: fourcc ("PAL "), "data", length, version (0x0300), num colors
            data_header = PAL_HEADER.pack('PAL data', len(self.colors) * 4 + 4, 0x0300, len(self.colors))
            riff_header = RIFF_HEADER.pack('RIFF', len(data_header))
            f.write(riff_header)
            f.write(data_header)
            self.WriteColorTable(f, reverse=True)
