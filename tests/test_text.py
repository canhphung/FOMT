import copy
import hashlib
import json
import os
import struct
from pathlib import Path

import pytest
import ips
from fomt_text import (FormatError, ROM_SHA1, VI_CHARS, VI_CODES, check_translation,
    decode, encode, extract, p32, parse_script, rebuild_script, verified_rom)
from text_inserter import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("raw", [b"Hello!", b"\xff!\r\nHi\x05\x0c",
    b"\x81\x40\xb1\x7b\x7d", b"\x01\x02\x80", b"\xff\x00"])
def test_lossless_markup(raw):
    assert encode(decode(raw)) == raw


@pytest.mark.parametrize("text", ["{VAR:FF", "{RAW:00}", "{UNKNOWN}", "emoji: 😊", "\n"])
def test_bad_markup_and_unencodable_characters_rejected(text):
    with pytest.raises(FormatError):
        encode(text, vietnamese=True)


def test_truncated_expansion_rejected():
    with pytest.raises(FormatError):
        decode(b"oops\xff")


def test_complete_vietnamese_alphabet():
    assert len(VI_CHARS) == len(set(VI_CODES.values())) == 134
    assert all(c in VI_CODES for c in "ẮằẲẵẶậỄệỈịỚờỞỡỢựĐđỸỹ")
    assert encode("Việt", True) == encode("Vie\u0323\u0302t", True)
    assert len(encode("ệ", True)) == 2


def test_control_and_placeholder_integrity():
    for vi in ["Chào{PAGE}", "Chào{VAR:22}{WAIT}", "Chào{WAIT}{VAR:21}"]:
        with pytest.raises(FormatError):
            check_translation("Hello{VAR:21}{WAIT}", vi, 28)


def test_raw_symbol_must_be_preserved():
    with pytest.raises(FormatError):
        check_translation("Hello{RAW:8140}", "Chào", 28)


def test_width_reserves_variables_and_lf_does_not_reset_x():
    with pytest.raises(FormatError):
        check_translation("A{LF}B", "A"*20+"{LF}"+"B"*10, 28)
    with pytest.raises(FormatError):
        check_translation("{VAR:21}", "A"*20+"{VAR:21}", 28)
    assert check_translation("A{CR}{LF}B", "A"*28+"{CR}{LF}"+"B"*28, 28)["maximum_tiles"] == 28


def sample_script():
    # Synthetic VM fixture, not claimed to be original game dialogue.
    code = p32(1)+b"\x20"
    strings = p32(2)+p32(0)+p32(2)+b"A\0B\0"
    jump = p32(0)
    body = b"SCR "+b"CODE"+p32(len(code))+code+b"JUMP"+p32(4)+jump+b"STR "+p32(len(strings))+strings
    return b"RIFF"+p32(8+len(body))+body


def test_game_riff_total_length_and_unaligned_chunks():
    data = sample_script()
    script = parse_script(data, 0)
    assert script["length"] == len(data)
    assert rebuild_script(script, {}) == data
    assert [e["raw"] for e in script["strings"]] == [b"A", b"B"]
    rebuilt = rebuild_script(script, {0: encode("Việt", True)})
    out = parse_script(rebuilt, 0)
    assert out["strings"][1]["raw"] == b"B"
    assert out["chunks"][:2] == script["chunks"][:2]


@pytest.mark.parametrize("mutate", [lambda b:b[:9], lambda b:b[:4]+p32(0xFFFFFFFF)+b[8:],
    lambda b:b.replace(b"STR ",b"BAD "), lambda b:b[:-1]])
def test_malformed_riff_rejected(mutate):
    with pytest.raises(FormatError):
        parse_script(mutate(sample_script()), 0)


@pytest.mark.parametrize("source,target", [(b"abc",b"abc"),(b"abc",b"xyzabc"),
    (b"abcdef",b"x"),(b"",b"\xff"*100000),(b"\0"*32,b"\xff"*32)])
def test_ips_round_trip(source,target):
    assert ips.apply(source, ips.create(source,target)) == target


def test_ips_16mib_and_reserved_eof_address():
    base = b"\0"*0x800000
    target = bytearray(base+b"\xff"*0x800000)
    target[0x454F46] = 1
    patch = ips.create(base, bytes(target))
    assert ips.apply(base,patch) == bytes(target)


@pytest.mark.parametrize("patch", [b"",b"PATCH",b"PATCH\0",b"PATCH\0\0\0\0\x04x",b"PATCHEOFjunk"])
def test_malformed_ips_rejected(patch):
    with pytest.raises(FormatError):
        ips.apply(b"",patch)


def test_wrong_base_rom_rejected(tmp_path):
    path = tmp_path/"wrong.gba"
    path.write_bytes(b"not the supported base ROM")
    with pytest.raises(FormatError,match="Requires unmodified"):
        verified_rom(path)


def test_atomic_write_preserves_unrelated_tempfile(tmp_path):
    from text_inserter import atomic_write
    sentinel = tmp_path/"output.bin.tmp"
    sentinel.write_bytes(b"user content")
    atomic_write(tmp_path/"output.bin",b"new data")
    assert sentinel.read_bytes() == b"user content"
    assert (tmp_path/"output.bin").read_bytes() == b"new data"


@pytest.fixture(scope="module")
def real_rom():
    path = os.environ.get("FOMT_ROM")
    if not path:
        pytest.skip("set FOMT_ROM to legally supplied USA revision 0 ROM")
    return verified_rom(path)


def test_all_actual_strings_round_trip(real_rom):
    catalog = extract(real_rom)
    assert len(catalog["records"]) == 9309
    for row in catalog["records"]:
        if row['source']['kind'] == 'glyph_strip':
            assert struct.pack('<8H', *map(ord,row['original_english'])) == bytes.fromhex(row['original_bytes'])
        else:
            assert encode(row["original_english"]) == bytes.fromhex(row["original_bytes"])


def new_game_translations():
    return json.loads((ROOT/'localization/vi/new_game.json').read_text())


def test_new_game_sources_and_atlas_dimensions(real_rom):
    import new_game_ui as ui
    rows = ui.extract_records(real_rom)
    assert len(rows) == 24 and len({r['id'] for r in rows}) == 24
    texts = {r['id']:r['vietnamese_translation'] for r in new_game_translations()['records']}
    atlas = ui.build_atlas(real_rom,texts)
    assert len(atlas) == 43*64
    assert atlas[:640] == b''.join(ui.strip(real_rom,str(i),8) for i in range(10))
    assert atlas[35*64:] == ui.strip(real_rom,'Sinh nhật',64,advance=7)
    import unicodedata
    assert ui.build_atlas(real_rom,{k:unicodedata.normalize('NFD',v) for k,v in texts.items()}) == atlas
    assert ui.summary_blank_patch(real_rom,texts) == bytes.fromhex('6d21')


@pytest.mark.parametrize('site',[0x4EE8,0xFBD30,0x6E3BC])
def test_new_game_rejects_unverified_pointer_atlas_or_call_site(real_rom,site):
    import new_game_ui as ui
    damaged = bytearray(real_rom)
    damaged[site] ^= 1
    with pytest.raises(FormatError):ui.extract_records(damaged)


def test_new_game_build_repoints_labels_preserves_keyboard_and_fixed_row_bounds(real_rom):
    import new_game_ui as ui
    trans = new_game_translations()
    out,report = build(real_rom,trans)
    assert report['translated_records'] == 24
    assert report['new_game_birthday_atlas']['glyphs'] == 43
    assert report['new_game_birthday_atlas']['vram_allocation_changed'] is False
    originals = {r['id']:r for r in ui.extract_records(real_rom)}
    for row in trans['records']:
        src = originals[row['id']]['source']
        payload = encode(row['vietnamese_translation'],True)+b'\0'
        if src['kind'] == 'pointer':
            for slot in src['pointer_offsets']:
                at = struct.unpack_from('<I',out,slot)[0]-0x08000000
                assert at >= len(real_rom) and at%4 == 0
                assert out[at:at+len(payload)] == payload
        elif src['kind'] == 'fixed_cstring':
            assert out[src['offset']:src['offset']+7] == payload.ljust(7,b'\0')
    assert out[ui.SEASON_TABLE-2:ui.SEASON_TABLE] == real_rom[ui.SEASON_TABLE-2:ui.SEASON_TABLE]
    assert out[ui.SEASON_TABLE+28:ui.SEASON_TABLE+32] == real_rom[ui.SEASON_TABLE+28:ui.SEASON_TABLE+32]
    # Original keyboard character tables, used to enter/save names, stay intact.
    assert out[0xE89AC:0xE8BF4] == real_rom[0xE89AC:0xE8BF4]
    assert out[ui.GLYPH_TABLE:ui.GLYPH_TABLE+86] == real_rom[ui.GLYPH_TABLE:ui.GLYPH_TABLE+86]
    assert out[ui.SUMMARY_BLANK_SITE:ui.SUMMARY_BLANK_SITE+2] == bytes.fromhex('6d21')


@pytest.mark.parametrize('identifier,text,reason',[
    ('ui.newgame.summary.confirm','ạ'*20,'encoded-byte limit'),
    ('ui.newgame.season.spring','đ'*6,'fixed string row'),
    ('ui.newgame.summary.player','ABCDEFGHIJKLMN','column 13 blank'),
])
def test_new_game_storage_and_blank_tile_constraints(real_rom,identifier,text,reason):
    trans = new_game_translations()
    row = next(r for r in trans['records'] if r['id'] == identifier)
    row['vietnamese_translation'] = text
    # Tampered client budget fields must not bypass verified-source constraints.
    row['max_encoded_bytes'] = 9999
    row['max_columns'] = 9999
    with pytest.raises(FormatError,match=reason):build(real_rom,trans)


def test_font_distinguishes_all_134_characters(real_rom):
    from vietnamese_font import glyph
    bitmaps = [glyph(real_rom,c) for c in VI_CHARS]
    assert len(set(bitmaps)) == 134  # in particular Ô/ô and Ớ/ớ must differ
    assert all(len(b) == 16 and any(b) for b in bitmaps)


def test_ascii_bodies_keep_original_outlines_and_horizontal_bearings(real_rom):
    from vietnamese_font import ascii_glyph, BODY_Y
    for code in range(32,127):
        index = struct.unpack_from("<h",real_rom,0x4FA7A0+code*2)[0]
        native = real_rom[0x4F90CC+12*index:0x4F90CC+12*(index+1)]
        mask = ascii_glyph(real_rom,chr(code))
        assert mask[:BODY_Y] == bytes(BODY_Y)
        assert mask[BODY_Y:] == native


def test_vietnamese_bodies_have_native_baseline_and_bearings(real_rom):
    import unicodedata
    from vietnamese_font import glyph, ascii_glyph, BODY_Y
    for ch in VI_CHARS:
        nfd = unicodedata.normalize("NFD",ch)
        base = {"Đ":"D","đ":"d"}.get(ch,nfd[0])
        native = ascii_glyph(real_rom,base)
        actual = glyph(real_rom,ch)
        occupied = [y for y,row in enumerate(native) if row]
        first,last = min(occupied),max(occupied)
        if base == "i":
            first = BODY_Y+3  # compare the stem, independently of replacement tone/dot
        for y in range(first,last+1):
            expected = native[y]
            if ch == "Đ" and y == BODY_Y+5:
                expected |= 0xF0
            elif ch == "đ" and y == BODY_Y+2:
                expected |= 0x1E
            elif "\u031b" in nfd and y == first:
                expected |= 0x04  # horn attachment, not a shifted/redrawn body
            assert actual[y] == expected, f"{ch}: native body changed at row {y}"


def test_i_dot_and_d_ascenders_are_not_truncated(real_rom):
    from vietnamese_font import glyph, ascii_glyph, BODY_Y
    assert glyph(real_rom,"ị")[BODY_Y+1] == ascii_glyph(real_rom,"i")[BODY_Y+1] != 0
    for ch,base in [("Đ","D"),("đ","d")]:
        for y,row in enumerate(ascii_glyph(real_rom,base)):
            assert glyph(real_rom,ch)[y] & row == row


def test_cached_glyphs_keep_four_tile_stride_and_foreground(real_rom):
    from vietnamese_font import build_glyphs,ascii_glyph,glyph
    cached = build_glyphs(real_rom)
    masks = [ascii_glyph(real_rom,chr(c)) for c in range(32,127)]+[glyph(real_rom,c) for c in VI_CHARS]
    assert len(cached) == 229*128
    for i,mask in enumerate(masks):
        data = cached[i*128:(i+1)*128]
        foreground = set()
        for y in range(16):
            for x in range(16):
                v = data[(y//8*2+x//8)*32+y%8*4+x%8//2] >> (x%2*4) & 15
                assert v in (0,1,2)
                if v == 1:
                    foreground.add((x,y))
        assert foreground == {(x+1,y) for y,row in enumerate(mask) for x in range(8) if row & (128>>x)}


def test_wrong_font_mask_height_rejected():
    from vietnamese_font import render_staging
    with pytest.raises(FormatError):
        render_staging(bytes(12))


def test_expanded_translation_set_builds_without_overlap(real_rom):
    merged = {"rom_sha1":ROM_SHA1,"records":[]}
    for name in ("pilot.json","items.json","new_game.json","intro.json","start_menu.json","item_descriptions_tools.json","signs.json"):
        merged["records"].extend(json.loads((ROOT/"localization/vi"/name).read_text())["records"])
    _, report = build(real_rom,merged)
    assert report["translated_records"] == 1566
    assert len({r["id"] for r in merged["records"]}) == 1566


@pytest.mark.parametrize('site',[0x5F78C,0x5F958,0x50B50])
def test_intro_source_literal_or_name_prologue_mutations_rejected(real_rom,site):
    import intro_text
    bad = bytearray(real_rom)
    bad[site] ^= 1
    with pytest.raises(FormatError):intro_text.extract_records(bad)


def test_intro_reinsert_preserves_every_script_instruction_and_unrelated_literal(real_rom):
    import intro_text
    trans = json.loads((ROOT/'localization/vi/intro.json').read_text())
    assert len(trans['records']) == 145
    out,report = build(real_rom,trans)
    assert report['translated_records'] == 145
    cache = report['intro_speaker_cache']
    assert len(cache['entries']) == 5 and cache['vram_allocation_changed'] is False
    assert cache['cache_size_per_name'] == 768
    originals = {r['id']:r for r in extract(real_rom)['records']}
    checked = set()
    for row in trans['records']:
        original = originals[row['id']]
        src = original['source']
        payload = encode(row['vietnamese_translation'],True)
        if src['kind'] == 'pointer':
            for slot in src['pointer_offsets']:
                address = struct.unpack_from('<I',out,slot)[0]-0x08000000
                assert address >= len(real_rom) and address%4 == 0
                assert out[address:address+len(payload)+1] == payload+b'\0'
            assert out[int(original['rom_offset'],16):int(original['rom_offset'],16)+len(bytes.fromhex(original['original_bytes']))] == bytes.fromhex(original['original_bytes'])
        else:
            address = struct.unpack_from('<I',out,src['script_pointer_offset'])[0]-0x08000000
            rebuilt = parse_script(out,address)
            assert rebuilt['strings'][src['string_index']]['raw'] == payload
            if src['script_id'] not in checked:
                old = parse_script(real_rom,src['script_offset'])
                assert [(t,p) for t,p in old['chunks'] if t!=b'STR '] == [(t,p) for t,p in rebuilt['chunks'] if t!=b'STR ']
                checked.add(src['script_id'])
    assert checked == set(intro_text.SCRIPT_IDS)


def test_intro_four_choice_limit_counts_bytes_and_cannot_be_overridden(real_rom):
    trans = json.loads((ROOT/'localization/vi/intro.json').read_text())
    row = next(r for r in trans['records'] if r['id']=='script.0737.007')
    row['vietnamese_translation'] = 'Mẹo hữu ích'  # fits cells, exceeds native strlen limit
    row['max_encoded_bytes'] = 999
    with pytest.raises(FormatError,match='encoded-byte limit'):build(real_rom,trans)


def test_exported_font_table_matches_build(real_rom):
    from vietnamese_font import glyph, encoding_table
    export = json.loads((ROOT/"localization/font/encoding.json").read_text())
    assert export == encoding_table(real_rom)
    assert len(export["characters"]) == 134
    for row in export["characters"]:
        assert bytes.fromhex(row["code"]) == VI_CODES[row["character"]]
        assert bytes.fromhex(row["bitmap_hex"]) == glyph(real_rom,row["character"])


def test_translator_offsets_are_not_trusted(real_rom):
    trans = json.loads((ROOT/"localization/vi/pilot.json").read_text())
    first = copy.deepcopy(trans["records"][0])
    first["source"] = {"kind":"pointer","pointer_offsets":[0]}
    first["rom_offset"] = "0x000000"
    first["original_bytes"] = "00"
    out,report = build(real_rom,{"rom_sha1":ROM_SHA1,"records":[first]})
    assert out[:0xC0] == real_rom[:0xC0]
    assert any(w["offset"] == 0xF1A34 for w in report["writes"])


def test_actual_pilot_build_and_write_whitelist(real_rom):
    trans = json.loads((ROOT/"localization/vi/pilot.json").read_text())
    out,report = build(real_rom,trans)
    assert len(out) == 0x1000000
    assert report["translated_records"] == len(trans["records"])
    mask = bytearray(len(real_rom))
    for w in report["writes"]:
        mask[w["offset"]:w["offset"]+w["size"]] = b"\1"*w["size"]
    assert all(a == b or mask[i] for i,(a,b) in enumerate(zip(real_rom,out)))
    assert hashlib.sha1(real_rom).hexdigest() == ROM_SHA1
    assert ips.apply(real_rom,ips.create(real_rom,out)) == out


def test_stale_source_and_unknown_ids_rejected(real_rom):
    trans = json.loads((ROOT/"localization/vi/pilot.json").read_text())
    one = {**trans,"records":[copy.deepcopy(trans["records"][0])]}
    one["records"][0]["original_english"] = "not original"
    with pytest.raises(FormatError,match="stale"):
        build(real_rom,one)
    one["records"][0]["id"] = "not.a.real.id"
    with pytest.raises(FormatError,match="unknown"):
        build(real_rom,one)


def test_duplicate_translation_ids_rejected(real_rom):
    trans = json.loads((ROOT/"localization/vi/pilot.json").read_text())
    trans["records"] = [trans["records"][0]]*2
    with pytest.raises(FormatError,match="duplicate"):
        build(real_rom,trans)


def test_unclassified_script_cannot_be_silently_translated(real_rom):
    original = next(r for r in extract(real_rom)["records"] if r["id"] == "script.0002.000")
    original.update(vietnamese_translation="Đã khỏi bệnh!{WAIT}",translation_status="translated")
    with pytest.raises(FormatError,match="unclassified"):
        build(real_rom,{"rom_sha1":ROM_SHA1,"records":[original]})


def test_title_asset_preserves_unrelated_data_and_reallocates_safely(real_rom):
    import title_graphics as t
    packed, report = t.localize(real_rom)
    before = t.unpack(real_rom[t.ASSET_OFFSET:t.ASSET_OFFSET+t.ASSET_SIZE])
    after = t.unpack(packed)
    assert len(after) == 20556 < 0x6A00
    assert after[:0x28] == before[:0x28]  # animation index table
    assert after[0x240:0x240+474*32] == before[0x240:t.TILE_OFFSET]  # logo
    assert after[0x240+542*32:0x240+543*32] == before[0x41C0:0x41E0]  # arrow
    assert after[0x240+543*32:0x4DA0] == before[0x41E0:0x4960]  # copyright
    assert after[0x4DA0:] == before[0x4960:]  # palettes and animation commands
    assert [r['vietnamese_translation'] for r in report['labels']] == ['Bắt đầu','Tiếp tục']
    assert 864+28 <= 896 and 896+41 <= 960 and 960+60 <= 1024
    for row in report['labels']:
        width,height = row['dimensions']
        widths = (32,16,8) if width == 56 else (32,32,16)
        at = row['decoded_tile_offset']
        data = after[at:at+row['tile_bytes']]
        # Independent inverse of OAM segments catches tile-row/stride mistakes.
        pixels = [[] for _ in range(height)]
        off = 0
        for segment in widths:
            for y in range(height):
                for x in range(segment):
                    b = data[off+((y//8)*(segment//8)+x//8)*32+y%8*4+(x%8)//2]
                    pixels[y].append((b >> (x%2*4)) & 15)
            off += segment*height//2
        assert pixels == t.title_pixels(row['id'])
    # Object count and all unmodified scene objects are preserved.
    assert after[0xC8:0xCC] == before[0xC8:0xCC]
    assert after[0xCC:0xCC+17*8] == before[0xCC:0xCC+17*8]
    assert after[0xCC+38*8:0x23C] == before[0xCC+38*8:0x23C]


@pytest.mark.parametrize('identifier',['title.start','title.continue'])
def test_title_has_complete_black_white_green_layers(identifier):
    import title_graphics as t
    path = t.ART_PATH if identifier == 'title.start' else t.CONTINUE_ART_PATH
    rows = json.loads(path.read_text())['stroke_mask']
    pixels = t.title_pixels(identifier)
    ink = {(x,y) for y,r in enumerate(rows) for x,c in enumerate(r) if c == '#'}
    assert {(x,y) for y,r in enumerate(pixels) for x,c in enumerate(r) if c == 3} == ink
    assert set(c for row in pixels for c in row) == {0,3,13,14}
    # Each stroke has a light neighbor and a separate outer dark neighbor,
    # including above stacked accents and below the dot of ụ.
    for x,y in ink:
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            if (x+dx,y+dy) not in ink:
                assert pixels[y+dy][x+dx] == 13
    assert min(y for x,y in ink) >= 2 and max(y for x,y in ink) <= 29


def test_title_source_mismatch_rejected(real_rom):
    import title_graphics as t
    for at in (t.ASSET_OFFSET,t.POINTER_OFFSET):
        wrong = bytearray(real_rom)
        wrong[at] ^= 1
        with pytest.raises(FormatError,match='title source'):
            t.localize(wrong)


@pytest.mark.parametrize('payload',[bytes(range(256)),b'\xff'*31,b'abcde'])
def test_popuri_literal_word_boundaries(payload):
    from title_graphics import unpack, pack_literal
    assert unpack(pack_literal(payload)) == payload


@pytest.mark.parametrize('payload',[b'',b'\x70\x10\x00\x00',b'\x70\x10\x00\x00\x00\x00\x00\xff'])
def test_popuri_truncation_or_unsupported_mode_rejected(payload):
    from title_graphics import unpack
    with pytest.raises(FormatError):
        unpack(payload)


def test_title_cursor_alignment_uses_visible_black_border():
    from title_cursor import offsets, assemble_hook
    assert offsets() == {'title.start':2,'title.continue':13}
    code = assemble_hook(0x08820000)
    assert len(code) <= 64
    assert code.endswith(p32(0x08002785))


def test_title_cursor_hook_refuses_wrong_instructions(real_rom):
    from title_cursor import verify_site, DRAW_OFFSET
    verify_site(real_rom)
    wrong = bytearray(real_rom)
    wrong[DRAW_OFFSET] ^= 1
    with pytest.raises(FormatError,match='cursor draw instructions'):
        verify_site(wrong)


@pytest.mark.parametrize('site',[0xE8704,0xFD328,0x600A8,0xCB05A,0xCC414,0x7A216])
def test_start_menu_rejects_changed_verified_source(real_rom,site):
    import start_menu
    bad = bytearray(real_rom)
    bad[site] ^= 1
    with pytest.raises(FormatError):start_menu.extract_records(bad)


def test_start_menu_payloads_fit_verified_cell_and_byte_limits(real_rom):
    import start_menu
    rows = json.loads((ROOT/'localization/vi/start_menu.json').read_text())['records']
    source = {r['id']:r for r in start_menu.extract_records(real_rom)}
    assert len(rows) == len(source) == 162
    for row in rows:
        original = source[row['id']]
        result = check_translation(original['original_english'],row['vietnamese_translation'],original['max_columns'])
        assert result['maximum_tiles'] <= original['max_columns']
        assert len(encode(row['vietnamese_translation'],True)) <= original.get('max_encoded_bytes',1000)
    for identifier in ('ui.start.1000b4','ui.start.1000bc'):
        assert source[identifier]['max_columns'] == 8
        assert source[identifier]['max_encoded_bytes'] == 11
