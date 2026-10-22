"""Verified title sprite localization; original asset uses Popuri Huff8/LZSS2.

Format research: StanHash/fomt b8471ae, asm/intro_scene.s,
asm/code_809E804.s (Unpack), and tools/scripts/decompress.py.
Only modes needed by this asset are supported.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from fomt_text import FormatError, p32, u32

ASSET_OFFSET = 0x747A74
ASSET_SIZE = 0x2F4C
POINTER_OFFSET = 0xCB4
DECODED_SIZE = 0x4C0C
TILE_OFFSET = 0x3D80
TILE_SIZE = 14 * 32
CONTINUE_TILE_OFFSET = 0x3F40
CONTINUE_TILE_SIZE = 20 * 32
PACKED_SHA256 = 'd00631160fde8a8d0a18ae6216f9ad9db85ed5dc5c0baa0970d7227fc496b897'
DECODED_SHA256 = '8e73d527aa1a7f905cdd1d4068bf4add642190baaff989b3a1b3be2106acd9d6'
ART_PATH = Path(__file__).resolve().parents[1]/'localization/vi/title_start.json'
CONTINUE_ART_PATH = ART_PATH.with_name('title_continue.json')
TITLE_REVISION = 'native-thin-double-outline-v5'


def native_title_mask(rom, text='Bắt đầu', width=56):
    """Native 10px capitals/7px lowercase with unexpanded one-pixel strokes.

    Unlike dialogue layout, this fixed graphic uses trimmed horizontal bearings,
    three empty columns between letters and five between the two words.
    All letters retain the native common baseline and Vietnamese accent rows.
    """
    from vietnamese_font import glyph, ascii_glyph
    ink = set()
    cursor = 0
    for word in text.split(' '):
        if cursor:
            cursor += 2
        for ch in word:
            mask = glyph(rom,ch) if ord(ch) > 127 else ascii_glyph(rom,ch)
            points = {(x,y) for y,row in enumerate(mask) for x in range(8) if row & (128 >> x)}
            left = min(x for x,y in points)
            right = max(x for x,y in points)
            points = {(cursor+x-left,y) for x,y in points}
            ink |= points
            cursor += right-left+1+3
    ink_width = max(x for x,y in ink)+1
    # A 32px OBJ canvas leaves room for stacked accents, dot below and both
    # outlines. Moving each text OBJ up 2px preserves the original ink position.
    if ink_width+4 > width:
        raise FormatError('title text and outlines exceed canvas width')
    left = (width-ink_width)//2
    ink = {(x+left,y+2) for x,y in ink}
    return [''.join('#' if (x,y) in ink else '.' for x in range(width)) for y in range(32)]


class Bits:
    def __init__(self, data):
        if len(data) % 4:
            raise FormatError('truncated Popuri word stream')
        self.data = b''.join(data[i:i+4][::-1] for i in range(0,len(data),4))
        self.pos = 0

    def read(self, count):
        if self.pos+count > len(self.data)*8:
            raise FormatError('truncated Popuri bits')
        value = 0
        for _ in range(count):
            value = value*2 + ((self.data[self.pos//8] >> (7-self.pos%8)) & 1)
            self.pos += 1
        return value


def unpack(data):
    """Decode bounded Huff8/LZSS2/no-delta or literal/no-delta streams."""
    head = u32(data,0)
    size = head >> 8
    if head & 255 != 0x70 or not 0 < size <= 0x40000:
        raise FormatError('invalid Popuri header')
    bits = Bits(data[4:])
    mode = bits.read(8)
    if mode == 4:
        return bytes(bits.read(8) for _ in range(size))
    if mode != 0x12:
        raise FormatError('unsupported Popuri mode')
    table = {}
    code = 0
    for length in range(1,17):
        code <<= 1
        count = bits.read(8)
        if code+count > 1 << length or len(table)+count > 256:
            raise FormatError('invalid Huffman tree')
        for _ in range(count):
            table[length,code] = bits.read(8)
            code += 1
    def atom():
        code = 0
        for length in range(1,17):
            code = code*2 + bits.read(1)
            if (length,code) in table:
                return table[length,code]
        raise FormatError('invalid Huffman code')
    ladder = []
    start = 1
    for _ in range(7):
        width = bits.read(4)+1
        ladder.append((start,width))
        start += 1 << width
    out = bytearray()
    while len(out) < size:
        if bits.read(1) == 0:
            out.append(atom())
            continue
        index = bits.read(3)
        count = 0
        if index == 7:
            for _ in range(8):
                digit = bits.read(4)
                count = (count << 3)+(digit >> 1)
                if digit & 1 == 0:
                    break
            else:
                raise FormatError('Popuri length overflow')
            if bits.read(1) == 0:
                if len(out)+count+1 > size:
                    raise FormatError('Popuri literal overflow')
                out.extend(atom() for _ in range(count+1))
                continue
            index = bits.read(3)
        if index >= 7:
            raise FormatError('invalid Popuri lookup')
        start,width = ladder[index]
        distance = start+bits.read(width)
        length = bits.read(4)+(count << 4)+3
        if distance > len(out) or len(out)+length > size:
            raise FormatError('invalid Popuri backreference')
        for _ in range(length):
            out.append(out[-distance])
    return bytes(out)


def pack_literal(data):
    """Game-supported mode 040 (format byte 0x04); MSB-first bytes in little-endian words."""
    if not 0 < len(data) <= 0x40000:
        raise FormatError('invalid Popuri output size')
    stream = b'\x04'+data
    stream += b'\0'*(-len(stream)%4)
    return p32((len(data)<<8)|0x70)+b''.join(stream[i:i+4][::-1] for i in range(0,len(stream),4))


def title_pixels(identifier='title.start'):
    path, width = { 'title.start':(ART_PATH,56),
                    'title.continue':(CONTINUE_ART_PATH,80)}[identifier]
    art = json.loads(path.read_text(encoding='utf-8'))
    rows = art['stroke_mask']
    if len(rows) != 32 or any(len(r) != width or set(r)-set('.#') for r in rows):
        raise FormatError(f'title art must be a {width}x32 binary stroke mask')
    ink = {(x,y) for y,r in enumerate(rows) for x,c in enumerate(r) if c == '#'}
    # Outer black -> inner white -> mint-green ink. Two actual rings; no shadow.
    halo = {(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}
    outer = {(x+dx,y+dy) for x,y in halo for dx in (-1,0,1) for dy in (-1,0,1)}
    if not ink or any(not (0 <= x < width and 0 <= y < 32) for x,y in outer):
        raise FormatError('title double outline exceeds sprite bounds')
    pixels = [[0]*width for _ in range(32)]
    for points,color in [(outer,14),(halo,13),(ink,3)]:
        for x,y in points:
            pixels[y][x] = color
    return pixels


def encode_tiles(pixels):
    """Three 1D 4bpp OBJ segments, 32px high; preserve original text widths."""
    widths = {56:(32,16,8),80:(32,32,16)}[len(pixels[0])]
    out = bytearray()
    left = 0
    for width in widths:
        for ty in range(0,len(pixels),8):
            for tx in range(0,width,8):
                for y in range(8):
                    for x in range(0,8,2):
                        out.append(pixels[ty+y][left+tx+x] | (pixels[ty+y][left+tx+x+1]<<4))
        left += width
    return bytes(out)


def expected_title_oam(original, with_save=False):
    """Expected hardware OAM delta from verified enlarged text descriptors."""
    import struct
    out = bytearray(original)
    groups = [(8,(0,0x8000,0x8000),(0x8000,0x8000,0x4000),(864,880,888))]
    if with_save:
        groups.append((11,(0,0,0x8000),(0x8000,0x8000,0x8000),(896,912,928)))
    for first,shapes,sizes,tiles in groups:
        for i in range(3):
            at = (first+i)*8
            a,b,c = struct.unpack_from('<HHH',out,at)
            a = (a & ~0xC0FF) | shapes[i] | (((a & 255)-2) & 255)
            b = (b & ~0xC000) | sizes[i]
            c = (c & ~0x03FF) | tiles[i]
            struct.pack_into('<HHH',out,at,a,b,c)
    if with_save:
        at = 14*8+4
        c = struct.unpack_from('<H',out,at)[0]
        struct.pack_into('<H',out,at,(c & ~0x03FF)|936)
    return bytes(out)


def localize(rom):
    import struct
    original = rom[ASSET_OFFSET:ASSET_OFFSET+ASSET_SIZE]
    if hashlib.sha256(original).hexdigest() != PACKED_SHA256 or u32(rom,POINTER_OFFSET) != 0x08000000+ASSET_OFFSET:
        raise FormatError('title source asset/pointer mismatch')
    decoded = unpack(original)
    if len(decoded) != DECODED_SIZE or hashlib.sha256(decoded).hexdigest() != DECODED_SHA256:
        raise FormatError('title decoded asset mismatch')
    # Original pool: logo 474 tiles; Start 14; Continue 20 + selection arrow 1;
    # copyright 60. Keep logo, arrow, copyright, palettes and animation commands.
    if u32(decoded,0x23C) != 569 or u32(decoded,0xC8) != 46:
        raise FormatError('title sprite table layout mismatch')
    start = encode_tiles(title_pixels())
    cont = encode_tiles(title_pixels('title.continue'))
    if len(start) != 28*32 or len(cont) != 40*32:
        raise FormatError('title tile allocation mismatch')
    prefix = bytearray(decoded[:0x23C])
    for frame in (1,2,3):
        struct.pack_into('<HH',prefix,0x28+frame*16+4,28,474)
    for frame in (5,6,7):
        struct.pack_into('<HH',prefix,0x28+frame*16+4,41,502)
    struct.pack_into('<HH',prefix,0x28+9*16+4,60,543)
    def object_group(first, shapes, sizes, offsets):
        for i,(shape,size,tile) in enumerate(zip(shapes,sizes,offsets)):
            at = 0xCC+(first+i)*8
            a,b,c = struct.unpack_from('<HHH',prefix,at)
            a = (a & ~0xC0FF) | shape | (((a & 255)-2) & 255)
            b = (b & ~0xC000) | size
            struct.pack_into('<HHH',prefix,at,a,b,(c & ~0x3FF)|tile)
    for first in (17,20,23):
        object_group(first,(0,0x8000,0x8000),(0x8000,0x8000,0x4000),(0,16,24))
    for first in (26,30,34):
        object_group(first,(0,0,0x8000),(0x8000,0x8000,0x8000),(0,16,32))
        struct.pack_into('<H',prefix,0xCC+(first+3)*8+4,40)
    pool = decoded[0x240:0x4960]
    updated = bytes(prefix)+p32(603)+pool[:474*32]+start+cont+pool[508*32:]+decoded[0x4960:]
    # Constructor reserves this+0x10 .. this+0x6A10 for the unpacked definition.
    if len(updated) != 20556 or len(updated) > 0x6A00:
        raise FormatError('title unpack buffer overflow')
    # Fixed OBJ allocations verified in the original live title, no free VRAM guesses.
    if 864+28 > 896 or 896+41 > 960:
        raise FormatError('title OBJ VRAM allocation overlap')
    packed = pack_literal(updated)
    if unpack(packed) != updated:
        raise FormatError('title asset round trip failed')
    labels = []
    for identifier,text,translation,width,source_at,target_at,tiles in [
        ('title.start','Start','Bắt đầu',56,TILE_OFFSET,0x240+474*32,start),
        ('title.continue','Continue','Tiếp tục',80,CONTINUE_TILE_OFFSET,0x240+502*32,cont)]:
        labels.append({'id':identifier,'original_english':text,
            'vietnamese_translation':translation,'dimensions':[width,32],
            'source_decoded_tile_offset':source_at,'decoded_tile_offset':target_at,
            'tile_bytes':len(tiles),'tiles_sha256':hashlib.sha256(tiles).hexdigest()})
    return packed, {'id':'title.prompts','source_offset':ASSET_OFFSET,
        'pointer_offset':POINTER_OFFSET,'decoded_size':len(updated),
        'tile_pool_count':603,'mode':'Popuri literal 040','revision':TITLE_REVISION,
        'palette':{'obj_bank':2,'ink_index':3,'halo_index':13,'outer_index':14,
            'ink_bgr555':'3B60','halo_bgr555':'7FFF','outer_bgr555':'0000'},
        'labels':labels,'vram':{'start':[864,891],'continue':[896,935],
            'selection_arrow':936,'copyright':[960,1019]}}
