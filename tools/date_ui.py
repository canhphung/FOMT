"""Verified A4NE rev 0 HUD date/time renderer (reference b8471ae 0803CD4C).

Keeps the original two 32x16 OBJ buffers, update flags, placement and weather.
Only display functions are redirected; the game's packed date/time is read-only.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from fomt_text import FormatError, ROM_BASE

HUD_SITES = {'initial':0x3CD4C,'season':0x3D080,'day':0x3D0F0,
             'hour':0x3D240,'blink':0x3D2E8,'minute':0x3D340}
HUD_EXPECTED = {
 'initial':'f0b557464e464546','season':'f0b582b007680129',
 'day':'f0b588b00c1c161c','hour':'f0b588b00d1c0668',
 'blink':'10b588b009060468','minute':'f0b5474680b40d1c',
}
DIGITS = 0x75A440
PROFILE = json.loads((Path(__file__).resolve().parents[1]/'localization/vi/date_ui.json').read_text())
SEASONS = tuple(PROFILE['seasons'])
WEEKDAYS = tuple(PROFILE['weekdays'])
if len(SEASONS)!=4 or len(WEEKDAYS)!=7:raise FormatError('date UI requires four seasons and seven weekdays')
REVISION = 'vietnamese-date-24h-spacing-v2'

# Four/five-pixel bodies, seven rows plus bottom dot. No UTF-8 in the ROM.
TINY = {
 'X':['1001','1001','0110','1001','1001'],
 'H':['1001','1001','1111','1001','1001'],
 'T':['1111','0100','0100','0100','0100'],
 'C':['0111','1000','1000','1000','0111'],
 'N':['1001','1101','1011','1001','1001'],
 'Đ':['1110','1001','1101','1001','1110'],
 'u':['000','101','101','101','111'],
 'n':['000','110','101','101','101'],
 'a':['000','011','101','101','011'],
 'o':['000','010','101','101','010'],
 'g':['000','011','101','011','001'],
 'h':['100','100','110','101','101'],
 '0':['010','101','101','101','010'],
 '1':['010','110','010','010','111'],
 '8':['010','101','010','101','010'],
 '9':['010','101','011','001','110'],
 '2':['110','001','010','100','111'],
 '3':['110','001','010','001','110'],
 '4':['101','101','111','001','001'],
 '5':['111','100','110','001','110'],
 '6':['011','100','110','101','010'],
 '7':['111','001','010','010','010'],
}


DIGITS_SHA256 = 'ad1d30345396b72746582a6140ac4dd5911332400733e33634b49d4039bedfe2'
CALENDAR_SHA256 = '3c47dd074560851632fbf494299b6fd99557d62111d576a42f2dff8a1d1078c8'

def verify(rom):
    if hashlib.sha256(rom[DIGITS:DIGITS+11*32]).hexdigest()!=DIGITS_SHA256:
        raise FormatError('HUD native numeral tiles mismatch')
    for key,at in HUD_SITES.items():
        if rom[at:at+8].hex()!=HUD_EXPECTED[key]:raise FormatError('HUD instruction mismatch: '+key)


def tiny_pixels(text,width):
    import unicodedata
    ink = set();cursor=0
    for char in text:
        if char==' ':cursor+=3;continue
        if char=='·':ink.add((cursor,4));cursor+=2;continue
        nfd=unicodedata.normalize('NFD',char);base=nfd[0];shape=TINY.get(base)
        if shape is None:raise FormatError('unknown tiny glyph '+char)
        for y,row in enumerate(shape):
            for x,bit in enumerate(row):
                if bit=='1':ink.add((cursor+x,y+2))
        if '\u0302' in nfd:ink.update(((cursor,1),(cursor+1,0),(cursor+2,1)))
        if '\u0323' in nfd:ink.add((cursor+1,7))
        cursor+=len(shape[0])+1
    if any(x>=width or y>=8 for x,y in ink):raise FormatError('tiny HUD text overflows')
    # Same foreground/shadow indices as original HUD glyphs; avoid a shadow
    # below the bottom dot and beyond the original eight-pixel row.
    pixels=[[0]*width for _ in range(8)]
    for x,y in ink:
        if x+1<width and y+1<8:pixels[y+1][x+1]=2
    for x,y in ink:pixels[y][x]=1
    return pixels


def tiles(pixels):
    out=bytearray();width=len(pixels[0])
    for tx in range(0,width,8):
        for y in range(8):
            for x in range(0,8,2):out.append(pixels[y][tx+x]|pixels[y][tx+x+1]<<4)
    return bytes(out)


def season_pixels(season):
    """Right-align actual ink (including its shadow) in the 24px season area."""
    pixels=tiny_pixels(season,24)
    right=max(x for row in pixels for x,value in enumerate(row) if value)
    shift=23-right
    return [[0]*shift+row[:24-shift] for row in pixels]


def day_week_pixels(day,weekday):
    # Three blank columns after the season, and between date/marker/weekday.
    # Render the complete suffix so one-digit dates leave no empty numeral tile.
    return [[0]*3+row for row in tiny_pixels(f'{day} · {weekday}',37)]


def build_hud_cache(rom):
    verify(rom)
    digit=lambda n:rom[DIGITS+n*32:DIGITS+(n+1)*32]
    groups={
        'season':b''.join(tiles(season_pixels(s)) for s in SEASONS),
        'day_week':b''.join(tiles(day_week_pixels(n,w)) for n in range(1,31) for w in WEEKDAYS),
        'hour':b''.join(digit(n//10)+digit(n%10)+digit(10) for n in range(24)),
        'minute':b''.join(digit(n//10)+digit(n%10) for n in range(60)),
        'blink':bytes(32)+digit(10),
    }
    return groups


def assemble_hud(address,cache):
    """Pure display setters; buffer P is reached through the native handle [r0]."""
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB);blob=bytearray();entries={}
    def emit(key,body):
        while len(blob)%4:blob.append(0)
        at=address+len(blob);entries[key]=at
        blob.extend(bytes(ks.asm(body,addr=at)[0]))
    flags='''
        movs r0, #1
        ldr r1, flag_one
        strb r0, [r4,r1]
        ldr r1, flag_two
        strb r0, [r4,r1]
        pop {r4,r5,r6,r7,pc}
        .align 2
    flag_one: .word 0x18C
    flag_two: .word 0x2B0
    '''
    def copy(offset,count,label):
        return f'''
        ldr r0, dest_{label}
        adds r0, r4, r0
        movs r2, #{count//4}
    copy_{label}:
        ldr r3, [r1]
        str r3, [r0]
        adds r1, #4
        adds r0, #4
        subs r2, #1
        bne copy_{label}
        b after_{label}
        .align 2
    dest_{label}: .word {offset}
    after_{label}:
        '''
    emit('season',f'''
        push {{r4,r5,r6,r7,lr}}
        ldr r4, [r0]
        cmp r1, #3
        bls valid
        movs r1, #0
    valid:
        movs r2, #96
        muls r1, r2
        ldr r2, cache
        adds r1, r1, r2
    '''+copy(0x84,96,'season')+flags+f'\ncache: .word {cache["season"]}\n')
    emit('day',f'''
        push {{r4,r5,r6,r7,lr}}
        ldr r4, [r0]
        mov r5, r2
        cmp r1, #1
        bhs valid_low
        movs r1, #1
    valid_low:
        cmp r1, #30
        bls valid_high
        movs r1, #30
    valid_high:
        subs r1, #1
        movs r2, #7
        muls r1, r2
        cmp r5, #6
        bls valid_week
        movs r5, #0
    valid_week:
        adds r1, r1, r5
        movs r2, #160
        muls r1, r2
        ldr r2, days
        adds r1, r1, r2
    '''+copy(0xE4,32,'day_left')+copy(0x1A8,128,'day_right')+flags+f'\ndays: .word {cache["day_week"]}\n')
    for key,maximum,stride,destination in [('hour',23,96,0x124),('minute',59,64,0x228),('blink',1,32,0x164)]:
        clamp=('subs r1, #24' if key=='hour' else 'movs r1, #0')
        emit(key,f'''
        push {{r4,r5,r6,r7,lr}}
        ldr r4, [r0]
        cmp r1, #{maximum}
        bls valid
        {clamp}
    valid:
        movs r2, #{stride}
        muls r1, r2
        ldr r2, cache
        adds r1, r1, r2
        '''+copy(destination,stride,key)+flags+f'\ncache: .word {cache[key]}\n')
    emit('initial',f'''
        push {{r4,r5,r6,r7,lr}}
        mov r4, r0
        mov r5, r1
        mov r6, r2
        ldr r7, [r0]
        adds r0, r7, #0
        adds r0, #0x84
        movs r1, #0
        movs r2, #64
    clear_left:
        str r1, [r0]
        adds r0, #4
        subs r2, #1
        bne clear_left
        ldr r0, right_offset
        adds r0, r0, r7
        movs r2, #64
    clear_right:
        str r1, [r0]
        adds r0, #4
        subs r2, #1
        bne clear_right
        ldrb r1, [r5,#1]
        movs r2, #3
        ands r1, r2
        mov r0, r4
        ldr r3, season_function
        bl call_r3
        ldrb r1, [r5]
        movs r2, #7
        ands r1, r2
        adds r1, #6
        movs r2, #120
        muls r1, r2
        ldrb r0, [r5,#1]
        movs r2, #3
        ands r0, r2
        movs r2, #30
        muls r0, r2
        adds r1, r1, r0
        ldrb r0, [r5,#1]
        lsrs r0, r0, #2
        movs r2, #31
        ands r0, r2
        adds r1, r1, r0
    modulo_week:
        cmp r1, #7
        blo have_week
        subs r1, #7
        b modulo_week
    have_week:
        mov r2, r1
        adds r1, r0, #1
        mov r0, r4
        ldr r3, day_function
        bl call_r3
        ldrh r1, [r5,#2]
        movs r2, #31
        ands r1, r2
        mov r0, r4
        ldr r3, hour_function
        bl call_r3
        ldrh r1, [r5,#2]
        lsrs r1, r1, #5
        movs r2, #63
        ands r1, r2
        mov r0, r4
        ldr r3, minute_function
        bl call_r3
        mov r0, r4
        mov r1, r6
        ldr r3, blink_function
        bl call_r3
        pop {{r4,r5,r6,r7,pc}}
    call_r3: bx r3
        .align 2
    right_offset: .word 0x1A8
    season_function: .word {entries['season']|1}
    day_function: .word {entries['day']|1}
    hour_function: .word {entries['hour']|1}
    minute_function: .word {entries['minute']|1}
    blink_function: .word {entries['blink']|1}
    ''')
    return bytes(blob),entries

CALENDAR_ASSET = 0x74F34C
CALENDAR_ASSET_SIZE = 0x1394
CALENDAR_POINTER = 0xA2460
CALENDAR_HEADER_SITE = 0xA34B4
CALENDAR_HEADER_EXPECTED = bytes.fromhex('1b14032000900024')
CALENDAR_WEEK_X_SITE = 0xA34EE


def calendar_pixels(rom,text,width):
    """Native 10px letter bodies at compact six-pixel advance, full accents."""
    from vietnamese_font import ascii_glyph,glyph
    ink=set();cursor=0
    for char in text:
        if char==' ':cursor+=1;continue
        if char=='—':
            ink.update((cursor+x,9) for x in range(3));cursor+=3;continue
        mask=ascii_glyph(rom,char) if ord(char)<128 else glyph(rom,char)
        points={(x,y) for y,row in enumerate(mask) for x in range(8) if row&(128>>x)}
        left=min(x for x,y in points)
        ink.update((cursor+x-left,y) for x,y in points)
        cursor+=max(x for x,y in points)-left+2
    if any(x>=width or y>=16 for x,y in ink):raise FormatError('calendar text exceeds original OBJ canvas: '+text)
    # Center short labels within their existing canvas; season headings fill it.
    used=max(x for x,y in ink)+1;offset=(width-used)//2
    ink={(x+offset,y) for x,y in ink}
    out=[[0]*width for _ in range(16)]
    for x,y in ink:
        if x+1<width and y+1<16:out[y+1][x+1]=8
    for x,y in ink:out[y][x]=11
    return out


def calendar_tiles(pixels,parts):
    """OBJ image storage concatenates each sprite's row-major 4bpp tiles."""
    out=bytearray();start=0
    for width in parts:
        for ty in (0,8):
            for tx in range(start,start+width,8):
                for y in range(ty,ty+8):
                    for x in range(tx,tx+8,2):out.append(pixels[y][x]|pixels[y][x+1]<<4)
        start+=width
    return bytes(out)


def build_calendar_asset(rom):
    import struct
    from fomt_text import u32
    if (u32(rom,CALENDAR_POINTER)!=ROM_BASE+CALENDAR_ASSET or
        rom[CALENDAR_HEADER_SITE:CALENDAR_HEADER_SITE+8]!=CALENDAR_HEADER_EXPECTED or
        rom[CALENDAR_WEEK_X_SITE:CALENDAR_WEEK_X_SITE+2]!=bytes.fromhex('0625')):
        raise FormatError('calendar resource/header source mismatch')
    # Native resource section strides are verified by func_0805E6CC.
    asset=rom[CALENDAR_ASSET:CALENDAR_ASSET+CALENDAR_ASSET_SIZE]
    if hashlib.sha256(asset).hexdigest()!=CALENDAR_SHA256:
        raise FormatError('calendar sprite asset hash mismatch')
    sizes=(4,16,8,32,32,8,4);sections=[];at=0
    for stride in sizes:
        n=struct.unpack_from('<I',asset,at)[0]
        sections.append((n,bytearray(asset[at+4:at+4+n*stride])))
        at+=4+n*stride
    if at!=len(asset) or [n for n,d in sections] != [22,22,9,134,3,0,22]:
        raise FormatError('unexpected calendar sprite resource sections')
    bitmaps=bytearray();frames=sections[1][1]
    for index in range(22):
        old=list(struct.unpack_from('<8H',frames,index*16));tile_start=old[3];tile_count=old[2]
        if index<10:
            payload=sections[3][1][tile_start*32:(tile_start+tile_count)*32]
        elif index==10:
            payload=calendar_tiles(calendar_pixels(rom,PROFILE['year'],32),(32,))
        elif index<15:
            text=PROFILE['season_heading_prefix']+SEASONS[index-11]
            payload=calendar_tiles(calendar_pixels(rom,text,48),(32,16))
            old[0],old[1]=2,2  # same 32x16 + 16x16 shapes as native Spring
        else:
            payload=calendar_tiles(calendar_pixels(rom,WEEKDAYS[index-15],16),(16,))
            old[0],old[1]=1,7  # native first weekday OBJ is already 16x16
        old[2],old[3]=len(payload)//32,len(bitmaps)//32
        struct.pack_into('<8H',frames,index*16,*old);bitmaps.extend(payload)
    # 124 tiles fit the native 128-tile reservation. Digits, palettes, event
    # graphics, animation records and all date calculations are unchanged.
    assert len(bitmaps)==124*32
    sections[3]=(124,bitmaps)
    return b''.join(struct.pack('<I',n)+data for n,data in sections)


def calendar_header_hook(address):
    # The entry trampoline clobbers r3; read the year again from the verified
    # UI field instead of relying on the incoming native year argument.
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    asm='''
        push {r4,r5,r7,lr}
        sub sp, #8
        mov r7, r6
        ldr r0, year_field
        adds r0, r7, r0
        movs r1, #0
        ldrsh r5, [r0,r1]
        adds r5, #1
        cmp r5, #200
        ble valid_year
        movs r5, #200
    valid_year:
        movs r1, #40
        cmp r5, #10
        blo have_x
        movs r1, #56
        cmp r5, #100
        blo have_x
        movs r1, #72
    have_x:
        movs r0, #3
        str r0, [sp]
        movs r0, #0
        str r0, [sp,#4]
        mov r0, r7
        movs r2, #1
        mov r3, r5
        ldr r4, digits_function
        bl call_r4
        movs r0, #0
        str r0, [sp]
        mov r0, r7
        movs r1, #40
        movs r2, #2
        movs r3, #10
        ldr r4, frame_function
        bl call_r4
        ldr r0, season_field
        adds r0, r7, r0
        movs r1, #0
        ldrsh r3, [r0,r1]
        adds r3, #11
        mov r0, r7
        movs r1, #128
        movs r2, #2
        ldr r4, frame_function
        bl call_r4
        add sp, #8
        pop {r4,r5,r7}
        pop {r3}
        movs r4, #0
        ldr r3, resume
        bx r3
    call_r4: bx r4
        .align 2
    digits_function: .word 0x080A3589
    frame_function: .word 0x080A3619
    year_field: .word 0x1E0
    season_field: .word 0x1E2
    resume: .word 0x080A34EF
    '''
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(asm,addr=address)[0])
