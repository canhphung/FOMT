#!/usr/bin/env python3
"""Real mGBA probes and a normal new-game input replay; never downloads ROMs.

Function probes are isolated in saved emulator states. They are NOT evidence
that an NPC encounter or a hardware playthrough was completed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from fomt_text import VI_CHARS, VI_CODES, ROM_BASE, parse_script, u32, SCRIPT_TABLE, encode
from mgba_session import Session
from vietnamese_font import glyph


def raster(data):
    # RAM renderer uses a 16x16 (four-tile) staging buffer even for 8px advance.
    return [[(data[(y//8*2+x//8)*32+(y%8)*4+x%8//2] >> (x%2*4)) & 15
             for x in range(16)] for y in range(16)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--base-rom", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("build/emulator"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source = args.base_rom.read_bytes()
    target = args.rom.read_bytes()
    report = {"target_sha256": hashlib.sha256(target).hexdigest(), "checks": {},
              "limitations": ["No real-hardware test", "No full-season gameplay test",
                               "Popuri not encountered in normal gameplay replay",
                               "All item screens and description layouts not playtested"]}
    patched = Session(args.rom)
    original = Session(args.base_rom)
    try:
        original.frames(360)
        original_state = original.state()
        patched.frames(360)
        state = patched.state()
        patched.screenshot(args.output_dir/"boot.png")
        for code in range(0x20,0x7F):
            original.restore(original_state)
            patched.restore(state)
            for s in (original,patched):
                s.write(0x0203C000,b"\xAA"*160)
                assert s.call(0x080D0D28,0x0203C010,code) == 1
            assert original.read(0x0203C000,160) == patched.read(0x0203C000,160), f"ASCII U+{code:04X} changed"
        report["checks"]["ascii_glyphs_unchanged"] = 95
        for ch in VI_CHARS:
            patched.restore(state)
            patched.write(0x0203C000,b"\xAA"*160)
            assert patched.call(0x080D0D28,0x0203C010,int.from_bytes(VI_CODES[ch],"big")) == 1
            out = patched.read(0x0203C000,160)
            assert out[:16] == out[144:] == b"\xAA"*16, f"buffer overwrite for {ch}"
            pixels = raster(out[16:144])
            bitmap = glyph(source,ch)
            for y in range(12):
                for x in range(8):
                    assert bool(bitmap[y] & (128>>x)) == (pixels[y+2][x+1] == 1), f"raster mismatch {ch} {x},{y}"
        report["checks"]["vietnamese_glyph_rasters_and_buffer_guards"] = len(VI_CHARS)
        patched.restore(state)
        assert patched.call(0x080D0D28,0,0xEB) == 0, "custom lead must defer to the next byte"
        for ch in VI_CHARS:
            patched.restore(state)
            assert patched.call(0x080D0D28,0,int.from_bytes(VI_CODES[ch],"big")) == 1
        report["checks"]["custom_code_width_without_drawing"] = len(VI_CHARS)
        # Exercise the game's actual multi-byte string renderer against all 7 menu labels.
        from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
        assembler = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
        menu_translations = json.loads(Path("localization/vi/pilot.json").read_text())
        menu_translations = {r["id"]:r["vietnamese_translation"] for r in menu_translations["records"]}
        table = 0xF1A34
        jobs = [(f"menu.pause.{i}",u32(target,table+4*i),menu_translations[f"menu.pause.{i}"],None)
                for i in range(7)]
        for i in range(15):
            key = f"item.food.{i:03d}.name"
            jobs.append((key,u32(target,0xEDCD8+16*i),menu_translations[key],None))
        for start in range(0,len(VI_CHARS),20):
            # Synthetic font diagnostic, not original game dialogue.
            text = VI_CHARS[start:start+20]
            jobs.append((f"font.diagnostic.{start}",0x0203B000,text,encode(text,True)+b"\0"))
        for identifier,ptr,text,payload in jobs:
            patched.restore(state)
            patched.write(0x02038000,b"\xAA"*16+b"\0"*2048+b"\xAA"*16)
            # func_0804E8F0 receives the string as its fifth stack argument.
            if payload is None:
                assert ROM_BASE <= ptr < ROM_BASE+len(target)
            else:
                patched.write(ptr,payload)
            wrapper, _ = assembler.asm(f"""
                push {{r4,lr}}
                sub sp,#4
                ldr r4, text_pointer
                str r4,[sp]
                ldr r4, draw_pointer
                bl call_r4
                add sp,#4
                pop {{r4}}
                pop {{r3}}
                bx r3
            call_r4: bx r4
                .balign 4
            text_pointer: .word {ptr}
            draw_pointer: .word 0x0804E8F1
            """,addr=0x0203D000)
            patched.write(0x0203D000,bytes(wrapper))
            patched.call(0x0203D001,0x00020020,0x02038010,0,0)
            output = patched.read(0x02038000,2080)
            assert output[:16] == output[-16:] == b"\xAA"*16
            rendered = output[16:-16]
            expected = set()
            for col,ch in enumerate(text):
                patched.restore(state)
                value = int.from_bytes(VI_CODES[ch],"big") if ch in VI_CODES else ord(ch)
                patched.call(0x080D0D28,0x0203C000,value)
                char_pixels = raster(patched.read(0x0203C000,128))
                expected.update((col*8+x,y) for y in range(16) for x in range(16) if char_pixels[y][x] == 1)
            actual = set()
            for y in range(16):
                for x in range(32*8):
                    byte = rendered[(y//8*32+x//8)*32+y%8*4+x%8//2]
                    if (byte >> (x%2*4)) & 15 == 1:
                        actual.add((x,y))
            assert actual == expected, f"string renderer lost/misplaced glyphs for {identifier}: {text}"
        report["checks"]["menu_multibyte_string_renderer_and_guards"] = 7
        report["checks"]["crop_item_pointers_and_multibyte_renderer"] = 15
        report["checks"]["full_charset_through_multibyte_string_renderer"] = 134
        patched.restore(state)
        # Replay ordinary controls. A=1, Start=8, Right=16.
        replay_start_frames = patched.frames_run
        patched.press(8,settle=120)
        patched.press(8,settle=300)
        patched.press(1)       # A as player name
        patched.press(8)       # select End
        patched.press(1)
        patched.press(1,settle=180)  # confirm player name
        for _ in range(3):
            patched.press(1,settle=180)  # season, day, birthday confirmation
        for _ in range(2):             # farm and dog names
            patched.press(1)
            patched.press(8)
            patched.press(1)
            patched.press(1,settle=180)
        patched.press(1,settle=200)     # final new-game confirmation
        patched.screenshot(args.output_dir/"intro-start.png")
        for i in range(150):
            patched.press(1,settle=120)
            if i in (0,1,2,3,4,5,6,8,10,12,15):
                patched.screenshot(args.output_dir/f"intro-{i:03d}.png")
        patched.press(8,settle=120)
        for index in range(7):
            patched.frames(1)
            patched.screenshot(args.output_dir/f"pause-{index}.png")
            patched.press(16,settle=30)
        report["checks"]["normal_new_game_input_replay_frames"] = patched.frames_run-replay_start_frames
        # Basic emulator state round trip; distinct from in-game save/load.
        state = patched.state()
        (args.output_dir/"end.state").write_bytes(state.raw)
        before = patched.read(0x02000000,0x40000)
        patched.frames(10)
        patched.restore(state)
        assert patched.read(0x02000000,0x40000) == before
        report["checks"]["emulator_state_round_trip"] = "passed"
        # Actual in-game diary save through normal button presses. Do not restore
        # an EWRAM-only state into a fresh core: SRAM initialization must run too.
        patched.press(1,settle=360)  # open Diary, Save selected
        patched.press(1,settle=300)  # select slot Data 1
        patched.press(1,settle=300)  # write save (empty slot, no overwrite prompt)
        patched.screenshot(args.output_dir/"diary-saved.png")
        savedata = patched.sram()
        assert len(savedata) == 32768 and savedata[:3] == b"GBA"
        assert sum(v != 255 for v in savedata) > 10000
        (args.output_dir/"save-test.sram").write_bytes(savedata)
        reloaded = Session(args.rom)
        try:
            reloaded.frames(360)
            reloaded.load_sram(savedata)
            assert reloaded.sram() == savedata
            reloaded.lib.session_reset(reloaded.handle)
            reloaded.frames(360)
            assert reloaded.sram() == savedata, "game rejected save on cold boot"
            reloaded.press(8,settle=180)
            reloaded.press(8,settle=360)
            reloaded.screenshot(args.output_dir/"diary-load-menu.png")
            reloaded.press(1,settle=360)  # Load? Yes
            reloaded.press(1,settle=360)  # confirm
            reloaded.screenshot(args.output_dir/"game-loaded.png")
            assert reloaded.sram() == savedata
        finally:
            reloaded.close()
        report["checks"]["in_game_sram_save_and_cold_boot_load"] = {
            "size":len(savedata), "sha256":hashlib.sha256(savedata).hexdigest(),
            "save_integrity_after_reboot":"identical", "screenshots":"diary-saved, diary-load-menu, game-loaded"}
        report["checks"]["emulator_error_count"] = patched.lib.session_errors()
        assert report["checks"]["emulator_error_count"] == 0
        report["status"] = "passed; screenshots require visual inspection"
    finally:
        original.close()
        patched.close()
    (args.output_dir/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False))


if __name__ == "__main__":
    main()
