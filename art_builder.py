#!/usr/bin/env python
"""Main program to recompile OP2_ART .prt and .bmp files from human-readable files."""

import os
import sys
import yaml

import bitmap
import palette
import prt_file

def main(argv):
    if len(argv) != 4:
        print 'usage: %s <directory containing input files> <new op2_art.prt> <new op2_art.bmp>' % argv[0]
        sys.exit(1)
    base_path = argv[1]
    palette_path = os.path.join(base_path, 'palettes')
    bitmap_path = os.path.join(base_path, 'bitmaps')
    with open(argv[2], 'wb') as prt:
        with open(argv[3], 'wb') as bmp:
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
                    bmp.palette_id = v['palette']
                    prt.bitmaps.append(bmp)
            print 'Loading palettes...'
            for i in xrange(num_palettes):
                pal = palette.Palette()
                pal.LoadPAL(os.path.join(palette_path, '%d.pal' % i))
                prt.palettes.append(pal)
            print 'Loading animation metadata...'
            with open(os.path.join(base_path, 'animations.yml'), 'r') as f:
                metadata = yaml.load(f.read(), Loader=yaml.CLoader)
                prt.num_optional_entries = metadata['num_optional_entries']
                del metadata['num_optional_entries']
                for k in sorted(metadata.iterkeys()):
                    prt.animations.append(metadata[k])
            print 'Writing op2_art data...'
            prt.Write()
            print 'Success!'

if __name__ == '__main__':
    main(sys.argv)
