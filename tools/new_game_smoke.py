#!/usr/bin/env python3
"""Cold-boot the new-game UI, including edit/cancel paths and birthday edges.

RAM fields come from reference b8471ae asm/new_game.s and func_0806EA6C;
objects are located by their verified vtables, never hardcoded heap addresses.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

from fomt_text import encode
from mgba_session import Session
from new_game_ui import build_atlas, SUMMARY_BLANK_TILE


def ui_object(session, vtable):
    ram = session.read(0x02000000, 0x40000)
    signature = struct.pack('<I', vtable)
    matches = [i-4 for i in range(4,len(ram)-4,4) if ram[i:i+4] == signature]
    assert len(matches) == 1, f'expected one active UI vtable {vtable:08X}, found {matches}'
    return 0x02000000+matches[0]


def string(session, address):
    return session.read(address,16).split(b'\0',1)[0]


def run(rom, base, library, output):
    output.mkdir(parents=True,exist_ok=True)
    translations = json.loads(Path('localization/vi/new_game.json').read_text())
    texts = {r['id']:r['vietnamese_translation'] for r in translations['records']}
    atlas = build_atlas(base.read_bytes(),texts)
    session = Session(rom,library)
    source = Session(base,library)
    checks = []
    screenshots = []
    try:
        for s in (source,session):
            s.frames(360)
            s.press(8,settle=120)
            s.press(8,settle=300)
        initial = [s.state() for s in (source,session)]
        for season in range(4):
            for day in (1,30):
                case = {'season':season,'day':day}
                evidence = season == 0 and day == 1
                def capture(name):
                    if evidence:
                        filename = f'new-game-{name}.png'
                        session.screenshot(output/filename)
                        screenshots.append(filename)
                def press(key, settle=30):
                    for s in (source,session):s.press(key,settle=settle)
                for s,state in zip((source,session),initial):s.restore(state)
                capture('player')
                boundary = season == 3 and day == 30
                if boundary:
                    for _ in range(12):press(1)
                    player = b'A'*12
                else:
                    press(1); press(16); press(1)  # AB
                    player = b'AB'
                for s in (source,session):
                    name = ui_object(s,0x080E5AB4)+0x461C
                    assert string(s,name) == player.ljust(12,b'_'), 'keyboard name length/input changed'
                press(8); press(1)
                capture('player-confirm')
                if evidence:
                    press(128); press(1,180)  # Sửa lại -> editable name
                    press(2)                 # delete B; retain A
                    player = b'A'
                    press(8); press(1)
                press(1,180)
                capture('season')
                assert session.read(0x06010000,0x8000).find(atlas) >= 0, 'birthday atlas not uploaded intact'
                for _ in range(season):press(16)
                press(1,180)
                if day == 30:
                    for _ in range(4):press(128)
                    press(16)
                capture('day')
                press(1,180)
                capture('birthday-confirm')
                if evidence:
                    press(128); press(1,180)  # Không -> return to date selection
                    press(1,180)             # reopen birthday confirmation
                packed = []
                for s in (source,session):
                    obj = ui_object(s,0x080E7AC4)
                    # Selection is committed to getter field +0x448 only after
                    # Yes closes this dialog (func_0806DB38). Read its inputs.
                    season_x,selected_day = s.read(obj+0x449,2)
                    packed.append((season_x//4) | ((selected_day-1)<<2))
                expected = season | ((day-1)<<2)
                assert packed == [expected,expected], f'birthday changed: {packed} != {expected}'
                press(1,180)
                capture('farm')
                for field,start in (('farm',1),('pet',2)):
                    for _ in range(start):press(16)
                    press(1); press(16); press(1)
                    press(8); press(1)
                    capture(field+'-confirm')
                    press(1,180)
                    if field == 'farm':capture('pet')
                capture('final')
                fields = []
                for s in (source,session):
                    obj = ui_object(s,0x080E5A98)
                    values = [string(s,obj+at) for at in (0x1A34,0x1A44,0x1A54,0x1A64)]
                    assert [values[i] for i in (0,2,3)] == [player,b'BC',b'CD'], values
                    fields.append(values)
                expected_date = encode(texts['ui.newgame.season.'+('spring','summer','fall','winter')[season]],True)+f'{day:2d}'.encode()
                assert fields[1][1] == expected_date, (fields[1][1],expected_date)
                assert session.read(0x06000000+SUMMARY_BLANK_TILE*32,32) == bytes(32), 'background tile contains ink'
                assert struct.unpack('<H',session.read(0x0600C000,2))[0] == SUMMARY_BLANK_TILE
                if evidence:
                    final_states = [s.state() for s in (source,session)]
                    press(128); press(1,300)  # final Sửa lại -> restart editing with names retained
                    for s in (source,session):
                        assert string(s,ui_object(s,0x080E5AB4)+0x461C) == player.ljust(12,b'_')
                    capture('edit-again')
                    for s,state in zip((source,session),final_states):s.restore(state)
                press(1,200)
                case['original_and_localized_selection'] = {
                    'names':[player.decode(),'BC','CD'],'packed_birthday':packed[1]}
                checks.append(case)
        assert session.lib.session_errors() == 0
        return {'target_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
                'status':'passed','cases':checks,'screenshots':screenshots,
                'checks':['four seasons x days 1/30 through normal controls',
                          'all 43 birthday OBJ cells uploaded intact',
                          'name input/delete, 12-character boundary, name/birthday/final cancel',
                          'final summary names/date and blank background tile',
                          'selected names/birthday match original ROM for same input'],
                'limitations':['Keyboard retains original character set; Vietnamese name input not added',
                               'No real GBA hardware test']}
    finally:
        source.close(); session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    parser.add_argument('--base-rom',required=True,type=Path)
    parser.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    parser.add_argument('--output-dir',type=Path,default=Path('build/new-game-emulator'))
    args = parser.parse_args()
    report = run(args.rom,args.base_rom,args.library,args.output_dir)
    (args.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':main()
