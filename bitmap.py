"""Bitmap routines for handling contents of OP2_ART.bmp.
BMPs are documented here: http://en.wikipedia.org/wiki/BMP_file_format#mediaviewer/File:BMPfileFormat.png
"""

import struct

BITMAPFILEHEADER = struct.Struct('<2s I hh I')
BITMAPINFOHEADER = struct.Struct('<IiihhIIiiII')

class BitmapLoadError(Exception):
    pass

class Bitmap(object):
    def __init__(self):
        self.palette = None
        self.width = 0
        self.height = 0
        self.data = bytearray()
        self.image_type = 0
        self.palette_id = 0
        self.offset = 0

    def LoadBMP(self, filename):
        """Reads the image from a standard .BMP file."""
        with open(filename, 'rb') as f:
            sig, file_size, _, _, data_offset = BITMAPFILEHEADER.unpack(f.read(14))
            if sig != 'BM':
                raise BitmapLoadError('not a valid windows BMP file')
            # Height is negative, since OP2 stores these in top down (sane) manner
            info_size, self.width, self.height, _, bpp, _, _, _, _, pal_len, _ = BITMAPINFOHEADER.unpack(f.read(40))
            if info_size != 40:
                raise BitmapLoadError('cannot handle bitmaps that do not use BITMAPINFOHEADER')
            if pal_len != 256:
                raise BitmapLoadError('unexpected palette length (got %d, expected 256)' % pal_len)
            if bpp not in [1, 8]:
                raise BitmapLoadError('only 1- and 8-bpp bitmaps are supported by the game')
            if self.height > 0:
                raise BitmapLoadError('only top-down bitmaps (height < 0) are supported')
            self.height = -self.height
            f.seek(data_offset)
            padded_width = (self.width + 3) & ~3
            self.data = bytearray(f.read(padded_width * self.height))

    def WriteBMPToOpenFile(self, f):
        """Writes the BMP data to an open file handle."""
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

    def WriteBMP(self, filename):
        """Writes the image to a standard .BMP file."""
        with open(filename, 'wb') as f:
            self.WriteBMPToOpenFile(f)
