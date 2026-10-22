"""Verified USA new-game UI literals and the birthday OBJ glyph atlas.

Reference b8471ae: asm/new_game.s; asm/code_0803EE94.s 0806E234;
src/code_0800E2E4.cc (four fixed seven-byte season-name rows).
"""
from __future__ import annotations
import struct
import unicodedata
from fomt_text import FormatError, ROM_BASE, cstring, make_record, u32

# ID suffix, source C string, verified literal slots, visible-cell budget.
POINTERS = (
 ('name.player',0xE8934,(0x4EE8,),10),
 ('name.farm',0xE893C,(0x4EEC,),10),
 ('name.pet',0xE8944,(0x4EF0,),10),
 ('name.label',0xE8BF4,(0x5F18,),6),
 ('name.end',0xE8BFC,(0x66F4,),27),
 ('name.end.wide',0xE8C14,(0x6710,0x6770),27),
 ('name.confirm',0xE8C2C,(0x7028,),28),
 ('name.yes',0xE8C44,(0x702C,),12),
 ('name.no',0xE8C48,(0x7030,),12),
 ('summary.player',0xE8958,(0x54B8,),14),
 ('summary.birthday',0xE8968,(0x54BC,),14),
 ('summary.farm',0xE8978,(0x54C0,),14),
 ('summary.pet',0xE8988,(0x54C4,),14),
 ('summary.confirm',0xE8998,(0x5904,),28),
 ('summary.yes',0xE89A4,(0x5908,),12),
 ('summary.no',0xE89A8,(0x590C,),12),
 ('birthday.confirm',0xFBD18,(0x6DEB4,),28),
 ('birthday.yes',0xFBD28,(0x6DEB8,),12),
 ('birthday.no',0xFBD2C,(0x6DEBC,),12),
)
SEASONS = ('spring','summer','fall','winter')
SEASON_TABLE = 0xF04EE
GLYPH_TABLE = 0xFBD30
GLYPH_TEXT = '0123456789SpringSummerFall  Winter_Birthday'
ATLAS_SITE = 0x6E3BC
ATLAS_EXPECTED = bytes.fromhex('0091002101910297')
SUMMARY_BLANK_SITE = 0x5702
SUMMARY_BLANK_EXPECTED = bytes.fromhex('6421')
# Summary label pool starts at tile 96. Column 13 of its first row is
# reserved blank; original column 4 (tile 100) is ink in "Tên bạn".
SUMMARY_BLANK_TILE = 96+13
PREFIX = 'ui.newgame.'


def extract_records(rom):
    rows = []
    for suffix,address,slots,columns in POINTERS:
        if any(u32(rom,slot) != ROM_BASE+address for slot in slots):
            raise FormatError('new-game literal pointer mismatch')
        row = make_record(PREFIX+suffix,cstring(rom,address,address+128),address,
            'new_game_'+suffix.replace('.','_'),{'kind':'pointer','pointer_offsets':list(slots),
            'reference':'StanHash/fomt b8471ae asm/new_game.s; birthday confirm: asm/code_0803EE94.s 0806DE84'},columns)
        # func_08050664 rejects prompts/options by strlen before rendering.
        if suffix.endswith('.confirm'):
            row['max_encoded_bytes'] = 28
        elif suffix.endswith(('.yes','.no')):
            row['max_encoded_bytes'] = 26  # two-choice layout
        rows.append(row)
    if u32(rom,0xE300) != ROM_BASE+SEASON_TABLE:
        raise FormatError('season lookup table pointer mismatch')
    for i,key in enumerate(SEASONS):
        at = SEASON_TABLE+i*7
        rows.append(make_record(PREFIX+'season.'+key,cstring(rom,at,at+7),at,
            'season_name_shared_with_new_game',{'kind':'fixed_cstring','offset':at,'size':7,
            'reference':'src/code_0800E2E4.cc func_0800E2E4; fixed char[4][7]'},6))
    source = rom[GLYPH_TABLE:GLYPH_TABLE+86]
    if struct.unpack('<43H',source) != tuple(map(ord,GLYPH_TEXT)) or rom[ATLAS_SITE:ATLAS_SITE+8] != ATLAS_EXPECTED or u32(rom,0x6E434) != ROM_BASE+GLYPH_TABLE:
        raise FormatError('birthday glyph atlas source mismatch')
    at = GLYPH_TABLE+35*2
    row = make_record(PREFIX+'birthday.title',b'Birthday',at,'new_game_birthday_glyph_strip',
        {'kind':'glyph_strip','glyph_table_offset':GLYPH_TABLE,'first':35,'count':8,
         'raw_format':'u16le_glyphs','reference':'asm/code_0803EE94.s func_0806E234/0806E578; eight title OBJ cells'},9)
    row['original_bytes'] = rom[at:at+16].hex()
    rows.append(row)
    return rows


def strip(rom,text,width,advance=8):
    from vietnamese_font import ascii_glyph,glyph
    points = set()
    for i,ch in enumerate(unicodedata.normalize('NFC',text)):
        mask = ascii_glyph(rom,ch) if ord(ch) < 127 else glyph(rom,ch)
        for y,row in enumerate(mask):
            for x in range(8):
                if row & (128 >> x):
                    points.add((i*advance+x+1,y))
    if any(not (0 <= x < width and 0 <= y < 16) for x,y in points):
        raise FormatError('birthday strip foreground overflow')
    pixels = [[0]*width for _ in range(16)]
    for x,y in points:
        for dx,dy in ((1,0),(1,1)):
            if x+dx < width and y+dy < 16:
                pixels[y+dy][x+dx] = 2
    for x,y in points:pixels[y][x] = 1
    # Each OBJ glyph occupies two vertically stacked 8x8 tiles = 64 bytes.
    out = bytearray()
    for cell in range(width//8):
        for ty in (0,8):
            for y in range(8):
                for x in range(0,8,2):
                    out.append(pixels[ty+y][cell*8+x] | (pixels[ty+y][cell*8+x+1]<<4))
    return bytes(out)


def build_atlas(rom,texts):
    extract_records(rom)  # verify every source before generating cache
    texts = {key:unicodedata.normalize('NFC',text) for key,text in texts.items()}
    result = b''.join(strip(rom,str(i),8) for i in range(10))
    originals = ('Spring','Summer','Fall  ','Winter')
    for key,original in zip(SEASONS,originals):
        text = texts.get(PREFIX+'season.'+key,original)
        if len(text) > 6:raise FormatError('birthday season label exceeds six cells')
        result += strip(rom,text.ljust(6),48)
    result += strip(rom,'_',8)
    text = texts.get(PREFIX+'birthday.title','Birthday')
    result += strip(rom,text,64,advance=7 if len(text)>8 else 8)
    if len(result) != 43*64:raise FormatError('birthday atlas size mismatch')
    return result


def summary_blank_patch(rom, texts):
    if rom[SUMMARY_BLANK_SITE:SUMMARY_BLANK_SITE+2] != SUMMARY_BLANK_EXPECTED:
        raise FormatError('summary background tile instruction mismatch')
    text = texts.get(PREFIX+'summary.player', 'Your name     ')
    if len(unicodedata.normalize('NFC', text).rstrip(' ')) > 13 or '{' in text:
        raise FormatError('summary.player must leave column 13 blank for background tile')
    return struct.pack('<H', 0x2100 | SUMMARY_BLANK_TILE)  # movs r1,#109


def atlas_hook(address,cache_address):
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    asm = f'''
        mov r0, r8
        lsls r1, r5, #6
        ldr r2, cache
        adds r1, r1, r2
        movs r2, #16
    copy:
        ldr r3, [r1]
        str r3, [r0]
        adds r1, #4
        adds r0, #4
        subs r2, #1
        bne copy
        ldr r3, resume
        bx r3
        .align 2
    cache: .word {cache_address}
    resume: .word 0x0806E3CF
    '''
    code = bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(asm,addr=address)[0])
    if len(code)>64:raise FormatError('birthday atlas hook too large')
    return code
