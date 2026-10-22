"""Verified A4NE revision 0 structures; ROMs are supplied locally, never fetched."""
from __future__ import annotations

import hashlib
import re
import struct
import unicodedata
from collections import Counter
from pathlib import Path

ROM_BASE = 0x08000000
ROM_SIZE = 0x800000
ROM_SHA1 = "a2fc3574f0a65a4fcf7682fb274b9d7eebdef963"
SCRIPT_TABLE = 0xF89D4
SCRIPT_COUNT = 1329  # includes null entry 0; incbin length 0x14C4
ITEM_TABLES = {"tool": (0xEAB0C, 81, 12, 8),
               "food": (0xEDCD8, 171, 16, 12),
               "article": (0xEFED4, 95, 12, 8)}
MENU_TABLE = 0xF1A34
MENU_NAMES = ("Diary", "Rucksack", "World Map", "Farm Map", "Earnings", "Memo", "Tutorial")
FONT_1BPP = 0x4F90CC
FONT_LOOKUP = 0x4FA7A0
GLYPH_FUNCTION = 0xD0D28
CONTROL = {5: "WAIT", 10: "LF", 12: "PAGE", 13: "CR"}
TOKEN = re.compile(r"\{(?:WAIT|LF|PAGE|CR|VAR:[0-9A-F]{2}|RAW:(?:[0-9A-F]{2})+)\}")


class FormatError(ValueError):
    pass


def u32(data: bytes, off: int) -> int:
    if off < 0 or off + 4 > len(data):
        raise FormatError(f"word out of bounds: {off:#x}")
    return struct.unpack_from("<I", data, off)[0]


def p32(value: int) -> bytes:
    return struct.pack("<I", value)


def offset(pointer: int, size: int) -> int:
    off = pointer - ROM_BASE
    if not 0 <= off < size:
        raise FormatError(f"invalid ROM pointer {pointer:#x}")
    return off


def verified_rom(path: str | Path) -> bytes:
    data = Path(path).read_bytes()
    if len(data) != ROM_SIZE or hashlib.sha1(data).hexdigest() != ROM_SHA1:
        raise FormatError("Requires unmodified Harvest Moon FOMT USA rev 0, SHA1 " + ROM_SHA1)
    return data


def cstring(data: bytes, start: int, end: int) -> bytes:
    if not 0 <= start < end <= len(data):
        raise FormatError("string bounds invalid")
    stop = data.find(b"\0", start, end)
    if stop < 0:
        raise FormatError(f"unterminated string at {start:#x}")
    return data[start:stop]


def decode(data: bytes) -> str:
    """Lossless markup: never misinterpret FF expansion bytes as CP932 PUA."""
    out = []
    i = 0
    while i < len(data):
        b = data[i]
        if b in CONTROL:
            out.append("{" + CONTROL[b] + "}")
        elif b == 0xFF:
            if i + 1 == len(data):
                raise FormatError("truncated FF expansion")
            i += 1
            out.append(f"{{VAR:{data[i]:02X}}}")
        elif 0x20 <= b <= 0x7E and chr(b) not in "{}":
            out.append(chr(b))
        elif (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC) and i + 1 < len(data):
            out.append(f"{{RAW:{b:02X}{data[i+1]:02X}}}")
            i += 1
        else:
            out.append(f"{{RAW:{b:02X}}}")
        i += 1
    return "".join(out)


def vietnamese_chars() -> str:
    chars = set("Đđ")
    for code in list(range(0xC0, 0x200)) + list(range(0x1EA0, 0x1EFA)):
        c = chr(code)
        nfd = unicodedata.normalize("NFD", c)
        if nfd[0] in "AaEeIiOoUuYy" and len(nfd) > 1 and all(
            x in "\u0300\u0301\u0302\u0303\u0306\u0309\u031b\u0323" for x in nfd[1:]
        ):
            # Restrict to the Vietnamese alphabet: no accented I/U/Y circumflex etc.
            if "\u0302" in nfd and nfd[0].lower() not in "aeo":
                continue
            if "\u0306" in nfd and nfd[0].lower() != "a":
                continue
            if "\u031b" in nfd and nfd[0].lower() not in "ou":
                continue
            chars.add(c)
    return "".join(sorted(chars))


VI_CHARS = vietnamese_chars()
VI_CODES = {c: bytes((0xEB, 0x40 + i)) for i, c in enumerate(VI_CHARS)}


def encode(text: str, vietnamese: bool = False) -> bytes:
    text = unicodedata.normalize("NFC", text)
    out = bytearray()
    i = 0
    inverse = {v: k for k, v in CONTROL.items()}
    while i < len(text):
        if text[i] == "{":
            m = TOKEN.match(text, i)
            if not m:
                raise FormatError(f"invalid token at character {i}")
            token = m[0][1:-1]
            if token in inverse:
                out.append(inverse[token])
            elif token.startswith("VAR:"):
                out.extend((0xFF, int(token[4:], 16)))
            else:
                raw = bytes.fromhex(token[4:])
                if 0 in raw:
                    raise FormatError("embedded terminator")
                out.extend(raw)
            i = m.end()
        else:
            c = text[i]
            if vietnamese and c in VI_CODES:
                out.extend(VI_CODES[c])
            elif 0x20 <= ord(c) <= 0x7E and c not in "{}":
                out.append(ord(c))
            else:
                raise FormatError(f"unsupported character U+{ord(c):04X}")
            i += 1
    return bytes(out)


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text)


def check_translation(original: str, translation: str, max_columns: int) -> dict:
    if tokens(original) != tokens(translation):
        raise FormatError("control/variable/RAW tokens must be preserved in exactly the same order")
    encoded = encode(translation, vietnamese=True)
    x = maximum = 0
    i = 0
    dynamic = False
    # Simulate CR and LF independently; WAIT does not reset the cursor.
    while i < len(encoded):
        c = encoded[i]
        if c in (12, 13):
            x = 0
        elif c == 0xFF:
            x += 12  # conservative reserve; identity of most variables still unverified
            dynamic = True
            i += 1
        elif c in (5, 10):
            pass
        elif c == 0xEB:
            x += 1
            i += 1
        elif 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
            x += 2
            i += 1
        else:
            x += 1
        maximum = max(maximum, x)
        i += 1
    if maximum > max_columns:
        raise FormatError(f"line width {maximum} tiles exceeds budget {max_columns}")
    return {"maximum_tiles": maximum, "dynamic_variable_reserve": dynamic,
            "vertical_layout": "requires_runtime_review"}


def parse_script(data: bytes, start: int) -> dict:
    if data[start:start+4] != b"RIFF" or data[start+8:start+12] != b"SCR ":
        raise FormatError(f"not SCR at {start:#x}")
    # This game stores TOTAL bytes in RIFF.length, unlike standard RIFF size-8.
    length = u32(data, start+4)
    end = start + length
    if length < 12 or end > len(data):
        raise FormatError("invalid SCR length")
    chunks = []
    entries = []
    pos = start + 12
    while pos < end:
        if pos + 8 > end:
            raise FormatError("truncated chunk header")
        tag = data[pos:pos+4]
        size = u32(data, pos+4)
        if tag not in (b"CODE", b"STR ", b"JUMP") or pos+8+size > end:
            raise FormatError(f"invalid SCR chunk at {pos:#x}")
        payload = data[pos+8:pos+8+size]
        chunks.append((tag, payload))
        if tag == b"CODE" and (size < 4 or u32(payload, 0) != size-4):
            raise FormatError("invalid CODE size")
        if tag == b"STR ":
            count = u32(payload, 0)
            if 4 + count*4 > size:
                raise FormatError("invalid STR count")
            pool = pos + 12 + count*4
            for index in range(count):
                slot = pos + 12 + index*4
                address = pool + u32(data, slot)
                raw = cstring(data, address, pos+8+size)
                entries.append({"index": index, "address": address, "slot": slot,
                                "pool": pool, "raw": raw})
        pos += 8 + size  # no RIFF even-byte padding between these chunks
    if sum(tag == b"STR " for tag, _ in chunks) != 1 or sum(tag == b"CODE" for tag, _ in chunks) != 1:
        raise FormatError("expected exactly one CODE and one STR chunk")
    return {"address": start, "length": length, "chunks": chunks, "strings": entries}


def rebuild_script(script: dict, replacements: dict[int, bytes]) -> bytes:
    if not replacements:
        return b"RIFF" + p32(script["length"]) + b"SCR " + b"".join(
            tag + p32(len(payload)) + payload for tag, payload in script["chunks"])
    out = bytearray(b"RIFF\0\0\0\0SCR ")
    for tag, payload in script["chunks"]:
        if tag == b"STR ":
            pool = bytearray()
            offsets = []
            for entry in script["strings"]:
                offsets.append(len(pool))
                pool.extend(replacements.get(entry["index"], entry["raw"]) + b"\0")
            payload = p32(len(offsets)) + b"".join(p32(x) for x in offsets) + pool
        out.extend(tag + p32(len(payload)) + payload)
    out[4:8] = p32(len(out))
    return bytes(out)


def make_record(identifier: str, raw: bytes, address: int, context: str,
                source: dict, columns: int, speaker: str | None = None) -> dict:
    original = decode(raw)
    if encode(original) != raw:
        raise FormatError("lossless codec check failed")
    return {"id": identifier, "rom_address": f"0x{address+ROM_BASE:08X}",
            "rom_offset": f"0x{address:06X}", "original_english": original,
            "vietnamese_translation": "", "context": context, "speaker": speaker,
            "control_codes": tokens(original), "translation_status": "untranslated",
            "original_bytes": raw.hex(), "source": source, "max_columns": columns,
            "layout_budget": "conservative; runtime review required"}


def extract(data: bytes) -> dict:
    records = []
    for kind, (table, count, stride, desc) in ITEM_TABLES.items():
        for index in range(count):
            for field, delta, columns in (("name", 0, 20), ("description", desc, 28)):
                slot = table + index*stride + delta
                address = offset(u32(data, slot), len(data))
                raw = cstring(data, address, min(address+4096, len(data)))
                records.append(make_record(f"item.{kind}.{index:03d}.{field}", raw, address,
                    f"item_{field}", {"kind": "pointer", "pointer_offsets": [slot],
                    "reference": f"StanHash/fomt data/item/{kind}.def; tools/scripts/dump_item_tables.py"}, columns))
    for index, expected in enumerate(MENU_NAMES):
        slot = MENU_TABLE + index*4
        address = offset(u32(data, slot), len(data))
        raw = cstring(data, address, address+64)
        if raw.decode("ascii") != expected:
            raise FormatError("pause menu identity check failed")
        records.append(make_record(f"menu.pause.{index}", raw, address, "pause_menu_label",
            {"kind": "pointer", "pointer_offsets": [slot],
             "reference": "asm/code_0803A8A4.s; literal 0x0803C0C4 -> table 0x080F1A34"}, 12))
    for index in range(1, SCRIPT_COUNT):
        slot = SCRIPT_TABLE + index*4
        address = offset(u32(data, slot), len(data))
        script = parse_script(data, address)
        for ent in script["strings"]:
            context = "script_string_unclassified"
            speaker = None
            if index == 993 and ent["index"] == 0:
                context, speaker = "npc_greeting_self_introduction", "Popuri"
            records.append(make_record(f"script.{index:04d}.{ent['index']:03d}", ent["raw"],
                ent["address"], context,
                {"kind": "script", "script_id": index, "string_index": ent["index"],
                 "script_offset": address, "script_pointer_offset": slot,
                 "relative_offset_slot": ent["slot"], "pool_offset": ent["pool"],
                 "reference": "src/script_engine.cc AScriptEngine::Load/GetString; ScriptEngine::LoadById"}, 28, speaker))
    from new_game_ui import extract_records
    records.extend(extract_records(data))
    from intro_text import extract_records as intro_records, annotate_scripts
    annotate_scripts(records)
    records.extend(intro_records(data))
    from start_menu import extract_records as start_records
    records.extend(start_records(data))
    return {"schema_version": 1, "rom": {"sha1": ROM_SHA1,
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "game_code": data[0xAC:0xB0].decode("ascii"), "revision": data[0xBC]},
            "reference_commit": "b8471ae065744869f64283473ed68372f82321c9",
            "statistics": dict(Counter(r["context"] for r in records)), "records": records}
