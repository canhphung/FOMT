"""Baseline-aligned Latin/Vietnamese font and ARM7TDMI Thumb dispatcher.

Source masks are 8x16. At build time they become native 16x16/four-tile
4bpp staging buffers, including the game's right/down-right shadow. The
runtime only copies 128 bytes, with the original advance of one 8px cell.
"""
from __future__ import annotations

import struct
import unicodedata
from fomt_text import FONT_1BPP, FONT_LOOKUP, FormatError, VI_CHARS, VI_CODES

SOURCE_ROWS = 16
ADVANCE_PIXELS = 8
BASELINE = 13
BODY_Y = 4
ASCII_FIRST = 0x20
ASCII_LAST = 0x7E
ASCII_COUNT = ASCII_LAST - ASCII_FIRST + 1
STAGING_BYTES = 128
FONT_REVISION = "native-outline-aligned-v2"


def original_glyph(rom: bytes, character: str) -> bytes:
    """The exact original 8x12 mask, with its native horizontal bearings."""
    code = ord(character)
    if not ASCII_FIRST <= code <= ASCII_LAST:
        raise FormatError("original_glyph requires a printable ASCII character")
    index = struct.unpack_from("<h", rom, FONT_LOOKUP + 2*code)[0]
    if index < 0:
        raise FormatError(f"missing original glyph for {character!r}")
    start = FONT_1BPP + 12*index
    return rom[start:start+12]


def ascii_glyph(rom: bytes, character: str) -> bytes:
    # Same 2px shift for every ASCII character relative to the original staging
    # output. Never trim, resample, recenter or replace the native outlines.
    return bytes(BODY_Y) + original_glyph(rom, character)


def glyph(rom: bytes, character: str) -> bytes:
    if character not in VI_CHARS:
        raise FormatError(f"not a supported Vietnamese character: {character!r}")
    if character in "Đđ":
        base = "D" if character == "Đ" else "d"
        marks = ""
    else:
        nfd = unicodedata.normalize("NFD", character)
        base, marks = nfd[0], nfd[1:]
    rows = bytearray(ascii_glyph(rom, base))
    upper = base.isupper()
    has_shape = "\u0302" in marks or "\u0306" in marks
    above_tone = next((m for m in marks if m in "\u0300\u0301\u0309\u0303"), None)

    # A top tone replaces i's dot; dot-below (ị) retains the original upper dot.
    if base == "i" and above_tone:
        rows[BODY_Y+1] = 0
    if character == "Đ":
        rows[BODY_Y+5] |= 0xF0
    elif character == "đ":
        rows[BODY_Y+2] |= 0x1E

    shape_y = (2 if above_tone else 1) if upper else 4
    if "\u0302" in marks:
        rows[shape_y] |= 0x10
        rows[shape_y+1] |= 0x28
    elif "\u0306" in marks:
        rows[shape_y] |= 0x28
        rows[shape_y+1] |= 0x10
    elif "\u031b" in marks:
        top = BODY_Y if upper else BODY_Y+3
        rows[top-2] |= 0x02
        rows[top-1] |= 0x06
        rows[top] |= 0x04

    tone_y = (0 if has_shape else 1) if upper else (1 if has_shape else 4)
    tones = {"\u0301": (0x08,0x10), "\u0300": (0x20,0x10),
             "\u0309": (0x18,0x08), "\u0303": (0x28,0x50)}
    if above_tone:
        a,b = tones[above_tone]
        rows[tone_y] |= a
        rows[tone_y+1] |= b
    if "\u0323" in marks:
        rows[BASELINE+2] |= 0x10
    return bytes(rows)


def render_staging(mask: bytes) -> bytes:
    """Match native shadow and tile order; clip shadow below the 16px cell."""
    if len(mask) != SOURCE_ROWS:
        raise FormatError("font mask must have exactly 16 rows")
    pixels = [[0]*16 for _ in range(16)]
    foreground = {(x+1,y) for y,row in enumerate(mask)
                  for x in range(8) if row & (128>>x)}
    for x,y in foreground:
        pixels[y][x+1] = 2
        if y+1 < 16:
            pixels[y+1][x+1] = 2
    for x,y in foreground:
        pixels[y][x] = 1
    out = bytearray(STAGING_BYTES)
    for y in range(16):
        for x in range(16):
            offset = (y//8*2+x//8)*32 + y%8*4 + x%8//2
            out[offset] |= pixels[y][x] << (x%2*4)
    return bytes(out)


def build_glyphs(rom: bytes) -> bytes:
    ascii_masks = (ascii_glyph(rom, chr(code)) for code in range(ASCII_FIRST,ASCII_LAST+1))
    vi_masks = (glyph(rom,c) for c in VI_CHARS)
    return b"".join(render_staging(mask) for masks in (ascii_masks,vi_masks) for mask in masks)


def encoding_table(rom: bytes) -> dict:
    return {"encoding":"FOMT-VI-EB-v1","normalization":"NFC","lead_byte":"EB",
            "font_revision":FONT_REVISION,"glyph_advance_pixels":ADVANCE_PIXELS,
            "glyph_rows":SOURCE_ROWS,"baseline_row":BASELINE,"ascii_glyphs":ASCII_COUNT,
            "glyph_storage":"source mask: 1bpp MSB-left; ROM cache: 16x16 4bpp, 128 bytes",
            "cache_stride_bytes":STAGING_BYTES,
            "characters":[{"character":ch,"code":VI_CODES[ch].hex().upper(),
                           "bitmap_hex":glyph(rom,ch).hex()} for ch in VI_CHARS]}


def assemble_hook(address: int, glyph_address: int) -> bytes:
    try:
        from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_LITTLE_ENDIAN
    except ImportError as exc:
        raise FormatError("Install keystone-engine==0.9.2 to assemble the font hook") from exc
    source = f"""
        cmp r1, #{ASCII_FIRST}
        blo original
        cmp r1, #{ASCII_LAST}
        bhi vietnamese
        mov r3, r1
        subs r3, #{ASCII_FIRST}
        b render
    vietnamese:
        lsrs r3, r1, #8
        cmp r3, #0xEB
        bne original
        movs r3, #0xFF
        ands r3, r1
        subs r3, #0x40
        cmp r3, #{len(VI_CHARS)-1}
        bhi original
        adds r3, #{ASCII_COUNT}
    render:
        cmp r0, #0
        beq width_only
        lsls r3, r3, #7
        ldr r2, glyph_pointer
        adds r1, r2, r3
        push {{r4, r5, r6, r7}}
        movs r2, #8
    copy:
        ldmia r1!, {{r4, r5, r6, r7}}
        stmia r0!, {{r4, r5, r6, r7}}
        subs r2, #1
        bne copy
        pop {{r4, r5, r6, r7}}
    width_only:
        movs r0, #1
        bx lr
    original:
        push {{r4, r5, r6, lr}}
        adds r4, r0, #0
        adds r2, r1, #0
        movs r6, #0
        ldr r3, resume_pointer
        bx r3
        .balign 4
    glyph_pointer: .word {glyph_address}
    resume_pointer: .word 0x080D0D31
    """
    assembler = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_LITTLE_ENDIAN)
    machine, _ = assembler.asm(source, addr=address)
    if machine is None:
        raise FormatError("font hook assembly failed")
    return bytes(machine)


def trampoline(destination: int) -> bytes:
    return b"\x00\x4B\x18\x47" + struct.pack("<I", destination | 1)
