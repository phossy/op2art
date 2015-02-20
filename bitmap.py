"""Bitmap routines for handling contents of OP2_ART.bmp.
BMPs are documented here: http://en.wikipedia.org/wiki/BMP_file_format#mediaviewer/File:BMPfileFormat.png
"""

import struct

BITMAPFILEHEADER = struct.Struct('<2s I hh I')
BITMAPINFOHEADER = struct.Struct('<IiihhIIiiII')

class Bitmap(object):
    def __init__(self):
        self.palette = None
        self.width = 0
        self.height = 0
        self.data = bytearray()
        self.image_type = 0
        self.palette_id = 0

    def LoadBMP(self, filename):
        raise NotImplementedError

    def WriteBMP(self, filename):
        """Writes the image to a standard .BMP file."""
        with open(filename, 'wb') as f:
            # BITMAPINFOHEADER (size, w, h, planes, bpp, compression, image size, h res, v res, num colors, num important colors)
            # Height is negative, since OP2 stores these in top down (sane) manner
            bpp = 1 if self.image_type in [4, 5] else 8
            info_header = BITMAPINFOHEADER.pack(40, self.width, -self.height, 1, bpp, 0, 0, 0, 0, len(self.palette.colors), 0)
            # BITMAPFILEHEADER (signature, file size, 2x reserved, data offset)
            file_header = BITMAPFILEHEADER.pack('BM', 14 + len(info_header) + len(self.palette.colors) * 4 + len(self.data), 0, 0, 14 + len(info_header) +
                    len(self.palette.colors) * 4)
            f.write(file_header)
            f.write(info_header)
            self.palette.WriteColorTable(f)
            f.write(self.data)
