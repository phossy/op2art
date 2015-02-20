"""Implementation of OP2_ART palette, including RIFF PAL conversion.
The RIFF format is documented here: http://www.aelius.com/njh/wavemetatools/doc/riffmci.pdf
"""

import collections
import struct

Color = collections.namedtuple('Color', ['r', 'g', 'b', 'flags'])

RIFF_HEADER = struct.Struct('<4s I')
PAL_HEADER = struct.Struct('<8s I hh')

class Palette(object):
    def __init__(self):
        self.colors = []

    def LoadPAL(self, filename):
        raise NotImplementedError

    def WriteColorTable(self, f):
        """Writes the color table to open file f."""
        # Color data (windows LOGPALETTE format)
        for color in self.colors:
            packed_color = struct.pack('<4B', color.r, color.g, color.b, color.flags)
            f.write(packed_color)

    def WritePAL(self, filename):
        """Writes the palette to filename in Microsoft PAL format."""
        with open(filename, 'wb') as f:
            # RIFF format: fourcc ("RIFF"), length
            # PAL chunk format: fourcc ("PAL "), "data", length, version (0x0300), num colors
            data_header = struct.pack('<8s I hh', 'PAL data', len(self.colors) * 4 + 4, 0x0300, len(self.colors))
            riff_header = struct.pack('<4s I', 'RIFF', len(data_header))
            f.write(riff_header)
            f.write(data_header)
            self.WriteColorTable(f)
