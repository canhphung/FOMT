#!/usr/bin/env python3
"""Actual Rucksack window fixtures, with explicit temporary RAM inventory setup.

No claim that rare/unused items were obtained through gameplay. Every case
restores a cold-booted house state, modifies documented item fields, then uses
normal Start/Right/A/R controls. Foreground pixels must match all glyphs.
"""
import argparse
import ctypes as C
import hashlib
import json
import re
from pathlib import Path
import struct

from date_ui_smoke import calendar_object
from fomt_text import encode, extract, u32, verified_rom, ROM_BASE
from mgba_session import Session
from vietnamese_font import glyph, ascii_glyph


def framebuffer(session):
    raw = C.string_at(session.lib.session_pixels(session.handle), 240 * 160 * 4)
    return {(i % 240, i // 240) for i in range(104 * 240, 160 * 240)
            if raw[i * 4:i * 4 + 3] == b'\0\0\0'}


def foreground(base, text, raw_mask):
    # The native three-line viewport scrolls on LF, including a trailing LF.
    # Keep the source token stream; compare the settled viewport, not hidden lines.
    scroll_lines = max(0, text.count("{LF}") - 2)
    text = "{LF}".join(text.split("{LF}")[scroll_lines:]).removeprefix("{CR}")
    expected = set()
    # Verified native item-info origin, 17px line stride. Cache adds X +1.
    x, y = 8, 107
    for part in re.split(r'(\{[^}]+\})', text):
        if part == '{CR}':
            x = 8
        elif part == '{LF}':
            y += 17
        elif part.startswith('{RAW:'):
            code = int(part[5:-1], 16)
            pixels, advance = raw_mask(code)
            expected.update((x + dx, y + dy) for dx, dy in pixels)
            x += advance * 8
        elif part.startswith('{'):
            raise AssertionError('unexpected item-info token: ' + part)
        else:
            for character in part:
                mask = ascii_glyph(base, character) if ord(character) < 128 else glyph(base, character)
                expected.update((x + dx + 1, y + dy) for dy, row in enumerate(mask)
                                for dx in range(8) if row & (128 >> dx))
                x += 8
    assert all(8 <= x < 240 and 104 <= y < 160 for x, y in expected), 'glyph would leave item-info window'
    return expected


def run(args):
    base = verified_rom(args.base_rom)
    target = args.rom.read_bytes()
    originals = {r['id']: r for r in extract(base)['records']}
    records = {r['id']: r for p in (Path('localization/vi') / n for n in
              ('pilot.json', 'items.json', 'new_game.json', 'intro.json', 'start_menu.json', 'item_descriptions_tools.json'))
               for r in json.loads(p.read_text())['records']}
    descriptions = [r for r in originals.values() if r['context'] == 'item_description']
    if args.limit:
        descriptions = descriptions[:args.limit]
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    session, probe = Session(args.rom, args.library), Session(args.rom, args.library)
    masks = {}
    captures, cases = [], []
    try:
        probe.frames(360)
        probe_state = probe.state()
        def raw_mask(code):
            if code not in masks:
                probe.restore(probe_state)
                probe.write(0x0203B000, b'\xAA' * 160)
                advance = probe.call(0x080D0D28, 0x0203B010, code)
                data = probe.read(0x0203B000, 160)
                assert data[:16] == data[-16:] == b'\xAA' * 16
                pixels = {(x, y) for y in range(16) for x in range(16)
                          if data[16 + (y // 8 * 2 + x // 8) * 32 + y % 8 * 4 + x % 8 // 2] >> (x % 2 * 4) & 15 == 1}
                masks[code] = pixels, advance
            return masks[code]
        session.frames(360)
        source_sram = args.sram.read_bytes()
        session.load_sram(source_sram)
        session.lib.session_reset(session.handle)
        session.frames(360)
        for key, settle in [(8, 180), (8, 360), (1, 360), (1, 360)]:
            session.press(key, settle=settle)
        house = session.state()
        session.frames(24, 16)
        session.frames(60, 64)
        session.frames(30)
        session.press(1, settle=200)
        game = u32(session.read(calendar_object(session) + 8, 4), 0)
        session.restore(house)
        assert u32(session.read(game + 0x1C38, 4), 0) == 2, 'fixture requires the native small Rucksack'
        assert base[0x4192C:0x41930] == struct.pack('<I', 0x1C38), 'native bag offset literal mismatch'
        counts = {}
        for label, getter, width in [('water', 0x0800E94C, 3), ('steps', 0x0800E958, 10),
                ('energy', 0x0800E4F0, 3), ('maximum_energy', 0x0800E51C, 3), ('fatigue', 0x0800E4FC, 3)]:
            probe.restore(probe_state)
            probe.write(game + 0x1BD8, session.read(game + 0x1BD8, 0x98))
            value = probe.call(getter, game + 0x1BD8)
            probe.call(0x0804EC84, value, 0x0203B000, width)
            counts[label] = probe.read(0x0203B000, 32).split(b'\0', 1)[0].decode('ascii')
        for original in descriptions:
            identifier = original['id']
            group, number = identifier.split('.')[1:3]
            number = int(number)
            text = records[identifier]['vietnamese_translation']
            for mode in ('description', 'wrapped_name') if group != 'tool' else ('description',):
                session.restore(house)
                if group == 'tool':
                    session.write(game + 0x1C34, bytes((number, 1)))
                    session.write(game + 0x1C60, bytes((number, 1)))
                else:
                    kind = int(group == 'article') | (2 if mode == 'wrapped_name' else 0)
                    session.write(game + 0x1C3C, bytes((kind, number, 0, 0)))
                session.press(8, settle=120)
                session.press(16, settle=30)
                session.press(1, settle=200)
                session.press(256, settle=60)
                if group == 'tool':
                    session.press(256, settle=60)
                wanted = text
                if group == 'tool':
                    if number in (0, 8, 16, 24, 32, 40):
                        title, separator, body = text.partition('{CR}')
                        wanted = ' "' + title + ' "' + separator + body
                    if number in (32, 33, 34, 35, 36, 38, 39):
                        wanted += counts['water'] + records['ui.items.1179fc']['vietnamese_translation']
                    if number == 76:
                        wanted = records['ui.items.1179e0']['vietnamese_translation'] + counts['steps'] + records['ui.items.1179f0']['vietnamese_translation']
                if mode == 'wrapped_name':
                    wanted = records[identifier.replace('.description', '.name')]['vietnamese_translation'] + records['ui.items.117a8c']['vietnamese_translation']
                expected = foreground(base, wanted, raw_mask)
                actual = framebuffer(session)
                display_kind = 'pedometer' if group == 'tool' and number == 76 else mode
                if group == 'tool' and number == 80 and expected != actual:
                    wanted = (records['ui.items.1179ac']['vietnamese_translation']
                        + records['ui.items.1179bc']['vietnamese_translation'] + counts['energy'] + '/' + counts['maximum_energy']
                        + '{CR}{LF}' + records['ui.items.1179cc']['vietnamese_translation'] + counts['fatigue'] + '/100')
                    expected = foreground(base, wanted, raw_mask)
                    display_kind = 'truth_stats'
                if expected != actual:
                    session.screenshot(out / ('failure-' + identifier + '-' + mode + '.png'))
                    raise AssertionError((identifier, mode, 'missing', len(expected - actual), 'extra', len(actual - expected)))
                cases.append({'id': identifier, 'mode': mode, 'display_kind': display_kind, 'native_scrolled_lines': max(0, wanted.count('{LF}') - 2), 'foreground_pixels_verified': len(expected)})
                if (number in (0, 40, 66, 90, 151) and mode == 'description') or (group == 'food' and number == 66):
                    name = identifier + '-' + mode + '.png'
                    session.screenshot(out / name)
                    captures.append(name)
        assert session.sram() == source_sram, 'RAM-only UI fixtures must not save changes'
        assert session.lib.session_errors() == probe.lib.session_errors() == 0
        return {'status': 'passed', 'target_sha256': hashlib.sha256(target).hexdigest(),
                'item_info_windows': sum(c['mode'] == 'description' for c in cases),
                'native_scroll_cases': sum(c['native_scrolled_lines'] > 0 for c in cases),
                'wrapped_name_windows': sum(c['mode'] == 'wrapped_name' for c in cases),
                'cases': cases, 'screenshots': captures, 'sram_unchanged': True,
                'emulator_error_count': 0, 'fixture_setup': 'temporary documented RAM item fields; normal UI input afterward',
                'limitations': ['Rare/unused items not obtained through gameplay.',
                    'Foreground pixels checked, not a language approval or complete shop purchase playthrough.',
                    'Unwrapped tool name pointers have renderer checks; tools have no gift-wrap view.', 'No real GBA hardware test.']}
    finally:
        session.close()
        probe.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('--base-rom', type=Path, required=True)
    parser.add_argument('--sram', type=Path, default=Path('local-data/fixtures/day2.sram'))
    parser.add_argument('--library', type=Path, default=Path('build/mgba_bridge.so'))
    parser.add_argument('--output-dir', type=Path, default=Path('build/item-ui'))
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        parser.error('--limit must be positive')
    if any(p.resolve().is_relative_to(args.output_dir.resolve()) for p in
           (args.rom, args.base_rom, args.sram, args.library)):
        parser.error('inputs must live outside output-dir')
    report = run(args)
    (args.output_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('cases', 'screenshots')}))


if __name__ == '__main__':
    main()
