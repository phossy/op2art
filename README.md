# art\_extractor
A program to extract Outpost 2 art files (prt and bmp) into their component files for inspection/editing.

## Installation
You need a reasonably recent version of python.  I used python 2.7.9, but I'm sure any recent version will do.
You need to install PyYAML.  Make sure it compiles libyaml, otherwise the dumping of the animation metadata will be dog-slow.

    $ pip install -r requirements.txt

## Usage
Make sure you have copies of op2\_art.prt and op2\_art.bmp.

Run art\_extractor.py:
    $ art_extractor.py <path to op2_art.prt> <path to op2_art.bmp> <directory in which you want the output files>

This will produce the following outputs in the directory specified:
- `palettes/*.pal` - palette files in Microsoft RIFF PAL format (most graphics editing software should be able to handle these). The name of the file is the
  0-indexed ID of the palette from the PRT.
- `bitmaps/*.bmp` - bitmap files in Microsoft BMP format. Again, the name of the file is the bitmap index. Most bitmaps are 8bpp (a handful of image types are
  1bpp). The color table is embedded in the bitmap file for display, but of course this will be ignored by the code that repacks the PRT (when I get around to
  that).
- `bitmaps.yml` - metadata information about the bitmaps in YAML format (currently just a mapping of ID to palette index and type)
- `animations.yml` - animation metadata. This makes up the vast majority of information in the PRT file, containing information such as bounding boxes, frame
  and subframe information, "unknown" fields such as "optional" data and "appendices", etc.

## FAQ/Caveats

- The animation metadata file also contains a `num_optional_entries` entry, since I didn't know where else to put this and it's not clear what this number
  actually represents. (it is not the number of "optional" data blocks or appendices), so we have to store it for now and reuse it when importing the data.
- Only tested on OS X 10.10, using homebrew versions of python and PyYAML, but I'm sure any OS will do if python is installed.
- Usual disclaimer, if this program crashes your computer, corrupts your OP2 installation, etc., I'm not responsible. All use is at your own risk.

## Copyright

In short: you're free to do what you want with this code, just ensure this copyright notice is included with it. Thanks!

The MIT License (MIT)

Copyright (c) 2015

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
