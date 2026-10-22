"""Build compact 8x12 1bpp Vietnamese glyphs and an ARM7TDMI Thumb hook."""
from __future__ import annotations

import struct
import unicodedata
from fomt_text import FONT_1BPP, FONT_LOOKUP, FormatError, VI_CHARS

# Seven-row pixel forms for capitals; lower-case bodies retain the game's font.
# Five active columns (six for capital O) leave room for horn/shadow rendering.
CAPITALS = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "O": (30, 33, 33, 33, 33, 33, 30),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "D": (30, 17, 17, 17, 17, 17, 30),
}


def glyph(rom: bytes, character: str) -> bytes:
    if character in "Đđ":
        base = character.replace("Đ", "D").replace("đ", "d")
        marks = ""
    else:
        nfd = unicodedata.normalize("NFD", character)
        base, marks = nfd[0], nfd[1:]
    if base.isupper():
        body = [row << 2 for row in CAPITALS[base]]
    else:
        index = struct.unpack_from("<h", rom, FONT_LOOKUP + 2*ord(base))[0]
        original = rom[FONT_1BPP+12*index:FONT_1BPP+12*(index+1)]
        body = list(original[3:10])
        if base == "d":
            # d ascender is above the ordinary lower-case seven-row body.
            body = [0x04, 0x04, 0x3C, 0x44, 0x44, 0x44, 0x3C]
        if base == "i":
            body[0] = 0  # remove the dot when a tone occupies that position
        if base == "y":
            body = [0x44, 0x44, 0x44, 0x3C, 0x04, 0x44, 0x38]
    rows = [0]*4 + body + [0]
    if character == "Đ":
        rows[7] |= 0x7C
    elif character == "đ":
        rows[5] |= 0x1C
    if "\u0302" in marks:  # circumflex
        rows[2], rows[3] = 0x10, 0x28
    elif "\u0306" in marks:  # breve
        rows[2], rows[3] = 0x28, 0x10
    elif "\u031b" in marks:  # horn, outside the right stem
        rows[3] |= 0x02
        rows[4] |= 0x06
    if "\u0301" in marks:
        rows[0], rows[1] = 0x08, 0x10
    elif "\u0300" in marks:
        rows[0], rows[1] = 0x20, 0x10
    elif "\u0309" in marks:
        rows[0], rows[1] = 0x18, 0x08
    elif "\u0303" in marks:
        rows[0], rows[1] = 0x28, 0x50
    elif "\u0323" in marks:
        rows[11] = 0x10
    return bytes(rows)


def build_glyphs(rom: bytes) -> bytes:
    return b"".join(glyph(rom, c) for c in VI_CHARS)


def assemble_hook(address: int, glyph_address: int) -> bytes:
    try:
        from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB, KS_MODE_LITTLE_ENDIAN
    except ImportError as exc:
        raise FormatError("Install keystone-engine==0.9.2 to assemble the font hook") from exc
    source = f"""
        lsrs r3, r1, #8
        cmp r3, #0xEB
        bne original
        movs r3, #0xFF
        ands r3, r1
        subs r3, #0x40
        cmp r3, #{len(VI_CHARS)-1}
        bhi original
        push {{r4, lr}}
        mov r4, r0
        cmp r4, #0
        beq width_only
        movs r0, #12
        muls r0, r3
        ldr r2, glyph_pointer
        adds r0, r0, r2
        mov r1, r4
        ldr r3, unpack_pointer
        bl call_r3
    width_only:
        movs r0, #1
        pop {{r4}}
        pop {{r3}}
        bx r3
    original:
        push {{r4, r5, r6, lr}}
        adds r4, r0, #0
        adds r2, r1, #0
        movs r6, #0
        ldr r3, resume_pointer
        bx r3
    call_r3:
        bx r3
        .balign 4
    glyph_pointer: .word {glyph_address}
    unpack_pointer: .word 0x0300085C
    resume_pointer: .word 0x080D0D31
    """
    # Only v4T instructions above; BLX and wide Thumb-2 instructions are forbidden.
    assembler = Ks(KS_ARCH_ARM, KS_MODE_THUMB | KS_MODE_LITTLE_ENDIAN)
    machine, _ = assembler.asm(source, addr=address)
    if machine is None:
        raise FormatError("font hook assembly failed")
    return bytes(machine)


def trampoline(destination: int) -> bytes:
    # ldr r3,[pc,#0]; bx r3; .word destination|1 (function is 4-byte aligned)
    return b"\x00\x4B\x18\x47" + struct.pack("<I", destination | 1)
