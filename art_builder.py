#!/usr/bin/env python
"""Main program to recompile OP2_ART .prt and .bmp files from human-readable files."""

import argparse
import os
import sys
import yaml

import bitmap
import palette
import prt_file

def main():
    parser = argparse.ArgumentParser(description='Recompiles OP2_ART assets from human-readable formats.')
    parser.add_argument('input', help='Input directory to read data from.')
    parser.add_argument('prt', type=argparse.FileType('wb'), help='Path to output op2_art.prt.')
    parser.add_argument('bmp', type=argparse.FileType('wb'), help='Path to output op2_art.bmp.')
    parser.add_argument('--palette_format', default='act', choices=palette.PAL_FORMATS.keys(), help='Palette format to read.  Choices are pal (Microsoft .pal '
        'format), text (.pal text format supported by Paint Shop Pro), or act (Photoshop .act color table, default).')
    parser.add_argument('--palettes_from_bitmaps', action='store_true', default=False, help='Reads palettes directly from input bitmaps if set, ignoring the '
        'palette files and metadata.  This will result in a unique palette entry for each loaded bitmap in the PRT file, which will increase its size as well '
        'as the amount of time it takes Outpost 2 to load the data, but allowing for greater flexibility with colors.')
    args = parser.parse_args()
    base_path = args.input
    palette_path = os.path.join(base_path, 'palettes')
    bitmap_path = os.path.join(base_path, 'bitmaps')
    with args.prt as prt:
        with args.bmp as bmp:
            prt = prt_file.PRTFile(prt, bmp)
            print 'Loading bitmaps...'
            with open(os.path.join(base_path, 'bitmaps.yml'), 'r') as f:
                bmp_metadata = yaml.load(f.read(), Loader=yaml.CLoader)
                num_palettes = bmp_metadata['num_palettes']
                del bmp_metadata['num_palettes']
                for k in sorted(bmp_metadata.iterkeys()): 
                    v = bmp_metadata[k]
                    bmp = bitmap.Bitmap()
                    bmp.LoadBMP(os.path.join(bitmap_path, '%d.bmp' % int(k)))
                    bmp.image_type = v['type']
                    bmp.palette_id = k if args.palettes_from_bitmaps else v['palette']
                    prt.bitmaps.append(bmp)
            if not args.palettes_from_bitmaps:
                print 'Loading palettes...'
                pal_format = palette.PAL_FORMATS[args.palette_format]
                for i in xrange(num_palettes):
                    pal = palette.Palette()
                    pal.LoadPAL(os.path.join(palette_path, '%d.%s' % (i, pal_format[1])), file_format=pal_format[0])
                    prt.palettes.append(pal)
            else:
                for b in prt.bitmaps:
                    prt.palettes.append(b.palette)
            print 'Loading animation metadata...'
            with open(os.path.join(base_path, 'animations.yml'), 'r') as f:
                metadata = yaml.load(f.read(), Loader=yaml.CLoader)
                prt.num_optional_entries = metadata['num_optional_entries']
                del metadata['num_optional_entries']
                for k in sorted(metadata.iterkeys()):
                    prt.animations.append(metadata[k])
            print 'Loading extra data...'
            with open(os.path.join(base_path, 'extra.dat'), 'rb') as f:
                prt.extra_data.extend(f.read())
            print 'Writing op2_art data...'
            prt.Write()
            print 'Success!'

if __name__ == '__main__':
    main()
