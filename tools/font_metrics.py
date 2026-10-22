#!/usr/bin/env python3
"""Export font geometry; optionally inspect a user-supplied OTF/ZIP as reference.

The optional OTF path needs fontTools; normal ROM build/test does not.
The OTF file is read only and is never used as executable setup instructions.
"""
import argparse
import hashlib
import io
import json
import unicodedata
import zipfile
from pathlib import Path
from fomt_text import VI_CHARS,verified_rom
from vietnamese_font import (ascii_glyph,glyph,BODY_Y,BASELINE,ADVANCE_PIXELS,FONT_REVISION)


def bounds(mask):
    points = [(x,y) for y,row in enumerate(mask) for x in range(8) if row & (128>>x)]
    if not points:
        return None
    return [min(x for x,y in points),min(y for x,y in points),
            max(x for x,y in points),max(y for x,y in points)]


def reference_font(path):
    from fontTools.ttLib import TTFont
    raw = path.read_bytes()
    if zipfile.is_zipfile(io.BytesIO(raw)):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = [i for i in archive.infolist() if i.filename.lower().endswith((".otf",".ttf"))]
            if len(entries) != 1 or entries[0].file_size > 16*1024*1024:
                raise ValueError("expected one font smaller than 16MiB in ZIP")
            raw = archive.read(entries[0])
    font = TTFont(io.BytesIO(raw))
    try:
        cmap = font.getBestCmap()
        names = {i:font['name'].getDebugName(i) for i in [1,13,14]}
        advances = {font['hmtx'][cmap[c]][0] for c in range(32,127)}
        return {"sha256":hashlib.sha256(raw).hexdigest(),"family":names[1],
            "license":names[13],"license_url":names[14],"cmap_characters":len(cmap),
            "vietnamese_characters_present":sum(ord(c) in cmap for c in VI_CHARS),
            "vietnamese_characters_missing":''.join(c for c in VI_CHARS if ord(c) not in cmap),
            "units_per_em":font['head'].unitsPerEm,"ascii_advance_font_units":sorted(advances),
            "ascii_advance_at_16ppem":[v*16/font['head'].unitsPerEm for v in sorted(advances)],
            "usage":"reference only; not embedded or required for ROM build"}
    finally:
        font.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom",type=Path)
    parser.add_argument("--reference-font",type=Path)
    parser.add_argument("--output",type=Path,default=Path("build/font-metrics.json"))
    args = parser.parse_args()
    rom = verified_rom(args.rom)
    report = {"font_revision":FONT_REVISION,"source_mask_rows":16,"baseline_row":BASELINE,
              "advance_pixels":ADVANCE_PIXELS,"ascii_body_offset_y":BODY_Y,
              "ascii_ink_bounds":{chr(c):bounds(ascii_glyph(rom,chr(c))) for c in range(32,127)},
              "vietnamese":[]}
    for ch in VI_CHARS:
        base = {"Đ":"D","đ":"d"}.get(ch,unicodedata.normalize('NFD',ch)[0])
        report['vietnamese'].append({"character":ch,"base":base,
            "inherited_base_bounds":bounds(ascii_glyph(rom,base)),
            "complete_glyph_bounds":bounds(glyph(rom,ch)),"advance_pixels":ADVANCE_PIXELS})
    if args.reference_font:
        report['user_reference_font'] = reference_font(args.reference_font)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['font_revision','baseline_row','advance_pixels']},ensure_ascii=False))


if __name__ == '__main__':
    main()
