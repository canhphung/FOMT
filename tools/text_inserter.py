#!/usr/bin/env python3
"""Build a Vietnamese test ROM and IPS from verified local inputs, fail closed."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import ips
from fomt_text import (FormatError, GLYPH_FUNCTION, ROM_BASE, ROM_SHA1, VI_CODES,
    check_translation, encode, extract, offset, p32, parse_script, rebuild_script, u32, verified_rom)
from vietnamese_font import (assemble_hook, build_glyphs, trampoline, FONT_REVISION,
    SOURCE_ROWS, BASELINE, ADVANCE_PIXELS, ASCII_COUNT, STAGING_BYTES)
import title_graphics


def build(base: bytes, translations: dict) -> tuple[bytes, dict]:
    catalog = extract(base)  # never trust user-edited offsets or original_bytes
    if translations.get("rom_sha1") != ROM_SHA1:
        raise FormatError("translation catalog targets a different ROM")
    originals = {r["id"]: r for r in catalog["records"]}
    selected = {}
    seen = set()
    layout = {}
    for row in translations["records"]:
        identifier = row["id"]
        if identifier in seen:
            raise FormatError(f"duplicate translation ID {identifier}")
        seen.add(identifier)
        if identifier not in originals:
            raise FormatError(f"unknown translation ID {identifier}")
        if row["translation_status"] not in ("translated", "reviewed"):
            continue
        original = originals[identifier]
        if row.get("original_english") != original["original_english"]:
            raise FormatError(f"stale original for {identifier}")
        if original["context"] == "script_string_unclassified" and not row.get("context_evidence"):
            raise FormatError(f"unclassified string {identifier}: supply verified context evidence")
        if not row["vietnamese_translation"]:
            raise FormatError(f"empty translation for {identifier}")
        try:
            layout[identifier] = check_translation(original["original_english"],
                row["vietnamese_translation"], original["max_columns"])
        except FormatError as exc:
            raise FormatError(f"{identifier}: {exc}") from exc
        selected[identifier] = encode(row["vietnamese_translation"], vietnamese=True)
    if not selected:
        return base, {"translated_records": 0, "size": len(base), "writes": [], "layout": {}}
    result = bytearray(base)
    writes = []
    allocations = []

    def append(data: bytes, purpose: str) -> int:
        while len(result) % 4:
            result.append(0xFF)
        addr = len(result)
        result.extend(data)
        allocations.append({"offset": addr, "size": len(data), "purpose": purpose})
        return addr

    def write(off: int, data: bytes, purpose: str):
        if off < 0 or off+len(data) > len(base):
            raise FormatError("write outside original verified structure")
        if any(off < w["offset"]+w["size"] and w["offset"] < off+len(data) for w in writes):
            raise FormatError("overlapping writes")
        before = bytes(result[off:off+len(data)])
        result[off:off+len(data)] = data
        writes.append({"offset": off, "size": len(data), "purpose": purpose,
                       "before": before.hex(), "after": data.hex()})

    hook_offset = append(b"\xFF"*128, "Vietnamese Thumb hook reservation")
    glyph_offset = append(build_glyphs(base), "229 Latin/Vietnamese glyphs, common baseline, 16x16 4bpp staging")
    hook = assemble_hook(ROM_BASE+hook_offset, ROM_BASE+glyph_offset)
    if len(hook) > 128:
        raise FormatError("hook reservation overflow")
    result[hook_offset:hook_offset+len(hook)] = hook
    expected = bytes.fromhex("70b5041c0a1c0026")
    if base[GLYPH_FUNCTION:GLYPH_FUNCTION+8] != expected:
        raise FormatError("glyph prologue mismatch")
    write(GLYPH_FUNCTION, trampoline(ROM_BASE+hook_offset), "glyph function entry")
    scripts = defaultdict(dict)
    for identifier, payload in selected.items():
        original = originals[identifier]
        src = original["source"]
        if src["kind"] == "pointer":
            at = append(payload+b"\0", identifier)
            for slot in src["pointer_offsets"]:
                if offset(u32(base, slot), len(base)) != int(original["rom_offset"], 16):
                    raise FormatError("pointer identity mismatch")
                write(slot, p32(ROM_BASE+at), identifier+" pointer")
        else:
            scripts[src["script_id"]][src["string_index"]] = payload
    for script_id, replacements in sorted(scripts.items()):
        exemplar = next(r for r in catalog["records"] if r["source"].get("script_id") == script_id)
        src = exemplar["source"]
        old = parse_script(base, src["script_offset"])
        at = append(rebuild_script(old, replacements), f"script {script_id}")
        new = parse_script(bytes(result), at)
        if [(t,p) for t,p in old["chunks"] if t != b"STR "] != [(t,p) for t,p in new["chunks"] if t != b"STR "]:
            raise FormatError("CODE/JUMP changed unexpectedly")
        for ent in new["strings"]:
            expect = replacements.get(ent["index"], old["strings"][ent["index"]]["raw"])
            if ent["raw"] != expect:
                raise FormatError("script reinsertion round trip failed")
        write(src["script_pointer_offset"], p32(ROM_BASE+at), f"script {script_id} pointer")
    title_asset, title_report = title_graphics.localize(base)
    title_offset = append(title_asset, "title sprite asset: Bắt đầu / Tiếp tục")
    write(title_graphics.POINTER_OFFSET, p32(ROM_BASE+title_offset), "title sprite asset pointer")
    title_report["target_offset"] = title_offset
    if len(result) > 0x1000000:
        raise FormatError("build exceeds IPS target limit; use a BPS backend")
    # Conventional 16MiB cartridge image: original 8MiB preserved, new allocations
    # start at 8MiB; no guessed free-space overwrites inside the original ROM.
    result.extend(b"\xFF"*(0x1000000-len(result)))
    mask = bytearray(len(base))
    for w in writes:
        mask[w["offset"]:w["offset"]+w["size"]] = b"\1"*w["size"]
    if any(a != b and not mask[i] for i, (a,b) in enumerate(zip(base, result))):
        raise FormatError("unapproved original ROM modification")
    patched = bytes(result)
    return patched, {"rom_sha1": ROM_SHA1, "target_sha256": hashlib.sha256(patched).hexdigest(),
        "size": len(patched), "translated_records": len(selected), "writes": writes,
        "allocations": allocations, "layout": layout, "font_hook_bytes": hook.hex(),
        "graphics": [title_report],
        "font": {"revision":FONT_REVISION,"source_mask_rows":SOURCE_ROWS,
                 "baseline_row":BASELINE,"advance_pixels":ADVANCE_PIXELS,
                 "ascii_glyphs":ASCII_COUNT,"vietnamese_glyphs":len(VI_CODES),
                 "cache_stride_bytes":STAGING_BYTES,
                 "cache_size":(ASCII_COUNT+len(VI_CODES))*STAGING_BYTES},
        "encoding": {c: b.hex() for c,b in VI_CODES.items()},
        "runtime_status": "requires emulator/hardware validation"}


def atomic_write(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name+".", suffix=".tmp", delete=False) as stream:
            temp = Path(stream.name)
            stream.write(content)
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--translations", type=Path, nargs="+", default=[Path("localization/vi/pilot.json"), Path("localization/vi/items.json")])
    parser.add_argument("--output", type=Path, default=Path("build/fomt-vi-demo.gba"))
    parser.add_argument("--patch", type=Path, default=Path("patches/fomt-vi-demo.ips"))
    parser.add_argument("--report", type=Path, default=Path("build/insertion-report.json"))
    args = parser.parse_args()
    inputs = {args.rom.resolve(), *(p.resolve() for p in args.translations)}
    outputs = [args.output.resolve(), args.patch.resolve(), args.report.resolve()]
    if len(set(outputs)) != 3 or inputs.intersection(outputs):
        parser.error("output, patch and report must be distinct and must not overwrite inputs")
    try:
        base = verified_rom(args.rom)
        merged = {"rom_sha1": ROM_SHA1, "records": []}
        for path in args.translations:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("rom_sha1") != ROM_SHA1:
                raise FormatError(f"{path}: different base ROM")
            merged["records"].extend(data["records"])
        patched, report = build(base, merged)
        patch = ips.create(base, patched)
        if ips.apply(base, patch) != patched:
            raise FormatError("IPS round trip failed")
        atomic_write(args.output, patched)
        atomic_write(args.patch, patch)
        atomic_write(args.report, (json.dumps(report, ensure_ascii=False, indent=2)+"\n").encode())
        print(json.dumps({"translated_records": report["translated_records"], "rom_size": len(patched),
                          "ips_size": len(patch), "target_sha256": report.get("target_sha256")}, ensure_ascii=False))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()
