"""Align only the title hand cursor to each localized label's visible border.

Verified call site: StanHash/fomt b8471ae asm/intro_scene.s 0800277C,
inside the hand-only draw path (this+6C40), not the text or shared cursor API.
"""
from __future__ import annotations
from fomt_text import FormatError
from title_graphics import title_pixels

DRAW_OFFSET = 0x277C
EXPECTED_BYTES = bytes.fromhex('1a20215e68460180')
REVISION = 'visible-left-edge-v1'


def offsets():
    return {key:min(x for row in title_pixels(key) for x,color in enumerate(row) if color)
            for key in ('title.start','title.continue')}


def verify_site(rom):
    if rom[DRAW_OFFSET:DRAW_OFFSET+8] != EXPECTED_BYTES:
        raise FormatError('title cursor draw instructions mismatch')


def assemble_hook(address):
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
    delta = offsets()
    if any(not 0 <= d <= 255 for d in delta.values()):
        raise FormatError('title cursor adjustment exceeds Thumb immediate')
    # Replays the overwritten signed-X read and stack parameter write. Only
    # known title anchors move. r2/r4-r7/sp/lr remain intact; r3 is dead here.
    source = f'''
        movs r0, #0x1a
        ldrsh r1, [r4, r0]
        cmp r1, #136
        beq continue_label
        cmp r1, #24
        beq start_label
        cmp r1, #80
        bne store_x
    start_label:
        adds r1, #{delta['title.start']}
        b store_x
    continue_label:
        adds r1, #{delta['title.continue']}
    store_x:
        mov r0, sp
        strh r1, [r0]
        ldr r3, return_address
        bx r3
        .align 2
    return_address:
        .word 0x08002785
    '''
    code = bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(source,addr=address)[0])
    if len(code) > 64:
        raise FormatError('title cursor hook overflow')
    return code
