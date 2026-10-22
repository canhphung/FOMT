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
    assert len(catalog["records"]) == 9069
    for row in catalog["records"]:
        assert encode(row["original_english"]) == bytes.fromhex(row["original_bytes"])


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
    for name in ("pilot.json","items.json"):
        merged["records"].extend(json.loads((ROOT/"localization/vi"/name).read_text())["records"])
    _, report = build(real_rom,merged)
    assert report["translated_records"] == 385
    assert len({r["id"] for r in merged["records"]}) == 385


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
