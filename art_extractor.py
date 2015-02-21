#!/usr/bin/env python
"""Main program to decompile OP2_ART .prt and .bmp files into human-readable structures."""

import os
import sys
import yaml

import bitmap
import palette
import prt_file

def main(argv):
    if len(argv) != 4:
        print 'usage: %s <op2_art.prt> <op2_art.bmp> <directory to place output files>' % argv[0]
        sys.exit(1)
    with open(argv[1], 'rb') as prt:
        with open(argv[2], 'rb') as bmp:
            prt = prt_file.PRTFile(prt, bmp)
            print 'Loading op2_art data...'
            prt.Load()
    print 'Dumping palettes...'
    base_path = argv[3]
    palette_path = os.path.join(base_path, 'palettes')
    bitmap_path = os.path.join(base_path, 'bitmaps')
    try:
        os.mkdir(palette_path)
    except OSError:
        pass
    for i, p in enumerate(prt.palettes):
        p.WritePAL(os.path.join(palette_path, '%d.pal' % i))
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
    print 'Success!'

if __name__ == '__main__':
    main(sys.argv)
