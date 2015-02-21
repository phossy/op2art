#!/usr/bin/env python
"""Main program to decompile OP2_ART .prt and .bmp files into human-readable structures."""

import argparse
import os
import sys
import yaml

import bitmap
import palette
import prt_file

def main():
    parser = argparse.ArgumentParser(description='Decompiles OP2_ART assets into human-readable formats.')
    parser.add_argument('prt', type=argparse.FileType('rb'), help='Path to input op2_art.prt.')
    parser.add_argument('bmp', type=argparse.FileType('rb'), help='Path to input op2_art.bmp.')
    parser.add_argument('output', help='Output directory to write to.  Will be created if it doesn\'t exist.')
    parser.add_argument('--palette_format', default='act', choices=palette.PAL_FORMATS.keys(), help='Palette format to dump.  Choices are pal (Microsoft .pal '
        'format), text (.pal text format supported by Paint Shop Pro), or act (Photoshop .act color table, default).')
    args = parser.parse_args()
    with args.prt as prt:
        with args.bmp as bmp:
            prt = prt_file.PRTFile(prt, bmp)
            print 'Loading op2_art data...'
            prt.Load()
    print 'Dumping palettes...'
    base_path = args.output
    try:
        os.mkdir(base_path)
    except OSError:
        pass
    palette_path = os.path.join(base_path, 'palettes')
    bitmap_path = os.path.join(base_path, 'bitmaps')
    try:
        os.mkdir(palette_path)
    except OSError:
        pass
    pal_format = palette.PAL_FORMATS[args.palette_format]
    for i, p in enumerate(prt.palettes):
        p.WritePAL(os.path.join(palette_path, '%d.%s' % (i, pal_format[1])), file_format=pal_format[0])
    print 'Dumping bitmaps...'
    try:
        os.mkdir(bitmap_path)
    except OSError:
        pass
    bmp_metadata = {'num_palettes': len(prt.palettes)}
    for i, b in enumerate(prt.bitmaps):
        bmp_metadata[i] = {
            'type': b.image_type,
            'palette': b.palette_id
        }
        b.WriteBMP(os.path.join(bitmap_path, '%d.bmp' % i))
    print 'Dumping bitmap metadata...'
    with open(os.path.join(base_path, 'bitmaps.yml'), 'w') as f:
        f.write(yaml.dump(bmp_metadata, Dumper=yaml.CDumper))
    print 'Dumping animation metadata...'
    with open(os.path.join(base_path, 'animations.yml'), 'w') as f:
        metadata = dict(enumerate(prt.animations))
        # since we don't know where to put this at the moment...
        metadata['num_optional_entries'] = prt.num_optional_entries
        f.write(yaml.dump(metadata, Dumper=yaml.CDumper))
    print 'Dumping extra data...'
    with open(os.path.join(base_path, 'extra.dat'), 'wb') as f:
        f.write(prt.extra_data)
    print 'Success!'

if __name__ == '__main__':
    main()
