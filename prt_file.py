"""Objects and reading/writing routines for PRT files."""

import collections
import struct

import bitmap
import palette

Rect = collections.namedtuple('Rect', ['left', 'top', 'right', 'bottom'])
Point = collections.namedtuple('Point', ['x', 'y'])

class PRTLoadError(Exception):
    pass

class PRTFile(object):
    def __init__(self, prt_file, bmp_file):
        self._prt_file = prt_file
        self._bmp_file = bmp_file
        self.palettes = []
        self.bitmaps = []
        self.animations = []
        self.num_optional_entries = 0
        self.extra_data = bytearray()

    def _ReadAndUnpack(self, fmt):
        s = struct.Struct(fmt)
        data = self._prt_file.read(s.size)
        if len(data) != s.size:
            raise PRTLoadError('ran out of data: expected %d bytes, got %d' % (s.size, len(data)))
        return s.unpack(data)

    def _LoadPalettes(self):
        """Loads the palette information ('CPAL' format)."""
        # Header (4 bytes 'CPAL' section tag plus 4 bytes number of palettes)
        tag, num_palettes = self._ReadAndUnpack('<4s I')
        if tag != 'CPAL':
            raise PRTLoadError('PRT signature was not CPAL')
        # Each palette consists of a PPAL section (1048 bytes), followed by a head section (4), then a data section (1024, i.e. 256 * 4 for each color)
        for i in xrange(num_palettes):
            pal = palette.Palette()
            num_tags_left = 2
            while num_tags_left > 0:
                num_tags_left = num_tags_left - 1
                tag, section_size = self._ReadAndUnpack('<4s I')
                if tag == 'PPAL':
                    if section_size != 1048:
                        raise PRTLoadError('Unexpected PPAL size (%d != 1048)' % section_size)
                elif tag == 'RIFF':
                    # TODO: we could probably support these
                    raise PRTLoadError('RIFF tag not implemented')
                elif tag == 'head':
                    if section_size != 4:
                        raise PRTLoadError('Unexpected head size (%d != 4)' % section_size)
                    num_tags_left, = self._ReadAndUnpack('<I')
                elif tag == 'data':
                    if section_size != 1024:
                        raise PRTLoadError('Unexpected data size (%d != 1024)' % section_size)
                    for j in xrange(256):
                        entry = self._ReadAndUnpack('<4B')
                        # Note that the blue and red channels appear to be swapped for some reason
                        pal.colors.append(palette.Color(r=entry[2], g=entry[1], b=entry[0], flags=entry[3]))
                else:
                    raise PRTLoadError('unhandled tag: %s (size=%d)' % (tag, section_size))
            self.palettes.append(pal)

    def _WritePalettes(self):
        """Writes the palette information ('CPAL' format)."""
        # Write the CPAL header
        self._prt_file.write(struct.pack('<4s I', 'CPAL', len(self.palettes)))
        # Write each PPAL section
        # Each palette consists of a PPAL section (1048 bytes), followed by a head section (4), then a data section (1024, i.e. 256 * 4 for each color)
        for pal in self.palettes:
            # PPAL
            self._prt_file.write(struct.pack('<4s I', 'PPAL', 1048))
            # head
            self._prt_file.write(struct.pack('<4s I I', 'head', 4, 1))
            # data
            self._prt_file.write(struct.pack('<4s I', 'data', 1024))
            for color in pal.colors:
                self._prt_file.write(struct.pack('<4B', color.b, color.g, color.r, color.flags))

    def _LoadBitmaps(self):
        """Loads the bitmap data (metadata + raw pixel data in bmp file)."""
        buf = self._bmp_file.read(14)
        signature, _, _, _, data_start = struct.unpack('<2s I hh I', buf)
        if signature != 'BM':
            raise PRTLoadError('OP2_ART.BMP is not a valid BMP file')
        num_bitmaps, = self._ReadAndUnpack('<I')
        for i in xrange(num_bitmaps):
            padded_w, offset, h, w, img_type, pal_id = self._ReadAndUnpack('<IIIIhh')
            if pal_id < 0 or pal_id > len(self.palettes) - 1:
                raise PRTLoadError('bitmap %d: palette_id %d out of range' % (i, pal_id))
            bmp = bitmap.Bitmap()
            bmp.palette = self.palettes[pal_id]
            bmp.palette_id = pal_id
            bmp.image_type = img_type
            bmp.width = w
            bmp.height = h
            # seek to the offset (relative to the start of the actual image data) and read the bitmap data
            self._bmp_file.seek(offset + data_start)
            bmp.data = bytearray(self._bmp_file.read(padded_w * h))
            self.bitmaps.append(bmp)

    def _WriteBitmaps(self):
        """Writes the bitmap data to the bmp file."""
        # Create one master bitmap and palette (the headers and palette info are totally ignored, the .bmp file is a glorified data buffer)
        master_bmp = bitmap.Bitmap()
        master_bmp.palette = palette.Palette()
        for i in xrange(256):
            master_bmp.palette.colors.append(palette.Color(r=0, g=0, b=0, flags=0))

        # Write the bitmap metadata to the prt file
        self._prt_file.write(struct.pack('<I', len(self.bitmaps)))
        for bmp in self.bitmaps:
            # TODO: sanity check the metadata here, like making sure it uses a valid palette ID, etc.
            padded_width = (bmp.width + 3) & ~3
            self._prt_file.write(struct.pack('<IIIIhh', padded_width, len(master_bmp.data), bmp.height, bmp.width, bmp.image_type, bmp.palette_id))
            master_bmp.data.extend(bmp.data)
        master_bmp.WriteBMPToOpenFile(self._bmp_file)

    def Load(self):
        self._LoadPalettes()
        self._LoadBitmaps()
        num_anims, = self._ReadAndUnpack('<I')
        num_frames, = self._ReadAndUnpack('<I')
        num_subframes, = self._ReadAndUnpack('<I')
        self.num_optional_entries, = self._ReadAndUnpack('<I')
        num_loaded_frames = 0
        num_loaded_subframes = 0
        # animations
        for i in xrange(num_anims):
            unk1, left, top, right, bottom, x_off, y_off, unk2, frames = self._ReadAndUnpack('<IIIIIIIII')
            animation = {
                'unknown1': unk1,
                'bounding_box': Rect(left=left, top=top, right=right, bottom=bottom),
                'offset': Point(x=x_off, y=y_off),
                'unknown2': unk2,
                'frames': [],
                'appendix': []
            }
            # frames
            for j in xrange(frames):
                subframes, unknown = self._ReadAndUnpack('<BB')
                optional1 = None
                optional2 = None
                optional3 = None
                optional4 = None
                if subframes & 0x80:
                    subframes = subframes & 0x7F
                    optional1, optional2 = self._ReadAndUnpack('<2B')
                if unknown & 0x80:
                    unknown = unknown & 0x7F
                    optional3, optional4 = self._ReadAndUnpack('<2B')
                frame_data = {
                    'subframes': [],
                    'unknown': unknown,
                    'optional1': optional1,
                    'optional2': optional2,
                    'optional3': optional3,
                    'optional4': optional4
                }
                # subframes
                for k in xrange(subframes):
                    bitmap_id, unk1, subframe_id, x_off, y_off = self._ReadAndUnpack('<hBBhh')
                    subframe_data = {
                        'bitmap_id': bitmap_id,
                        'unknown': unk1,
                        'subframe_id': subframe_id,
                        'offset': Point(x=x_off, y=y_off),
                    }
                    frame_data['subframes'].append(subframe_data)
                    num_loaded_subframes = num_loaded_subframes + 1
                animation['frames'].append(frame_data)
                num_loaded_frames = num_loaded_frames + 1
            unk3, = self._ReadAndUnpack('<I')
            animation['unknown3'] = unk3
            # "appendix"
            for j in xrange(unk3):
                appendix_info = self._ReadAndUnpack('<4I')
                animation['appendix'].append(list(appendix_info))
            self.animations.append(animation)
        if len(self.animations) != num_anims:
            raise PRTLoadError('incorrect number of animations loaded (%d, expected %d)' % (num_loaded_anims, num_anims))
        if num_loaded_frames != num_frames:
            raise PRTLoadError('incorrect number of frames loaded (%d, expected %d)' % (num_loaded_frames, num_frames))
        if num_loaded_subframes != num_subframes:
            raise PRTLoadError('incorrect number of subframes loaded (%d, expected %d)' % (num_loaded_subframes, num_subframes))
        # Read any data from the end of the PRT that is left
        self.extra_data.extend(self._prt_file.read())

    def Write(self):
        self._WritePalettes()
        self._WriteBitmaps()
        # number of animations, frames, subframes, optional entries
        num_frames = 0
        num_subframes = 0
        for anim in self.animations:
            num_frames = num_frames + len(anim['frames'])
            for frame in anim['frames']:
                num_subframes = num_subframes + len(frame['subframes'])
        self._prt_file.write(struct.pack('<I', len(self.animations)))
        self._prt_file.write(struct.pack('<I', num_frames))
        self._prt_file.write(struct.pack('<I', num_subframes))
        self._prt_file.write(struct.pack('<I', self.num_optional_entries))

        # animations
        for anim in self.animations:
            bbox = anim['bounding_box']
            off = anim['offset']
            self._prt_file.write(struct.pack('<IIIIIIIII', anim['unknown1'], bbox.left, bbox.top, bbox.right, bbox.bottom, off.x, off.y, anim['unknown2'],
                    len(anim['frames'])))
            # frames
            for frame in anim['frames']:
                subframes = len(frame['subframes'])
                unknown = frame['unknown']
                opt1 = frame['optional1']
                opt2 = frame['optional2']
                opt3 = frame['optional3']
                opt4 = frame['optional4']
                if opt1 is not None or opt2 is not None:
                    subframes = subframes | 0x80
                if opt3 is not None or opt4 is not None:
                    unknown = unknown | 0x80
                self._prt_file.write(struct.pack('<BB', subframes, unknown))
                if opt1 is not None or opt2 is not None:
                    self._prt_file.write(struct.pack('<2B', int(opt1), int(opt2)))
                if opt3 is not None or opt4 is not None:
                    self._prt_file.write(struct.pack('<2B', int(opt3), int(opt4)))
                # subframes
                for sf in frame['subframes']:
                    self._prt_file.write(struct.pack('<hBBhh', sf['bitmap_id'], sf['unknown'], sf['subframe_id'], sf['offset'].x, sf['offset'].y))
            self._prt_file.write(struct.pack('<I', anim['unknown3']))
            # "appendix"
            for ap in anim['appendix']:
                # TODO: sanity check that the appendix list is 4 entries long
                self._prt_file.write(struct.pack('<4I', ap[0], ap[1], ap[2], ap[3]))
        # extra data
        self._prt_file.write(self.extra_data)
