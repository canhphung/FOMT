"""A one-tile overlay for the HUD grave, one scanline above the native sprites.

A4NE rev 0: constructor/destructor own the extra VRAM resource and upload
command. All original object fields stay at their native offsets.
"""
from __future__ import annotations
import re
from fomt_text import FormatError

OLD_SIZE=0x35C
OBJECT_SIZE=0x380
RESOURCE=0x35C
TRANSFER=0x364
DIRTY=0x37C
VISIBLE=0x37D
SITES={'constructor':0x3C5B0,'draw':0x3C7C8,'destructor':0xE0D70}
EXPECTED={'constructor':'f0b557464e464546','draw':'f0b557464e464546e0b49bb089469246',
          'destructor':'70b5061c0d1cd021'}
SIZE_SITE=0x3C5BE


def verify(rom):
    for name,at in SITES.items():
        if rom[at:at+len(bytes.fromhex(EXPECTED[name]))].hex()!=EXPECTED[name]:raise FormatError('HUD overlay prologue mismatch: '+name)
    if rom[SIZE_SITE:SIZE_SITE+4]!=bytes.fromhex('d7208000'):
        raise FormatError('HUD object allocation size mismatch')


def draw_trampoline(address):
    # Unlike the three-argument setters, draw receives its OAM list in r3.
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    source=f'push {{r3}}; ldr r3, target; mov ip,r3; pop {{r3}}; bx ip; .align 2; target: .word {address|1}'
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(source,addr=0x0803C7C8)[0])


def accent_tile():
    # Centered grave: the native HUD origin is (x+4,y+4); this sprite is
    # (x+20,y+3), so (4,0)/(5,1) becomes HUD-local (20,-1)/(21,0).
    pixels=[[0]*8 for _ in range(8)]
    pixels[0][4]=pixels[1][5]=1
    return bytes(pixels[y][x]|pixels[y][x+1]<<4 for y in range(8) for x in range(0,8,2))


def assemble(address,tile_address):
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB);blob=bytearray();entries={}
    def emit(name,source):
        while len(blob)%4:blob.append(0)
        at=address+len(blob);entries[name]=at
        # Appended code is >4MiB from native code: ARM7 Thumb BL cannot reach
        # it directly. Local veneers use BX and preserve the native Thumb bit.
        native=sorted(set(re.findall(r'bl #0x([0-9A-Fa-f]+)',source)))
        for target in native:
            source=source.replace('bl #0x'+target,'bl native_'+target)
            source+=f'\nnative_{target}: ldr r3, pointer_{target}\n bx r3\n .align 2\npointer_{target}: .word {int(target,16)|1}\n'
        blob.extend(bytes(ks.asm(source,addr=at)[0]))
    for name,at in SITES.items():
        raw=','.join(str(x) for x in bytes.fromhex(EXPECTED[name]))
        emit(name+'_original',f'''
            .byte {raw}
            push {{r0}}
            ldr r0, resume
            mov ip, r0
            pop {{r0}}
            bx ip
            .align 2
        resume: .word {0x08000000+at+len(bytes.fromhex(EXPECTED[name]))+1}
        ''')
    emit('constructor',f'''
        push {{r4,r5,r6,r7,lr}}
        sub sp, #4
        mov r4, r0
        ldr r3, original
        bl call_r3
        ldr r5, [r4]
        ldr r6, resource_offset
        adds r6, r5, r6
        movs r7, #0
        str r7, [r6]
        str r7, [r6,#4]
        mov r0, r6
        bl #0x08007874
        mov r0, r6
        movs r1, #0
        bl #0x08007B54
        str r0, [r6,#4]
        adds r6, #8
        str r7, [r6]
        str r7, [r6,#4]
        ldr r0, transfer_vtable
        str r0, [r6,#8]
        str r7, [r6,#12]
        str r7, [r6,#16]
        str r7, [r6,#20]
        adds r6, #24
        movs r0, #1
        strb r0, [r6]
        strb r7, [r6,#1]
        mov r0, r4
        add sp, #4
        pop {{r4,r5,r6,r7,pc}}
    call_r3: bx r3
        .align 2
    original: .word {entries['constructor_original']|1}
    resource_offset: .word {RESOURCE}
    transfer_vtable: .word 0x080E77D0
    ''')
    emit('destructor',f'''
        push {{r4,r5,r6,lr}}
        mov r4, r0
        mov r5, r1
        ldr r6, resource_offset
        adds r6, r4, r6
        mov r0, r6
        adds r0, #8
        movs r1, #2
        bl #0x080098AC
        mov r0, r6
        ldr r1, [r6,#4]
        bl #0x08007C28
        mov r0, r6
        movs r1, #2
        bl #0x080079E8
        mov r0, r4
        mov r1, r5
        ldr r3, original
        bl call_r3
        pop {{r4,r5,r6,pc}}
    call_r3: bx r3
        .align 2
    resource_offset: .word {RESOURCE}
    original: .word {entries['destructor_original']|1}
    ''')
    emit('draw',f'''
        push {{r4,r5,r6,r7,lr}}
        sub sp, #12
        mov r4, r0
        mov r5, r1
        mov r6, r2
        mov r7, r3
        ldr r0, [sp,#32]
        str r0, [sp]
        ldr r0, original
        mov ip, r0
        mov r0, r4
        bl call_ip
        ldr r0, [r4]
        ldr r1, visible_offset
        ldrb r1, [r0,r1]
        cmp r1, #0
        beq done
        ldr r1, [r0,#0x64]
        cmp r1, #0
        beq done
        ldr r1, left_handle_offset
        ldr r1, [r0,r1]
        cmp r1, #0
        beq done
        ldr r1, resource_offset
        adds r4, r0, r1
        ldr r1, [r4,#4]
        cmp r1, #0
        beq done
        mov r0, r4
        bl #0x08007D4C
        str r0, [sp,#4]
        mov r0, r4
        adds r0, #32
        ldrb r0, [r0]
        cmp r0, #0
        beq uploaded
        mov r1, r4
        adds r1, #8
        ldr r0, tile_source
        str r0, [r1,#12]
        ldr r0, [sp,#4]
        lsls r0, r0, #5
        ldr r2, vram_base
        adds r0, r0, r2
        str r0, [r1,#16]
        movs r0, #32
        str r0, [r1,#20]
        ldr r0, [sp]
        ldr r2, [r0,#8]
        ldr r3, [r2,#16]
        bl call_r3
        movs r0, #0
        mov r1, r4
        adds r1, #32
        strb r0, [r1]
    uploaded:
        ldr r0, resource_offset
        subs r0, r4, r0
        adds r0, #0x60
        ldr r1, [r0,#4]
        bl #0x080074C0
        movs r1, #15
        ands r0, r1
        lsls r0, r0, #12
        ldr r1, [sp,#4]
        orrs r0, r1
        ldrb r1, [r7]
        cmp r1, #127
        bhi done
        lsls r2, r1, #3
        adds r2, #4
        adds r2, r7, r2
        strh r0, [r2,#4]
        adds r6, #3
        movs r0, #255
        ands r6, r0
        ldr r0, mosaic_flag
        orrs r6, r0
        strh r6, [r2]
        adds r5, #20
        ldr r0, x_mask
        ands r5, r0
        strh r5, [r2,#2]
        adds r1, #1
        strb r1, [r7]
    done:
        add sp, #12
        pop {{r4,r5,r6,r7,pc}}
    call_ip: bx ip
    call_r3: bx r3
        .align 2
    original: .word {entries['draw_original']|1}
    visible_offset: .word {VISIBLE}
    left_handle_offset: .word 0x188
    resource_offset: .word {RESOURCE}
    tile_source: .word {tile_address}
    vram_base: .word 0x06010000
    x_mask: .word 511
    mosaic_flag: .word 0x1000
    ''')
    return bytes(blob),entries
