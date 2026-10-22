#!/usr/bin/env python3
"""Compare actual mGBA string-renderer output from two local patched ROMs.

This is a labeled font diagnostic, not a screenshot of an NPC encounter.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from fomt_text import encode
from mgba_session import Session

SAMPLES = ["Aa ÀÁÂÃĂ A  Dd Đđ", "Ii íìỉĩị  Yy ýỳỷỹỵ", "Oo Ôô Ơơ  Uu Ưư",
           "a á à ả ã ạ ă â ấ ậ", "Này! Chủ nông trại này",
           "À, chừng sáu tháng trước.", "Lúc dọn nhà cho ông ấy,",
           "bác tìm thấy di chúc.", "Nhật ký   Hướng dẫn"]


def render_line(session, state, text):
    session.restore(state)
    session.write(0x0203B000,encode(text,True)+b"\0")
    session.write(0x02038000,b"\xAA"*16+b"\0"*2048+b"\xAA"*16)
    code,_ = Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm("""
        push {r4,lr}
        sub sp,#4
        ldr r4, text_pointer
        str r4,[sp]
        ldr r4, draw_pointer
        bl call_r4
        add sp,#4
        pop {r4}
        pop {r3}
        bx r3
    call_r4: bx r4
        .balign 4
    text_pointer: .word 0x0203B000
    draw_pointer: .word 0x0804E8F1
    """,addr=0x0203D000)
    session.write(0x0203D000,bytes(code))
    session.call(0x0203D001,0x00020020,0x02038010,0,0)
    out = session.read(0x02038000,2080)
    assert out[:16] == out[-16:] == b"\xAA"*16
    data = out[16:-16]
    image = Image.new("RGB",(256,16),"white")
    colors = {0:(255,255,255),1:(0,0,0),2:(150,150,150)}
    for y in range(16):
        for x in range(256):
            value = data[(y//8*32+x//8)*32+y%8*4+x%8//2] >> (x%2*4) & 15
            image.putpixel((x,y),colors[value])
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before",type=Path)
    parser.add_argument("after",type=Path)
    parser.add_argument("--output",type=Path,default=Path("build/font-spacing-comparison.png"))
    args = parser.parse_args()
    sessions = []
    scale,panel_width,row_height = 3,788,78
    canvas = Image.new("RGB",(panel_width*2,50+len(SAMPLES)*row_height),"#e9e9e9")
    draw = ImageDraw.Draw(canvas)
    try:
        for col,path in enumerate((args.before,args.after)):
            session = Session(path)
            sessions.append(session)
            session.frames(360)
            state = session.state()
            draw.text((col*panel_width+10,10),"BEFORE: v1 (mixed outlines/baselines)" if col==0 else "AFTER: v2 (native outlines, common baseline)",fill="black")
            for index,text in enumerate(SAMPLES):
                line = render_line(session,state,text).resize((768,48),Image.Resampling.NEAREST)
                x,y = col*panel_width+10,40+index*row_height
                canvas.paste(line,(x,y))
                draw.text((x,y+50),f"diagnostic {index+1} - ticks: original 8px advance",fill="#555555")
                for tick in range(len(text)+1):
                    tx=x+tick*8*scale
                    draw.line((tx,y+46,tx,y+48),fill="#85a8b8")
    finally:
        for session in sessions:
            session.close()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    canvas.save(args.output)


if __name__ == "__main__":
    main()
