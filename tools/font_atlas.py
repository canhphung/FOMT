#!/usr/bin/env python3
"""Export the custom 1bpp font as a labeled engineering atlas, not a game screenshot."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw
from fomt_text import VI_CHARS, VI_CODES, verified_rom
from vietnamese_font import glyph, SOURCE_ROWS, FONT_REVISION, encoding_table


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom",type=Path)
    parser.add_argument("--output",type=Path,default=Path("build/vietnamese-font.png"))
    parser.add_argument("--encoding-output",type=Path,help="also export the current encoding/mask JSON")
    args = parser.parse_args()
    rom = verified_rom(args.rom)
    width,height,cols,scale = 48,70,16,3
    out = Image.new("RGB",(cols*width,32+((len(VI_CHARS)+cols-1)//cols)*height),"white")
    draw = ImageDraw.Draw(out)
    draw.text((4,5),f"{FONT_REVISION}: 134 masks, 8x{SOURCE_ROWS}, scale 3x; labels are ROM codes",fill="black")
    for i,ch in enumerate(VI_CHARS):
        x,y = i%cols*width,32+i//cols*height
        draw.rectangle((x,y,x+width-1,y+height-1),outline="#cccccc")
        draw.text((x+6,y+2),VI_CODES[ch].hex().upper(),fill="#333333")
        for row,value in enumerate(glyph(rom,ch)):
            for col in range(8):
                if value & (128>>col):
                    x0,y0 = x+12+col*scale,y+17+row*scale
                    draw.rectangle((x0,y0,x0+scale-1,y0+scale-1),fill="black")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    out.save(args.output)
    if args.encoding_output:
        args.encoding_output.parent.mkdir(parents=True,exist_ok=True)
        args.encoding_output.write_text(json.dumps(encoding_table(rom),ensure_ascii=False,indent=2)+'\n')


if __name__ == "__main__":
    main()
