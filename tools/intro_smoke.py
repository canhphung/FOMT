#!/usr/bin/env python3
"""Read-only dialogue witnesses during a normal new-game input replay.

The text reader at widget +0xEC and its cursor +0xF4 are verified in
func_0804F288/080ADD5C. The marker at +0xD0 is vtable_unk_080E78C0.
Function probes are isolated and are reported separately from natural replay.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from fomt_text import ROM_BASE, encode, parse_script, u32, verified_rom
from intro_text import NAME_SITE, NAME_EXPECTED, SPEAKERS, name_cache
from mgba_session import Session


def widgets(session):
    ram = session.read(0x02000000,0x40000)
    start = 0
    while True:
        at = ram.find(struct.pack('<I',0x080E78C0),start)
        if at < 0:return
        start = at+4
        root = at-0xD0
        if root < 0 or root+0x554 > len(ram):continue
        state = u32(ram,root+8)
        if state not in range(7):continue
        yield 0x02000000+root,state,u32(ram,root+0xF4),ram[root:root+0x554]


def text_ranges(target,records):
    result = []
    for row in records:
        src = row['source']
        if src['kind'] == 'pointer':
            address = u32(target,src['pointer_offsets'][0])-ROM_BASE
        else:
            script = parse_script(target,u32(target,src['script_pointer_offset'])-ROM_BASE)
            address = script['strings'][src['string_index']]['address']
        payload = encode(row['vietnamese_translation'],True)
        assert target[address:address+len(payload)+1] == payload+b'\0'
        result.append((ROM_BASE+address,ROM_BASE+address+len(payload),row,payload))
    return result


def probe_lines(session,records):
    """Use the actual string renderer on all translated lines, with guards."""
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
    wrapper = '''
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
    '''
    code = bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(wrapper,addr=0x0203D000)[0])
    state = session.state()
    lines = []
    for row in records:
        line = ''
        for part in re.split(r'(\{[^}]+\})',row['vietnamese_translation']):
            if part in ('{CR}','{PAGE}'):
                if line:lines.append((row['id'],line))
                line = ''
            elif part in ('{LF}','{WAIT}'):continue
            elif part.startswith('{VAR:'):
                line += 'A'*12+('?' if part == '{VAR:3F}' else '')
            else:line += part
        if line:lines.append((row['id'],line))
    for identifier,text in lines:
        session.restore(state)
        payload = encode(text,True)+b'\0'
        session.write(0x0203D000,code)
        session.write(0x0203B000,payload)
        session.write(0x02038000,b'\xAA'*16+bytes(1792)+b'\xAA'*16)
        session.call(0x0203D001,0x0002001C,0x02038010,0,0)
        output = session.read(0x02038000,1824)
        assert output[:16] == output[-16:] == b'\xAA'*16, identifier
        assert any(output[16:-16]),identifier
    session.restore(state)
    return len(lines)


def run(args):
    output = args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    target = args.rom.read_bytes()
    source = verified_rom(args.base_rom)
    records = json.loads(Path('localization/vi/intro.json').read_text())['records']
    ranges = text_ranges(target,records)
    texts = {r['id']:r['vietnamese_translation'] for r in records}
    names = {key:name_cache(source,texts['intro.flashback.speaker.'+key]) for key,_,_,_ in SPEAKERS}
    control = bytearray(target)
    control[NAME_SITE:NAME_SITE+8] = NAME_EXPECTED
    control_path = output/'native-name-control.gba'
    control_path.write_bytes(control)
    session = Session(args.rom,args.library)
    native = Session(control_path,args.library)
    seen,seen_names,pages = set(),set(),set()
    witnesses,choices = [],[]
    screenshot_count = 0
    try:
        session.frames(360);native.frames(360)
        probe_count = probe_lines(session,records)
        states = [s.state() for s in (native,session)]
        for text in ('Thomas','Zack','ABCDEFGHIJKL','TooLongName12!'):
            outputs = []
            for s,state in zip((native,session),states):
                s.restore(state)
                s.write(0x02038000,b'\xAA'*0x600)
                s.write(0x0203B000,text.encode()+b'\0')
                s.call(0x08050B50,0x02038010,0x0203B000)
                outputs.append(s.read(0x02038000,0x600))
            assert outputs[0] == outputs[1],f'native speaker fallback changed: {text}'
        session.restore(states[1])

        def observe(phase):
            nonlocal screenshot_count
            active = list(widgets(session))
            for root,state,pointer,ram in active:
                matched_names = []
                if ram[0x1F0]&1:
                    raster = b''.join(ram[0x1F8+i*260:0x1F8+i*260+256] for i in range(3))
                    for key,cache in names.items():
                        if raster == cache:seen_names.add(key);matched_names.append(key)
                for begin,end,row,payload in ranges:
                    if not begin <= pointer <= end:continue
                    seen.add(row['id'])
                    if state != 5:continue  # actual input-wait page, after drawing
                    offset = pointer-begin
                    marker = (phase,row['id'],offset)
                    if marker in pages:continue
                    pages.add(marker)
                    filename = f'{screenshot_count:03d}-{row["id"]}.png'
                    session.screenshot(output/filename)
                    screenshot_count += 1
                    witnesses.append({'id':row['id'],'phase':phase,'cursor_offset':offset,
                        'waits_consumed':payload[:offset].count(5),'widget':hex(root),
                        'speaker_cache_matches':matched_names,'screenshot':filename})
            return active

        def choice(active):return next((w for w in active if w[1] == 6),None)
        def press(key=1,settle=180):session.press(key,settle=settle)
        session.press(8,settle=120);session.press(8,settle=300)
        for field in ('player','farm','pet'):
            for _ in range(12 if field == 'player' else 1):session.press(1)
            session.press(8);session.press(1);session.press(1,settle=180)
            if field == 'player':
                for _ in range(3):session.press(1,settle=180)
        press(settle=200)
        for _ in range(160):
            active = observe('opening')
            if 'script.0867.009' in seen and any(w[1] == 5 for w in active):
                press(settle=360)
                break
            press()
        else:raise AssertionError('opening never reached the next-day transition')
        expected = {r['id'] for r in records if r['id'].startswith('intro.flashback.dialogue.') or r['id'].startswith('script.0867.')}
        assert expected <= seen,sorted(expected-seen)
        assert seen_names == set(names),sorted(set(names)-seen_names)
        session.screenshot(output/'first-morning-house.png')
        # Walk around the table, then through the doorway to trigger script 737.
        session.frames(45,128);session.frames(16,32);session.frames(100,128);session.frames(300)
        guide_state = None
        for _ in range(140):
            active = observe('first-morning-decline')
            if choice(active) and guide_state is None and 'script.0737.001' in seen:
                guide_state = session.state()
                session.screenshot(output/'guide-yes-no.png')
                session.press(128);press()  # Không
                choices.append('first instruction: No')
                continue
            if 'script.0737.021' in seen and any(w[1] == 5 for w in active):
                press(settle=360);break
            press()
        else:raise AssertionError('first morning did not reach Zack goodbye')
        assert guide_state is not None
        session.screenshot(output/'first-morning-complete.png')
        after_morning = session.state()
        session.restore(guide_state);press()  # Có
        for _ in range(15):
            active = observe('guide-accept')
            if choice(active) and 'script.0737.004' in seen:break
            press()
        else:raise AssertionError('instruction topic menu not reached')
        topic_state = session.state()
        session.screenshot(output/'guide-topics.png')
        choices.append('first instruction: Yes; four topic labels rendered')
        session.press(16);press()  # Mẹo hữu ích (top right)
        for _ in range(50):
            active = observe('guide-tips')
            if choice(active):break
            if 'script.0737.012' in seen and any(w[1] == 5 for w in active):
                press();observe('guide-tips');break
            press()
        # The demos are also available later via Tutorial. Require every
        # dialogue record to appear before accepting the replay below.
        for topic in ('crops','chickens','cows','sheep'):
            session.restore(topic_state)
            if topic != 'crops':session.press(128)
            press()
            if topic != 'crops':
                for _ in range(10):
                    if choice(observe('animal-selector')):break
                    press()
                session.screenshot(output/'guide-animals.png')
                # Animal menu: Chicken top-left, Cow bottom-left, Sheep top-right.
                if topic == 'cows':session.press(128)
                if topic == 'sheep':session.press(16)
                press()
            before = set(seen)
            for _ in range(110):
                active = observe('demo-'+topic)
                if choice(active):break
                press()
            choices.append({'topic':topic,'new_records_witnessed':sorted(seen-before)})
        menu_ids = {f'script.0737.{i:03d}' for i in (2,3,5,6,7,8)} | {f'script.1059.{i:03d}' for i in range(5)}
        required = {r['id'] for r in records if 'speaker.' not in r['id']}-menu_ids
        assert required <= seen,sorted(required-seen)
        session.restore(after_morning)
        assert session.lib.session_errors() == 0
        covered_dialogue = {r['id'] for r in records if 'speaker.' not in r['id'] and r['id'] in seen}
        return {'target_sha256':hashlib.sha256(target).hexdigest(),'status':'passed',
            'translated_records':len(records),'isolated_string_renderer_lines_with_guards':probe_count,
            'native_name_fallback_cases':4,'speaker_cache_names_witnessed':sorted(seen_names),
            'player_name':'A'*12,'normal_replay_frames':session.frames_run,
            'normal_dialogue_records_witnessed':sorted(covered_dialogue),
            'menu_records_in_choice_screenshots':sorted(menu_ids),
            'not_witnessed_by_dialogue_reader':sorted(menu_ids),
            'choices':choices,'pages':witnesses,'emulator_error_count':0,
            'limitations':['Choice labels are captured in menu screenshots; the dialogue reader does not retain their pointers',
                           'Function-renderer probes are not a natural encounter or a real-hardware playthrough']}
    finally:
        native.close();session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    parser.add_argument('--base-rom',type=Path,required=True)
    parser.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    parser.add_argument('--output-dir',type=Path,default=Path('build/intro-emulator'))
    args = parser.parse_args()
    report = run(args)
    (args.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='pages'},ensure_ascii=False))


if __name__ == '__main__':main()
