"""Calendar heading metrics and compact copies of native year digits.

Shared date digits and the 22 native frame indices remain unchanged.
"""
from __future__ import annotations
import struct
from fomt_text import FormatError

TILE_COUNT=180
RESERVATION_SITE=0xA234A
RESERVATION_EXPECTED=bytes.fromhex('072165f702fc')
YEAR_ADVANCE=10
WORD_GAP=4
GROUP_GAP=6


def verify(rom):
    if rom[RESERVATION_SITE:RESERVATION_SITE+6]!=RESERVATION_EXPECTED:
        raise FormatError('calendar font allocation source mismatch')


def visible_bounds(pixels):
    points=[(x,y) for y,row in enumerate(pixels) for x,v in enumerate(row) if v]
    return min(x for x,y in points),max(x for x,y in points)


def layout(year,season,year_pixels,season_pixels):
    """Return frame origins; center the ink, not empty OBJ canvases."""
    label_left,label_right=visible_bounds(year_pixels)
    season_left,season_right=visible_bounds(season_pixels)
    label_width=label_right-label_left+1
    season_width=season_right-season_left+1
    number_width=len(str(year))*YEAR_ADVANCE-1
    total=label_width+WORD_GAP+number_width+GROUP_GAP+season_width
    start=(240-total)//2
    digits=start+label_width+WORD_GAP
    return (start-label_left,digits,digits+number_width+GROUP_GAP-season_left,0)


def year_digits(original,frames,encode):
    """Nearest-neighbor integer sampling of native 16x16 digits to 9x13.

    Crop transparent bearings first. No new font, antialiasing or runtime
    scaling; native foreground/shadow palette indices are copied verbatim.
    """
    result=bytearray()
    for digit in range(10):
        frame=struct.unpack_from('<8H',frames,16*digit)
        payload=original[frame[3]*32:(frame[3]+frame[2])*32]
        if len(payload)!=128:raise FormatError('native calendar digit must be 16x16')
        pixels=[[0]*16 for _ in range(16)]
        for y in range(16):
            for x in range(16):
                at=(y//8*2+x//8)*32+y%8*4+x%8//2
                pixels[y][x]=(payload[at]>>(4*(x%2)))&15
        pts=[(x,y) for y in range(16) for x in range(16) if pixels[y][x]]
        left=min(x for x,y in pts);right=max(x for x,y in pts)
        top=min(y for x,y in pts);bottom=max(y for x,y in pts)
        out=[[0]*16 for _ in range(16)]
        for y in range(13):
            sy=top+y*(bottom-top)//12
            for x in range(9):
                sx=left+x*(right-left)//8
                out[y+1][x]=pixels[sy][sx]
        result.extend(encode(out,(16,)))
    return bytes(result)


def header_hook(address,layouts):
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    asm='''
        push {r4,r5,r7,lr}
        sub sp, #32
        mov r7, r6
        ldr r0, year_field
        adds r0, r7, r0
        movs r1, #0
        ldrsh r5, [r0,r1]
        adds r5, #1
        cmp r5, #1
        bge minimum_year
        movs r5, #1
    minimum_year:
        cmp r5, #200
        ble valid_year
        movs r5, #200
    valid_year:
        movs r4, #1
        cmp r5, #10
        blo have_count
        movs r4, #2
        cmp r5, #100
        blo have_count
        movs r4, #3
    have_count:
        str r4, [sp,#20]
        ldr r0, season_field
        adds r0, r7, r0
        movs r1, #0
        ldrsh r3, [r0,r1]
        cmp r3, #3
        bls valid_season
        movs r3, #0
    valid_season:
        str r3, [sp,#24]
        movs r0, #3
        muls r3, r0
        adds r3, r3, r4
        subs r3, #1
        lsls r3, r3, #2
        adr r0, layouts
        adds r0, r0, r3
        ldrb r1, [r0]
        str r1, [sp,#8]
        ldrb r1, [r0,#1]
        str r1, [sp,#12]
        ldrb r1, [r0,#2]
        str r1, [sp,#16]
        movs r0, #0
        str r0, [sp]
        mov r0, r7
        ldr r1, [sp,#8]
        movs r2, #2
        movs r3, #10
        ldr r4, frame_function
        bl call_r4
        ldr r0, [sp,#20]
        cmp r0, #3
        bne tens
        movs r3, #0
    hundreds_loop:
        cmp r5, #100
        blo hundreds_ready
        subs r5, #100
        adds r3, #1
        b hundreds_loop
    hundreds_ready:
        mov r0, r7
        ldr r1, [sp,#12]
        movs r2, #2
        bl year_digit
        ldr r1, [sp,#12]
        adds r1, #10
        str r1, [sp,#12]
    tens:
        ldr r0, [sp,#20]
        cmp r0, #2
        blo units
        movs r3, #0
    tens_loop:
        cmp r5, #10
        blo tens_ready
        subs r5, #10
        adds r3, #1
        b tens_loop
    tens_ready:
        mov r0, r7
        ldr r1, [sp,#12]
        movs r2, #2
        bl year_digit
        ldr r1, [sp,#12]
        adds r1, #10
        str r1, [sp,#12]
    units:
        mov r0, r7
        ldr r1, [sp,#12]
        movs r2, #2
        mov r3, r5
        bl year_digit
        movs r0, #0
        str r0, [sp]
        mov r0, r7
        ldr r1, [sp,#16]
        movs r2, #2
        ldr r3, [sp,#24]
        adds r3, #11
        ldr r4, frame_function
        bl call_r4
        add sp, #32
        pop {r4,r5,r7}
        pop {r3}
        movs r4, #0
        ldr r3, resume
        bx r3
    year_digit:
        push {r4,r5,r6,lr}
        sub sp, #8
        ldr r5, tile_cache
        adds r5, r5, r0
        lsls r4, r3, #1
        adds r5, r5, r4
        ldrh r6, [r5]
        str r6, [sp,#4]
        mov r4, r6
        adds r4, #4
        strh r4, [r5]
        movs r4, #0
        str r4, [sp]
        ldr r4, frame_function
        bl call_r4
        ldr r6, [sp,#4]
        strh r6, [r5]
        add sp, #8
        pop {r4,r5,r6,pc}
    call_r4: bx r4
        .align 2
    frame_function: .word 0x080A3619
    year_field: .word 0x1E0
    season_field: .word 0x1E2
    tile_cache: .word 0x140
    resume: .word 0x080A34EF
    layouts:
    '''
    asm+='\n.byte '+','.join(str(v) for entry in layouts for v in entry)
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(asm,addr=address)[0])
