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
PACKED_SHA256 = 'd00631160fde8a8d0a18ae6216f9ad9db85ed5dc5c0baa0970d7227fc496b897'
DECODED_SHA256 = '8e73d527aa1a7f905cdd1d4068bf4add642190baaff989b3a1b3be2106acd9d6'
ART_PATH = Path(__file__).resolve().parents[1]/'localization/vi/title_start.json'
TITLE_REVISION = 'native-thin-ink-v3'


def native_title_mask(rom):
    """Native 10px capitals/7px lowercase with unexpanded one-pixel strokes.

    Unlike dialogue layout, this fixed graphic uses trimmed horizontal bearings,
    three empty columns between letters and five between the two words.
    All letters retain the native common baseline and Vietnamese accent rows.
    """
    from vietnamese_font import glyph, ascii_glyph
    ink = set()
    cursor = 0
    for word in ('Bắt', 'đầu'):
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
    width = max(x for x,y in ink)+1
    left = (56-width)//2
    ink = {(x+left,y) for x,y in ink}
    return [''.join('#' if (x,y) in ink else '.' for x in range(56)) for y in range(16)]


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


def title_pixels():
    art = json.loads(ART_PATH.read_text(encoding='utf-8'))
    rows = art['stroke_mask']
    if len(rows) != 16 or any(len(r) != 56 or set(r)-set('.#') for r in rows):
        raise FormatError('title art must be a 56x16 binary stroke mask')
    ink = {(x,y) for y,r in enumerate(rows) for x,c in enumerate(r) if c == '#'}
    # The reference uses slender dark strokes on white. A single light halo
    # preserves that appearance against the title characters without a shadow.
    halo = {(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}
    if any(not (0 <= x < 56 and 0 <= y < 16) for x,y in halo):
        raise FormatError('title halo exceeds sprite bounds')
    pixels = [[0]*56 for _ in range(16)]
    for points,color in [(halo,13),(ink,14)]:
        for x,y in points:
            pixels[y][x] = color
    return pixels


def encode_tiles(pixels):
    """Three original 1D OBJ segments: 32x16, 16x16, 8x16, 4bpp."""
    out = bytearray()
    left = 0
    for width in (32,16,8):
        for ty in (0,8):
            for tx in range(0,width,8):
                for y in range(8):
                    for x in range(0,8,2):
                        out.append(pixels[ty+y][left+tx+x] | (pixels[ty+y][left+tx+x+1]<<4))
        left += width
    return bytes(out)


def localize(rom):
    original = rom[ASSET_OFFSET:ASSET_OFFSET+ASSET_SIZE]
    if hashlib.sha256(original).hexdigest() != PACKED_SHA256 or u32(rom,POINTER_OFFSET) != 0x08000000+ASSET_OFFSET:
        raise FormatError('title source asset/pointer mismatch')
    decoded = unpack(original)
    if len(decoded) != DECODED_SIZE or hashlib.sha256(decoded).hexdigest() != DECODED_SHA256:
        raise FormatError('title decoded asset mismatch')
    tiles = encode_tiles(title_pixels())
    if len(tiles) != TILE_SIZE:
        raise FormatError('title tile size changed')
    updated = decoded[:TILE_OFFSET]+tiles+decoded[TILE_OFFSET+TILE_SIZE:]
    packed = pack_literal(updated)
    if unpack(packed) != updated:
        raise FormatError('title asset round trip failed')
    return packed, {'id':'title.start', 'original_english':'Start',
        'vietnamese_translation':'Bắt đầu','source_offset':ASSET_OFFSET,
        'pointer_offset':POINTER_OFFSET,'decoded_tile_offset':TILE_OFFSET,
        'tile_bytes':TILE_SIZE,'dimensions':[56,16], 'mode':'Popuri literal 040',
        'revision':TITLE_REVISION,
        'tiles_sha256':hashlib.sha256(tiles).hexdigest()}
