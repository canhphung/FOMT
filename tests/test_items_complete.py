"""Actual source checks for item coverage, explicit source defects and native guards."""
import json
import os
from pathlib import Path

import pytest

from fomt_text import FormatError, check_translation, encode, extract, verified_rom
from localization_queue import DEFAULT_TRANSLATIONS
import item_window
import shop_text


@pytest.fixture
def base():
    if not os.environ.get('FOMT_ROM'):
        pytest.skip('FOMT_ROM required for verified USA source checks')
    return verified_rom(os.environ['FOMT_ROM'])


def test_all_item_records_and_native_literals_preserve_actual_source_and_limits(base):
    originals = {r['id']: r for r in extract(base)['records']}
    vi = {r['id']: r for path in DEFAULT_TRANSLATIONS for r in json.loads(path.read_text())['records']}
    for context, count in [('item_name', 347), ('item_description', 347), ('native_shop', 17), ('native_item_window', 9)]:
        rows = [r for r in originals.values() if r['context'] == context]
        assert len(rows) == count
        for row in rows:
            translated = vi[row['id']]
            assert translated['original_english'] == row['original_english']
            check_translation(row['original_english'], translated['vietnamese_translation'], row['max_columns'])
            assert len(encode(translated['vietnamese_translation'], True)) <= row.get('max_encoded_bytes', 1 << 30)
    assert 'Flower' == originals['item.food.066.name']['original_english']
    assert vi['item.food.066.name']['vietnamese_translation'] == 'Bột mì'
    assert vi['item.article.032.description']['vietnamese_translation'].startswith('Hoàng ngọc{CR}')
    assert vi['item.article.010.description']['vietnamese_translation'].startswith('Len (X)')


def test_shop_literal_guards_reject_modified_pointer_and_source(base):
    at, slots, _ = shop_text.SPECS[0]
    slot = int(slots[0], 16)
    for where in (at, slot):
        altered = bytearray(base)
        altered[where] ^= 1
        with pytest.raises(FormatError, match='literal mismatch'):
            shop_text.extract_records(altered)


def test_native_title_scan_guard_and_effective_tool_byte_budgets(base):
    item_window.verify(base)
    altered = bytearray(base)
    altered[item_window.SITE] ^= 1
    with pytest.raises(FormatError, match='scanner mismatch'):
        item_window.verify(altered)
    rows = {r['id']: r for r in extract(base)['records']}
    assert rows['item.tool.000.description']['max_encoded_bytes'] + 4 == 99
    assert rows['item.tool.032.description']['max_encoded_bytes'] + 4 + 3 + 13 == 99
    assert rows['ui.items.1179fc']['max_encoded_bytes'] == 13
