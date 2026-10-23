"""Bounded native tool-title scan: stop at NUL as well as CR.

Original 080CF3B0 advances past NUL and continues searching for CR, even
though Fishing Rod's source description has none. Preserve normal CR paths.
"""
from fomt_text import FormatError
from vietnamese_font import trampoline

SITE = 0xCF3B0
EXPECTED = bytes.fromhex('34780136002c09d0')


def annotate_records(records):
    # Native formatter has char[100], max 99 payload bytes. Reserve quotes,
    # a three-column water counter and the 13-byte unit suffix when applicable.
    for row in records:
        if row['id'].startswith('item.tool.') and row['id'].endswith('.description'):
            number = int(row['id'].split('.')[2])
            if number < 48:
                row['max_encoded_bytes'] = 79 if 32 <= number < 40 else 95
                row['layout_budget'] = 'native char[100] formatter; reserve quotes/counter/unit suffix'
        if row['id'] == 'ui.items.1179fc':
            row['max_encoded_bytes'] = 13


def verify(base):
    if base[SITE:SITE + 8] != EXPECTED:
        raise FormatError('native tool title scanner mismatch')


def hook(address):
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
    assembly = '''
        ldrb r4,[r6]
        cmp r4,#0
        beq terminated
        adds r6,#1
        ldr r3, continuation
        bx r3
    terminated:
        ldr r3, close_title
        bx r3
        .balign 4
    continuation: .word 0x080CF3B9
    close_title: .word 0x080CF3D3
    '''
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(assembly, addr=address)[0])


def patch(address):
    # Same LDR r3/BX r3/literal form as the verified glyph entry trampoline.
    return trampoline(address)
