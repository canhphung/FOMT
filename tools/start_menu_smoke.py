#!/usr/bin/env python3
"""Replay START menus from a locally generated in-game SRAM save.

First run emulator_smoke.py to produce save-test.sram. This tool uses that SRAM
in a cold boot, never a savestate from a different ROM. Font probes are isolated
from natural menu navigation and do not prove all animal/map states were visited.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

from fomt_text import ROM_BASE, encode, u32
from intro_smoke import probe_lines
from mgba_session import Session


def run(args):
    out = args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    rows = json.loads(Path('localization/vi/start_menu.json').read_text())['records']
    target = args.rom.read_bytes()
    # Verify every relocated literal/table field, not only the first pointer.
    for row in rows:
        payload = encode(row['vietnamese_translation'],True)+b'\0'
        for slot in row['source']['pointer_offsets']:
            at = u32(target,slot)-ROM_BASE
            assert at >= 0x800000 and target[at:at+len(payload)] == payload,row['id']
    session = Session(args.rom,args.library)
    names = ('diary','rucksack','world-map','farm-map','earnings','memo','tutorial')
    shots = []
    def capture(name):
        session.frames(1)  # framebuffer is refreshed after restoring core state
        path = out/(name+'.png')
        session.screenshot(path)
        shots.append(path.name)
    try:
        session.frames(360)
        line_count = probe_lines(session,rows)
        session.load_sram(args.sram.read_bytes())
        session.lib.session_reset(session.handle)
        session.frames(360)
        session.press(8,settle=180)
        session.press(8,settle=360)
        session.press(1,settle=360)
        session.press(1,settle=360)
        session.press(8,settle=120)
        pause = session.state()
        menu_states = []
        bag_checks = []
        for i,name in enumerate(names):
            session.restore(pause)
            for _ in range(i):session.press(16)
            session.press(1,settle=300)
            capture('start-'+name)
            menu_states.append(session.state())
            if name == 'rucksack':
                ram = session.read(0x02000000,0x40000)
                for vt,identifier in ((0x080E85BC,'ui.start.1000b4'),(0x080E85AC,'ui.start.1000bc')):
                    signature = struct.pack('<I',vt)
                    found = [p-0x210 for p in range(0x210,len(ram)-4,4) if ram[p:p+4]==signature]
                    assert len(found)==1,(hex(vt),found)
                    at = found[0]
                    row = next(r for r in rows if r['id']==identifier)
                    payload = encode(row['vietnamese_translation'],True)
                    assert ram[at+0x28C:at+0x298].split(b'\0',1)[0] == payload,identifier
                    size = u32(ram,at+0x298)
                    assert size in (2,4,8), f'backpack size field after title changed: {size}'
                    bag_checks.append({'id':identifier,'encoded_bytes':len(payload),'cells':len(row['vietnamese_translation']),
                                       'title_buffer_bytes':12,'next_field_backpack_size':size})
        # Diary explanations, both confirmations, all accessible statistics pages.
        session.restore(menu_states[0])
        for i in range(6):
            capture('diary-row-'+str(i))
            session.press(128,settle=120)
        for mode in ('save','load'):
            session.restore(menu_states[0])
            if mode=='load':session.press(16)
            session.press(1,settle=180)
            capture('diary-'+mode+'-slot')
            session.press(1,settle=180)
            capture('diary-'+mode+'-confirm')
            session.press(128)  # No; avoid changing the fixture during menu screenshots
            session.press(1,settle=180)
        for i,count in ((4,4),(5,3)):
            session.restore(menu_states[i])
            for page in range(count):
                capture(names[i]+'-page-'+str(page))
                session.press(16,settle=120)
        session.restore(menu_states[6])
        session.press(16)
        session.press(1,settle=240)
        capture('tutorial-useful-tips')
        from new_game_ui import strip
        title = next(r['vietnamese_translation'] for r in rows if r['id']=='ui.start.11561c')
        expected_cache = strip(target,title,len(title)*8)
        title_vram_offset = session.read(0x06010000,0x8000).find(expected_cache)
        assert title_vram_offset >= 0, 'book title glyph cache not uploaded intact'
        for page in range(1,5):
            session.frames(60,128)
            session.frames(10)
            capture('tutorial-useful-tips-'+str(page))
        for topic in ('crops','animals'):
            session.restore(menu_states[6])
            if topic=='animals':session.press(128)
            session.press(1,settle=240)
            capture('tutorial-'+topic)
        assert session.lib.session_errors()==0
        from PIL import Image
        sheet = Image.new('RGB',(720,540),'#222222')
        for i,name in enumerate(names):
            sheet.paste(Image.open(out/('start-'+name+'.png')),((i%3)*240,(i//3)*180))
        sheet.save(out/'start-overview.png')
        return {'target_sha256':hashlib.sha256(target).hexdigest(),'status':'passed',
                'translated_records':len(rows),'isolated_renderer_lines_with_guards':line_count,
                'relocated_pointer_fields_verified':sum(len(r['source']['pointer_offsets']) for r in rows),
                'bag_title_buffers':bag_checks,'book_title_cache_vram_offset':title_vram_offset,'screenshots':shots,'emulator_error_count':0,
                'limitations':['Screenshots require visual inspection; no OCR assertion',
                               'Empty animal/fish lists in this SRAM fixture; those labels have isolated renderer checks only',
                               'Map descriptions all pointer-verified and line-probed; all hotspots not manually replayed',
                               'HUD date abbreviations SP/Mon/AM and day-unit graphics remain original',
                               'No real-hardware or full-season test']}
    finally:session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    parser.add_argument('--sram',type=Path,required=True)
    parser.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    parser.add_argument('--output-dir',type=Path,default=Path('build/start-menu-emulator'))
    args = parser.parse_args()
    report = run(args)
    (args.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
