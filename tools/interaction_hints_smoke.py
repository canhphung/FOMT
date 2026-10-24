#!/usr/bin/env python3
"""Source-guarded bed/shipment instructions in isolated native dialogue fixtures."""
import argparse
import hashlib
import json
import re
from pathlib import Path

from fomt_text import FormatError, ROM_BASE, SCRIPT_TABLE, decode, parse_script, u32, verified_rom
from intro_smoke import probe_lines, text_ranges, widgets
from mgba_session import Session
from npc_context import instructions
from object_labels_smoke import cache_pixels, expected_pixels
from object_text import verify as verify_handlers

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'localization/qa/batches/interaction-hints-01.json'


def verify(base, target=None):
    base = bytes(base)
    # Reuse the existing native-handler/jump-slot guards; this batch is separate
    # from the short noun labels and does not change their coverage claims.
    verify_handlers(base)
    batch = json.loads(BATCH.read_text())
    assert batch['record_ids'] == [p['id'] for p in batch['source_proofs']]
    for proof in batch['source_proofs']:
        sid, index = proof['script_id'], proof['string_index']
        source = parse_script(base, u32(base, SCRIPT_TABLE+sid*4)-ROM_BASE)
        code = dict(source['chunks'])[b'CODE'][4:]
        if hashlib.sha256(code).hexdigest() != proof['code_sha256'] or decode(source['strings'][index]['raw']) != proof['original_english']:
            raise FormatError('interaction hint source mismatch: '+proof['id'])
        ins = list(instructions(code))
        sites = [{'code_offset':pc, 'native_call':arg, 'text_flags':{33:256,34:64,35:0}[arg]}
                 for j,(pc,op,arg) in enumerate(ins) if op == 0x21 and arg in (33,34,35)
                 and j and ins[j-1][1] in (0x17,0x22,0x23) and ins[j-1][2] == index]
        if not sites or sites != proof['show_text_sites']:
            raise FormatError('interaction hint display site mismatch')
        if target is not None:
            inserted = parse_script(target, u32(target, SCRIPT_TABLE+sid*4)-ROM_BASE)
            assert len(source['strings']) == len(inserted['strings'])
            for tag in (b'CODE', b'JUMP'):
                assert dict(source['chunks']).get(tag) == dict(inserted['chunks']).get(tag)
            for a,b in zip(source['strings'],inserted['strings']):
                if a['index'] != index:
                    assert a['raw'] == b['raw'], 'unselected sleep menu changed'
    return batch


def run(args):
    base = verified_rom(args.base_rom)
    target = args.rom.read_bytes()
    batch = verify(base, target)
    translations = {r['id']:r for r in json.loads((ROOT/'localization/vi/pilot.json').read_text())['records']}
    rows = [translations[i] for i in batch['record_ids']]
    proofs = {r['id']:r for r in batch['source_proofs']}
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    session = Session(args.rom,args.library)
    try:
        session.frames(360)
        renderer = probe_lines(session,rows)
        sram = args.sram.read_bytes()
        session.load_sram(sram)
        session.lib.session_reset(session.handle)
        session.frames(360)
        for key,settle in ((8,180),(8,360),(1,360),(1,360)):
            session.press(key,settle=settle)
        session.press(1,settle=150)  # Natural round-table widget, fixture host only.
        active = [w for w in widgets(session) if w[1] == 5]
        assert len(active) == 1
        root,_,_,data = active[0]
        context = u32(data,0xF8)
        initial = session.state()
        cases = []
        for begin,end,row,payload in text_ranges(target,rows):
            session.restore(initial)
            before = session.read(0x02000000,0x40000)
            session.write(0x04000208,b'\0\0')
            flags = proofs[row['id']]['show_text_sites'][0]['text_flags']
            session.call(0x08050425,root,begin,flags,context)
            session.call(0x08050B3D,root)
            session.call(0x08050C19,root)
            after = session.read(0x02000000,0x40000)
            session.restore(initial)
            i = 0
            while i < len(after):
                if before[i] == after[i] or 0x3F000 <= i < 0x3F004:
                    i += 1
                    continue
                start = i
                while i < len(after) and before[i] != after[i] and not 0x3F000 <= i < 0x3F004:
                    i += 1
                session.write(0x02000000+start,after[start:i])
            assert not cache_pixels(session,root)
            expected_waits = [i+1 for i,b in enumerate(payload) if b == 5]
            captures = []
            for page,offset in enumerate(expected_waits):
                for _ in range(200):
                    session.frames(4)
                    current = next(w for w in widgets(session) if w[0] == root)
                    if current[1] == 5 and current[2] == begin+offset:
                        break
                else:
                    raise AssertionError((row['id'],'WAIT not reached',offset))
                # First page is three rows. Later WAIT follows one native scroll;
                # verify its new text appears intact in one cache row as well.
                lines = row['vietnamese_translation'].split('{WAIT}')[0].split('{CR}{LF}')
                actual = cache_pixels(session,root)
                if page == 0:
                    expected = set().union(*( {(x,y+n*16) for x,y in expected_pixels(base,line)} for n,line in enumerate(lines)))
                    assert actual == expected, (row['id'],'first-page foreground mismatch')
                else:
                    last = re.split(r'\{CR\}\{LF\}',row['vietnamese_translation'])[-1].removesuffix('{WAIT}')
                    mask = expected_pixels(base,last)
                    assert any({(x,y-n*16) for x,y in actual if n*16 <= y < (n+1)*16} == mask for n in range(3)), 'payment line clipped'
                name = f"{row['id']}-wait-{page+1}.png"
                session.screenshot(out/name)
                captures.append(name)
                if page+1 < len(expected_waits):
                    session.press(1,settle=1)
            cases.append({'id':row['id'],'wait_offsets_verified':expected_waits,'native_flags':flags,'screenshots':captures,'foreground_masks_verified':True})
        assert session.sram() == sram
        assert session.lib.session_errors() == 0
        return {'status':'passed','target_sha256':hashlib.sha256(target).hexdigest(),
                'cases':cases,'guarded_renderer_lines':renderer,'native_waits_verified':sum(len(c['wait_offsets_verified']) for c in cases),
                'source_CODE_JUMP_and_unselected_strings_unchanged':True,'sram_unchanged':True,'emulator_error_count':0,
                'limitations':['Native UI fixtures hosted in the starting house; not natural bed/shipment encounters.',
                               'Sleep choices, unknown RAW:81A8 label and manual language/layout review outside this batch.']}
    finally:
        session.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--base-rom',required=True,type=Path)
    p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'))
    p.add_argument('--output-dir',type=Path,default=Path('build/interaction-hints'))
    args = p.parse_args()
    if any(f.resolve().is_relative_to(args.output_dir.resolve()) for f in (args.rom,args.base_rom,args.library,args.sram)):
        p.error('inputs must be outside output-dir')
    report = run(args)
    (args.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__ == '__main__':
    main()
