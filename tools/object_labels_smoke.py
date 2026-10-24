#!/usr/bin/env python3
"""Object labels: two natural house interactions plus isolated native UI fixtures.

Fixture mechanics follow npc_daily_smoke: native setters with IME temporarily
off, copy changed EWRAM caches only, restore CPU/IRQ/IWRAM before frames.
"""
import argparse
import hashlib
import json
from pathlib import Path

from fomt_text import ROM_BASE,SCRIPT_TABLE,encode,parse_script,u32,verified_rom
from intro_smoke import widgets,text_ranges,probe_lines
from mgba_session import Session
from object_text import verify
from vietnamese_font import ascii_glyph,glyph


def cache_pixels(session,root):
    pixels=set()
    for line in range(3):
        cells=u32(session.read(root+0xD8+line*4,4),0)
        for cell in range(7):
            texture=u32(session.read(cells+cell*16,4),0)
            assert 0x02000000<=texture<0x0203FEFC
            data=session.read(texture+4,256)
            for y in range(16):
                for x in range(32):
                    at=(y//8*4+x//8)*32+y%8*4+x%8//2
                    if data[at]>>(x%2*4)&15==1:pixels.add((cell*32+x,line*16+y))
    return pixels


def expected_pixels(base,text):
    label=text.removesuffix('{WAIT}').removesuffix('{CR}{LF}')
    result=set()
    for col,char in enumerate(label):
        mask=ascii_glyph(base,char) if ord(char)<128 else glyph(base,char)
        result.update((col*8+dx+1,y) for y,row in enumerate(mask) for dx in range(8) if row&(128>>dx))
    assert all(x<224 and y<16 for x,y in result)
    return result


def audit_scripts(base,target,translations,contract):
    names={r['id'] for r in contract['records']};untouched=0
    for sid in map(int,contract['script_code_sha256']):
        a=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
        b=parse_script(target,u32(target,SCRIPT_TABLE+sid*4)-ROM_BASE)
        assert len(a['strings'])==len(b['strings'])
        for tag in (b'CODE',b'JUMP'):assert dict(a['chunks']).get(tag)==dict(b['chunks']).get(tag)
        for x,y in zip(a['strings'],b['strings']):
            key=f"script.{sid:04d}.{x['index']:03d}"
            expected=encode(translations[key]['vietnamese_translation'],True) if key in translations else x['raw']
            assert y['raw']==expected,key
            untouched+=key not in names and y["raw"]==x["raw"]
    return untouched


def run(args):
    base=verified_rom(args.base_rom);target=args.rom.read_bytes();contract=verify(base)
    proofs={r['id']:r for r in contract['records']}
    rows=[r for r in json.loads(Path('localization/vi/pilot.json').read_text())['records'] if r['id'] in proofs]
    assert len(rows)==261
    if args.limit:rows=rows[:args.limit]
    translations={r['id']:r for r in json.loads(Path('localization/vi/pilot.json').read_text())['records']}
    untouched=audit_scripts(base,target,translations,contract)
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    session=Session(args.rom,args.library)
    try:
        session.frames(360);renderer=probe_lines(session,rows)
        source_sram=args.sram.read_bytes();session.load_sram(source_sram);session.lib.session_reset(session.handle);session.frames(360)
        for key,settle in ((8,180),(8,360),(1,360),(1,360)):session.press(key,settle=settle)
        house=session.state();ranges=text_ranges(target,rows);natural=[]
        for identifier,moves in [('script.0355.000',[]),('script.0351.001',[(128,54),(32,94)])]:
            session.restore(house)
            for key,frames in moves:session.frames(frames,key);session.frames(1)
            session.press(1,settle=150)
            row=translations[identifier];s=parse_script(target,u32(target,SCRIPT_TABLE+row['source']['script_id']*4)-ROM_BASE)
            entry=s['strings'][row['source']['string_index']];end=ROM_BASE+entry['address']+len(entry['raw'])
            active=[w for w in widgets(session) if w[1]==5 and w[2]==end];assert len(active)==1,(identifier,active)
            assert cache_pixels(session,active[0][0])==expected_pixels(base,row['vietnamese_translation'])
            file='natural-'+identifier+'.png';session.screenshot(out/file)
            natural.append({'id':identifier,'controls':moves,'A_settle_frames':150,'native_wait_pointer':hex(end),'screenshot':file,'ram_state_modified':False})
        root,_,_,data=active[0];context=u32(data,0xF8);initial=session.state();cases=[];captures=[]
        for begin,end,row,payload in ranges:
            session.restore(initial);before=session.read(0x02000000,0x40000)
            flags=proofs[row['id']]['show_text_sites'][0]['text_flags']
            session.write(0x04000208,b'\0\0')
            session.call(0x08050425,root,begin,flags,context)
            session.call(0x08050B3D,root);session.call(0x08050C19,root)
            after=session.read(0x02000000,0x40000);session.restore(initial)
            i=0
            while i<len(after):
                if before[i]==after[i] or 0x3F000<=i<0x3F004:i+=1;continue
                start=i
                while i<len(after) and before[i]!=after[i] and not 0x3F000<=i<0x3F004:i+=1
                session.write(0x02000000+start,after[start:i])
            assert not cache_pixels(session,root),'stale object text foreground cache'
            for _ in range(200):
                session.frames(4)
                current=next(w for w in widgets(session) if w[0]==root)
                if current[1]==5 and current[2]==end:break
            else:raise AssertionError((row['id'],'object WAIT not reached'))
            expected=expected_pixels(base,row['vietnamese_translation']);actual=cache_pixels(session,root)
            if actual!=expected:
                session.screenshot(out/('failure-'+row['id']+'.png'))
                raise AssertionError((row['id'],'foreground mismatch',len(expected-actual),len(actual-expected)))
            cases.append({'id':row['id'],'native_text_flags':flags,'foreground_pixels_verified':len(expected),'wait_pointer':hex(end)})
            if row['id'] in ('script.0116.000','script.0127.000','script.0335.000','script.0343.046','script.0538.000'):
                name='fixture-'+row['id']+'.png';session.screenshot(out/name);captures.append(name)
        assert session.sram()==source_sram and session.lib.session_errors()==0
        return {'status':'passed','target_sha256':hashlib.sha256(target).hexdigest(),'object_label_records':len(cases),
            'unique_terms':len({proofs[r['id']]['label_english'] for r in rows}),'native_waits_verified':len(cases),
            'guarded_renderer_lines':renderer,'script_CODE_JUMP_unchanged':len(contract['script_code_sha256']),
            'nonlabel_strings_byte_identical':untouched,'natural_house_interactions':natural,'cases':cases,
            'fixture_screenshots':captures,'sram_unchanged':True,'emulator_error_count':0,
            'limitations':['Natural input verified two tables in the starting farmhouse, not every map/upgrade/object.',
                'Other labels use native dialogue fixtures with original flags; framebuffer location is not a natural encounter witness.',
                'Menus, longer hints, signs and mixed-script event dialogue outside selected labels remain unchanged.',
                'Language/layout review and real GBA hardware testing pending.']}
    finally:session.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path)
    p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'));p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'))
    p.add_argument('--output-dir',type=Path,default=Path('build/object-labels'));p.add_argument('--limit',type=int)
    a=p.parse_args()
    if a.limit is not None and a.limit<=0:p.error('limit must be positive')
    if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library,a.sram)):p.error('inputs must be outside output-dir')
    result=run(a);(a.output_dir/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','fixture_screenshots','natural_house_interactions')}))

if __name__=='__main__':main()
