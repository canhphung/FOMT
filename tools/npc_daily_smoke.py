#!/usr/bin/env python3
"""Native daily-dialogue layout fixtures, not natural NPC encounters.

Boots the normal opening, uses its initialized widget, probes native setters
in isolation, then transfers widget and external tile-cache EWRAM back into the saved CPU state.
Hides the opening portrait so it cannot falsely depict Popuri as Thomas.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from fomt_text import ROM_BASE, encode, u32, verified_rom
from intro_smoke import widgets, text_ranges, probe_lines
from mgba_session import Session
from npc_context import witnesses, branch_matrix


def run(args):
    base=verified_rom(args.base_rom);target=args.rom.read_bytes()
    ids={r['id'] for r in witnesses(base)}
    records=[r for r in json.loads(Path('localization/vi/pilot.json').read_text())['records'] if r['id'] in ids]
    assert len(records)==85
    if args.limit:records=records[:args.limit]
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    session=Session(args.rom,args.library)
    try:
        session.frames(360)
        renderer=probe_lines(session,records)
        session.press(8,settle=120);session.press(8,settle=300)
        for field in ('player','farm','pet'):
            for _ in range(12 if field=='player' else 1):session.press(1)
            session.press(8);session.press(1);session.press(1,settle=180)
            if field=='player':
                for _ in range(3):session.press(1,settle=180)
        session.press(1,settle=200)
        for _ in range(100):
            active=[w for w in widgets(session) if w[1]==5]
            if active:break
            session.frames(4)
        session.screenshot(out/'widget-setup.png')
        assert len(active)==1,'normal opening dialogue widget not ready'
        root,state,cursor,data=active[0]
        context=u32(data,0xF8)
        initial=session.state();sram=session.sram();cases=[];captures=[]
        ranges=text_ranges(target,records)
        for begin,end,row,payload in ranges:
            session.restore(initial)
            # Native setters update external line/tile caches as well as the widget.
            # Transfer their EWRAM changes only; keep the original CPU/IRQ/stack state.
            before=session.read(0x02000000,0x40000)
            session.write(0x04000208,b"\0\0")  # IME off only during isolated calls
            session.call(0x08050425,root,begin,0x100,context)
            session.call(0x08050B3D,root)
            session.write(0x03006000,row['speaker'].encode('ascii')+b'\0')
            session.call(0x08050B51,root,0x03006000)
            after=session.read(0x02000000,0x40000)
            session.restore(initial)
            i=0
            while i<len(after):
                if before[i]==after[i] or 0x3F000<=i<0x3F004:
                    i+=1;continue
                start=i
                while i<len(after) and before[i]!=after[i] and not (0x3F000<=i<0x3F004):i+=1
                session.write(0x02000000+start,after[start:i])
            # 3 rows x 7 native 32x16 caches: stale opening pixels must be gone.
            cache_count=0
            for line in range(3):
                cells=u32(session.read(root+0xD8+line*4,4),0)
                for cell in range(7):
                    texture=u32(session.read(cells+cell*16,4),0)
                    assert 0x02000000<=texture<0x0203FEFC
                    assert not any(session.read(texture+4,256)), (line,cell,hex(texture),session.read(texture,36).hex())
                    cache_count+=1
            expected=[i+1 for i,b in enumerate(payload) if b==5]
            observed=[]
            for offset in expected:
                for _ in range(200):
                    session.frames(4)
                    current=next(w for w in widgets(session) if w[0]==root)
                    if current[1]==5 and current[2]==begin+offset:break
                else:raise AssertionError((row['id'],'native WAIT not reached',offset,[(w[1],hex(w[2])) for w in widgets(session)]))
                observed.append(offset)
                if row['id'] in ('script.1017.020','script.1017.030','script.0993.095','script.0993.102','script.0993.130') and len(observed)==1:
                    name=row['id']+'.png';session.screenshot(out/name);captures.append(name)
                if len(observed)<len(expected):session.press(1,settle=1)
            assert observed==expected
            cases.append({'id':row['id'],'speaker':row['speaker'],'wait_offsets_verified':observed,'native_widget':hex(root),'cleared_native_tile_caches':cache_count})
        assert session.sram()==sram,'fixture must not write SRAM'
        assert session.lib.session_errors()==0
        return {'status':'passed','target_sha256':hashlib.sha256(target).hexdigest(),'dialogue_records':len(cases),'thomas_branch_cases':len(branch_matrix(base)),
            'native_waits_verified':sum(len(c['wait_offsets_verified']) for c in cases),'guarded_renderer_lines':renderer,
            'cases':cases,'screenshots':captures,'sram_unchanged':True,'emulator_error_count':0,
            'limitations':['Native widget RAM fixtures; no natural NPC encounter, gift transaction or season progression claimed.',
                'Opening portrait hidden; speaker labels follow ROM-backed context, not an encountered actor.',
                'Language/layout manual review pending; longest dynamic variables separately reserved at 12 cells.',
                'Popuri spouse/home dialogue indexes 1..92 remain outside this batch.']}
    finally:session.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path)
    p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    p.add_argument('--output-dir',type=Path,default=Path('build/npc-daily'))
    p.add_argument('--limit',type=int)
    a=p.parse_args()
    if a.limit is not None and a.limit<=0:p.error('--limit must be positive')
    if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library)):p.error('inputs must be outside output-dir')
    result=run(a);(a.output_dir/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','screenshots')}))

if __name__=='__main__':main()
