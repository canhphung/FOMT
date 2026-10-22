"""Verified childhood flashback literals: reference b8471ae func_0805F5F4.

All slots below are literal pools in the scene's dialogue state machine.
The speaker renderer splits labels into three four-BYTE chunks; Vietnamese
labels instead use a pre-rendered cache in those same three four-CELL buffers.
"""
from __future__ import annotations
import struct
from fomt_text import FormatError, ROM_BASE, cstring, make_record, u32
from new_game_ui import strip

SPEAKERS = (
    ('mother',0xFB234,(0x5F788,0x5F800,0x5F868,0x5F97C),'Mother'),
    ('father',0xFB27C,(0x5F7C4,0x5F824,0x5F8A4,0x5F91C),'Father'),
    ('old_man',0xFB300,(0x5F83C,0x5F8E0,0x5F958,0x5FA84,0x5FAC0,0x5FAE4,0x5FB7C,0x5FBAC),'Old Man'),
    ('unknown',0xFB51C,(0x5F9AC,),'???'),
    ('girl',0xFB53C,(0x5F9F4,0x5FA30,0x5FA54,0x5FB14,0x5FB50),'Girl'),
)
# Dialogue state, exact string start, literal slot, speaker shown by the scene.
DIALOGUE = (
    (0,0xFB23C,0x5F78C,'Mother'),(1,0xFB284,0x5F7C8,'Father'),
    (2,0xFB2D0,0x5F804,'Mother'),(3,0xFB2F4,0x5F828,'Father'),
    (4,0xFB308,0x5F840,'Old Man'),(5,0xFB398,0x5F86C,'Mother'),
    (6,0xFB3CC,0x5F8A8,'Father'),(7,0xFB420,0x5F8E4,'Old Man'),
    (9,0xFB46C,0x5F920,'Father'),(10,0xFB484,0x5F95C,'Old Man'),
    (11,0xFB4D4,0x5F980,'Mother'),(14,0xFB520,0x5F9B0,'???'),
    (15,0xFB534,0x5F9C8,'Player'),(16,0xFB544,0x5F9F8,'Girl'),
    (17,0xFB578,0x5FA34,'Girl'),(18,0xFB5D4,0x5FA58,'Girl'),
    (19,0xFB634,0x5FA88,'Old Man'),(20,0xFB6C0,0x5FAC4,'Old Man'),
    (21,0xFB710,0x5FAE8,'Old Man'),(22,0xFB738,0x5FB18,'Girl'),
    (23,0xFB754,0x5FB54,'Girl'),(24,0xFB7A0,0x5FB80,'Old Man'),
    (25,0xFB7F0,0x5FBB0,'Old Man'),
)
NAME_SITE = 0x50B50
NAME_EXPECTED = bytes.fromhex('f0b557464e464546')
NAME_CACHE_SIZE = 3*256
SCRIPT_IDS = (737,867,1059,1060,1061,1062,1063)


def annotate_scripts(records):
    """Roles witnessed by intro_smoke; choice byte limits in 08050478/50664."""
    for row in records:
        src = row['source']
        sid,index = src.get('script_id'),src.get('string_index')
        if sid not in SCRIPT_IDS:continue
        if sid == 867:
            row['context'] = 'intro_arrival_dialogue' if index<9 else 'intro_transition_narration'
            row['speaker'] = 'Thomas' if index<9 else None
        elif sid == 737:
            choice = index in (2,3,5,6,7,8)
            row['context'] = 'intro_first_morning_choice' if choice else 'intro_first_morning_dialogue'
            row['speaker'] = None if choice else ('Thomas' if index<14 else 'Zack')
            if choice:
                row['max_columns'] = row['max_encoded_bytes'] = 26 if index in (2,3) else 12
        else:
            row['context'] = 'intro_optional_tutorial_choice' if sid==1059 else 'intro_optional_tutorial_dialogue'
            row['speaker'] = None
            if sid == 1059:
                row['max_columns'] = row['max_encoded_bytes'] = 28 if index==0 else 12
        src['context_reference'] = 'intro_smoke.py natural replay; scripts 867/737/1059-1063; choice limits asm/code_0803EE94.s 08050478/08050664'


def extract_records(rom):
    rows = []
    entries = [('speaker.'+key,address,slots,speaker,12) for key,address,slots,speaker in SPEAKERS]
    entries += [(f'dialogue.{state:02d}',address,(slot,),speaker,28)
                for state,address,slot,speaker in DIALOGUE]
    for suffix,address,slots,speaker,columns in entries:
        if any(u32(rom,slot) != ROM_BASE+address for slot in slots):
            raise FormatError('intro flashback literal pointer mismatch')
        row = make_record('intro.flashback.'+suffix,cstring(rom,address,address+512),address,
            'intro_flashback_speaker' if suffix.startswith('speaker.') else 'intro_flashback_dialogue',
            {'kind':'pointer','pointer_offsets':list(slots),
             'reference':'StanHash/fomt b8471ae asm/code_0803EE94.s func_0805F5F4; scene func_0805EE44'},
            columns,speaker)
        if suffix.startswith('speaker.'):
            row['max_encoded_bytes'] = 12
        rows.append(row)
    if rom[NAME_SITE:NAME_SITE+8] != NAME_EXPECTED:
        raise FormatError('speaker name renderer prologue mismatch')
    return rows


def name_cache(rom,text):
    import unicodedata
    text = unicodedata.normalize('NFC',text)
    if len(text)>12:raise FormatError('speaker name exceeds 12 cells')
    cells = strip(rom,text.ljust(12),96)
    # Three original OBJ chunks, each 4x2 tiles in row-major order.
    out = b''.join(cells[(group*4+cell)*64+half*32:(group*4+cell)*64+(half+1)*32]
                   for group in range(3) for half in range(2) for cell in range(4))
    assert len(out) == NAME_CACHE_SIZE
    return out


def name_hook(address,entries):
    """Dispatch only relocated intro speaker pointers; execute native fallback."""
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    asm = f'''
        push {{r0,r1,r2,r3,r4,lr}}
        ldr r2, table_pointer
        movs r4, #{len(entries)}
    lookup:
        ldr r3, [r2]
        cmp r1, r3
        beq found
        adds r2, #8
        subs r4, #1
        bne lookup
        pop {{r0,r1,r2,r3,r4}}
        pop {{r2}}
        mov lr, r2
        push {{r4,r5,r6,r7,lr}}
        mov r7, r10
        mov r6, r9
        mov r5, r8
        ldr r2, native_resume
        bx r2
    found:
        ldr r1, [r2,#4]
        movs r2, #252
        lsls r2, r2, #1
        adds r0, r0, r2
        movs r4, #3
    group:
        movs r2, #64
    copy:
        ldr r3, [r1]
        str r3, [r0]
        adds r0, #4
        adds r1, #4
        subs r2, #1
        bne copy
        adds r0, #4
        subs r4, #1
        bne group
        ldr r0, [sp]
        movs r2, #248
        lsls r2, r2, #1
        adds r0, r0, r2
        ldrb r1, [r0]
        movs r2, #3
        orrs r1, r2
        strb r1, [r0]
        pop {{r0,r1,r2,r3,r4}}
        pop {{r3}}
        bx r3
        .align 2
    native_resume: .word 0x08050B59
    table_pointer: .word {address+0x100}
    '''
    code = bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(asm,addr=address)[0])
    if not entries or len(code)>0x100:raise FormatError('speaker cache dispatch overflow')
    return code.ljust(0x100,b'\0')+b''.join(struct.pack('<II',*entry) for entry in entries)
