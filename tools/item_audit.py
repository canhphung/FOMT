#!/usr/bin/env python3
"""Audit all canonical item pointers, nontext fields and verified shop catalogs."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from fomt_text import ITEM_TABLES, ROM_BASE, ROM_SHA1, check_translation, encode, extract, u32, verified_rom
from localization_queue import DEFAULT_TRANSLATIONS
from intro_smoke import probe_lines
from mgba_session import Session


def audit(base, target, translations):
    originals = {r['id']: r for r in extract(base)['records']}
    vi = {r['id']: r for r in translations}
    assert len(vi) == len(translations), 'duplicate translation ID'
    rows = [r for r in originals.values() if r['context'] in
            ('item_name', 'item_description', 'native_shop', 'native_item_window')]
    for source in rows:
        row = vi[source['id']]
        assert row['original_english'] == source['original_english'], source['id']
        payload = encode(row['vietnamese_translation'], True)
        check_translation(source['original_english'], row['vietnamese_translation'], source['max_columns'])
        assert len(payload) <= source.get('max_encoded_bytes', 1 << 30), source['id']
        for slot in source['source']['pointer_offsets']:
            at = u32(target, slot) - ROM_BASE
            assert at >= len(base) and target[at:at + len(payload) + 1] == payload + b'\0', source['id']
    nontext = 0
    for table, count, stride, desc in ITEM_TABLES.values():
        for index in range(count):
            for byte in set(range(stride)) - set(range(4)) - set(range(desc, desc + 4)):
                at = table + index * stride + byte
                assert target[at] == base[at], ('item nontext field changed', hex(at))
            nontext += 1
    shops = []
    for name, table, size, group in [('seeds', 0xFDDD8, 0x68, 'tool'),
            ('groceries', 0xFDFA4, 0x40, 'food'), ('clinic', 0xFE050, 0x20, 'food')]:
        assert target[table:table + size] == base[table:table + size], name
        goods = []
        for index in range(size // 8):
            item, price = struct.unpack_from('<II', base, table + index * 8)
            if (item, price) == (0, 0):
                continue
            identifier = f'item.{group}.{item:03}.name'
            assert identifier in originals, (name, index, item)
            goods.append({'id': identifier, 'original_english': originals[identifier]['original_english'],
                          'vietnamese': vi[identifier]['vietnamese_translation'], 'price_G': price})
        shops.append({'kind': name, 'rom_address': hex(ROM_BASE + table), 'bytes_unchanged': size, 'goods': goods})
    guide = originals['script.1043.108']['original_english']
    passage = guide[guide.index('Here you can buy:'):]
    expected_names = ['Rice Balls', 'Bread', 'Oil', 'Flour', 'Curry Powder', 'Muffin Mix', 'Chocolate']
    assert [passage.index(name) for name in expected_names] == sorted(passage.index(name) for name in expected_names)
    assert [r['id'] for r in shops[1]['goods']] == [f'item.food.{i:03}.name' for i in range(63, 70)]
    flour = shops[1]['goods'][3]
    assert flour['original_english'] == 'Flower' and flour['vietnamese'] == 'Bột mì' and flour['price_G'] == 50
    return rows, {'target_sha256': hashlib.sha256(target).hexdigest(),
        'item_names': 347, 'item_descriptions': 347,
        'native_shop_and_item_literals': len(rows) - 694,
        'pointer_fields_verified': sum(len(r['source']['pointer_offsets']) for r in rows),
        'item_records_nontext_fields_unchanged': nontext, 'shops': shops,
        'flour_identity': {'id': flour['id'], 'food_id_hex': '0x42', 'icon_id': 163,
             'original_spelling_retained': 'Flower', 'translation': 'Bột mì',
             'independent_guide_source_id': 'script.1043.108',
             'guide_grocery_order': expected_names, 'matched_grocery_position': 4}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path)
    p.add_argument('--base-rom', type=Path, required=True)
    p.add_argument('--library', type=Path, default=Path('build/mgba_bridge.so'))
    p.add_argument('--output-dir', type=Path, default=Path('build/item-audit'))
    args = p.parse_args()
    if any(path.resolve().is_relative_to(args.output_dir.resolve()) for path in
           (args.rom, args.base_rom, args.library, *DEFAULT_TRANSLATIONS)):
        p.error('inputs must live outside output-dir')
    base = verified_rom(args.base_rom)
    translations = [r for path in DEFAULT_TRANSLATIONS for r in json.loads(path.read_text())['records']]
    originals, report = audit(base, args.rom.read_bytes(), translations)
    ids = {r['id'] for r in originals}
    selected = [r for r in translations if r['id'] in ids]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    subset = {'rom_sha1': ROM_SHA1, 'records': selected}
    (args.output_dir / 'records.json').write_text(json.dumps(subset, ensure_ascii=False, indent=2) + '\n')
    session = Session(args.rom, args.library)
    try:
        session.frames(360)
        report['renderer_lines_with_buffer_guards'] = probe_lines(session, selected)
        assert session.lib.session_errors() == 0
        report['emulator_error_count'] = 0
    finally:
        session.close()
    report['status'] = 'passed'
    report['limitations'] = ['Shop stock/price tables and literal/render paths verified; no normal purchase/sale playthrough claimed.',
                             'Language review pending; UI fixtures are reported separately.']
    (args.output_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('shops', 'flour_identity')}))


if __name__ == '__main__':
    main()
