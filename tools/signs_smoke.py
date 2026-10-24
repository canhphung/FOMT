#!/usr/bin/env python3
"""Source-preserved signs: original RAW glyphs and native WAIT/page/scroll fixtures."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from fomt_text import ROM_BASE,SCRIPT_TABLE,encode,parse_script,u32,verified_rom
from intro_smoke import probe_lines,text_ranges,widgets
from localization_queue import DEFAULT_TRANSLATIONS
from mgba_session import Session
from object_labels_smoke import cache_pixels,expected_pixels
from sign_text import verify


def raw_glyph(session,code):
    state=session.state()
    try:
        session.write(0x02038000,b'\xAA'*16+bytes(128)+b'\xAA'*16)
        width=session.call(0x080D0D29,0x02038010,code)*8
        data=session.read(0x02038000,160)
        assert data[:16]==data[-16:]==b'\xAA'*16
        pixels=set()
        for y in range(16):
            for x in range(16):
                at=(y//8*2+x//8)*32+y%8*4+x%8//2
                if data[16+at]>>(x%2*4)&15==1:pixels.add((x,y))
        assert width in (8,16)
        return width,pixels,data[16:-16]
    finally:session.restore(state)


def pages(base,text,raw):
    """Independent foreground model: CR/LF, PAGE and three-row scrolling."""
    rows=[set(),set(),set()];line=x=0;result=[]
    for part in re.split(r'(\{[^}]+\})',text):
        if part=='{CR}':x=0
        elif part=='{LF}':
            line+=1
            if line==3:rows.pop(0);rows.append(set());line=2
        elif part=='{PAGE}':rows=[set(),set(),set()];line=x=0
        elif part=='{WAIT}':result.append([set(r) for r in rows])
        elif part.startswith('{RAW:'):
            code=int(part[5:-1],16);advance,mask,_=raw[code]
            assert all(x+dx<224 for dx,y in mask),'RAW glyph overflow'
            rows[line].update((x+dx,y) for dx,y in mask);x+=advance
        elif part.startswith('{'):raise AssertionError('fixture variable not expanded: '+part)
        else:
            for char in part:
                mask=expected_pixels(base,char)
                assert all(x+dx<224 for dx,y in mask),'letter overflow'
                rows[line].update((x+dx,y) for dx,y in mask);x+=8
    return result


def assert_cache(actual,expected):
    # Native cache slots rotate on scroll. Require the full three-row bitmap
    # under a cyclic permutation, not just the presence of a final word.
    for shift in range(3):
        combined={(x,y+n*16) for n in range(3) for x,y in expected[(n+shift)%3]}
        if actual==combined:return shift
    combined=min(({(x,y+n*16) for n in range(3) for x,y in expected[(n+shift)%3]} for shift in range(3)),key=lambda c:len(c^actual))
    raise AssertionError(('sign cache foreground mismatch',len(actual),[len(r) for r in expected], 'missing',sorted(combined-actual)[:24], 'extra',sorted(actual-combined)[:24]))


def run(args, verifier=verify, capture_ids=None, speaker_labels=False):
    base=verified_rom(args.base_rom);target=args.rom.read_bytes();contract=verifier(base)
    proofs={r['id']:r for r in contract['source_proofs']}
    translations={r['id']:r for p in DEFAULT_TRANSLATIONS for r in json.loads(p.read_text())['records']}
    rows=[translations[i] for i in contract['record_ids']]
    untouched=0
    for sid in {r['script_id'] for r in proofs.values()}:
        a=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
        b=parse_script(target,u32(target,SCRIPT_TABLE+sid*4)-ROM_BASE)
        for tag in (b'CODE',b'JUMP'):assert dict(a['chunks']).get(tag)==dict(b['chunks']).get(tag)
        assert len(a['strings'])==len(b['strings'])
        for x,y in zip(a['strings'],b['strings']):
            key=f"script.{sid:04d}.{x['index']:03d}"
            expected=encode(translations[key]['vietnamese_translation'],True) if key in translations else x['raw']
            assert y['raw']==expected,key
            if key not in translations:untouched+=1
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    session=Session(args.rom,args.library);original=Session(args.base_rom,args.library)
    try:
        session.frames(360);original.frames(360)
        codes=sorted({int(code,16) for row in rows for code in re.findall(r'\{RAW:([0-9A-F]+)\}',row['vietnamese_translation'])})
        raw={};glyphs=[]
        for code in codes:
            a=raw_glyph(original,code);b=raw_glyph(session,code)
            assert a==b,hex(code)
            raw[code]=a;glyphs.append({'code':f'{code:04X}','advance_pixels':a[0],'foreground_pixels':len(a[1]),'staging_sha256':hashlib.sha256(a[2]).hexdigest()})
        renderer_rows=[{**r,'vietnamese_translation':re.sub(r'(^|\{CR\}\{LF\})((?:\{RAW:8140\})+)(?=\{CR\}\{LF\}|\{WAIT\}|$)',r'\1',r['vietnamese_translation'])} for r in rows]
        renderer=probe_lines(session,renderer_rows)
        sram=args.sram.read_bytes();session.load_sram(sram);session.lib.session_reset(session.handle);session.frames(360)
        for key,settle in ((8,180),(8,360),(1,360),(1,360)):session.press(key,settle=settle)
        session.press(1,settle=150)
        active=[w for w in widgets(session) if w[1]==5];assert len(active)==1
        root,_,_,data=active[0];context=u32(data,0xF8);initial=session.state();cases=[]
        for begin,end,row,payload in text_ranges(target,rows):
            if proofs[row['id']]['kind'] in ('frisbee_choice','popuri_choice','heart_event_choice'):continue
            working=re.sub(r'\{VAR:[0-9A-F]{2}\}','123456789012',row['vietnamese_translation'])
            dynamic=working!=row['vietnamese_translation']
            if dynamic:payload=encode(working,True);begin=0x03006000;end=begin+len(payload)
            session.restore(initial);before=session.read(0x02000000,0x40000)
            if dynamic:session.write(begin,payload+b'\0')
            session.write(0x04000208,b'\0\0')
            flags=proofs[row['id']]['show_text_sites'][0]['text_flags']
            session.call(0x08050425,root,begin,flags,context)
            session.call(0x08050B3D,root)
            if speaker_labels and row.get('speaker'):
                session.write(0x03005800,row['speaker'].split(' / ')[0].encode('ascii')+b'\0')
                session.call(0x08050B51,root,0x03005800)
            else:session.call(0x08050C19,root)
            after=session.read(0x02000000,0x40000);session.restore(initial)
            if dynamic:session.write(begin,payload+b'\0')
            i=0
            while i<len(after):
                if before[i]==after[i] or 0x3F000<=i<0x3F004:i+=1;continue
                start=i
                while i<len(after) and before[i]!=after[i] and not 0x3F000<=i<0x3F004:i+=1
                session.write(0x02000000+start,after[start:i])
            assert not cache_pixels(session,root),'stale sign cache'
            offsets=[i+1 for i,b in enumerate(payload) if b==5];expected=pages(base,working,raw);assert len(offsets)==len(expected)
            rotations=[];captures=[]
            for n,(offset,wanted) in enumerate(zip(offsets,expected)):
                for _ in range(220):
                    session.frames(4)
                    widget=next(w for w in widgets(session) if w[0]==root)
                    if widget[1]==5 and widget[2]==begin+offset:break
                else:raise AssertionError((row['id'],'WAIT not reached',n))
                try:rotations.append(assert_cache(cache_pixels(session,root),wanted))
                except AssertionError:
                    session.screenshot(out/('failure-'+row['id']+f'-{n}.png'));raise
                if row['id'] in (capture_ids or ('script.0161.000','script.0163.000','script.0403.013','script.0492.000','script.0496.000','script.0497.000','script.0505.000','script.0507.000')):
                    name=row['id']+f'-wait-{n+1}.png';session.screenshot(out/name);captures.append(name)
                if n+1<len(offsets):session.press(1,settle=1)
            cases.append({'id':row['id'],'speaker':row.get('speaker') if speaker_labels else None,'wait_offsets_verified':offsets,'exact_foreground_cache_rotations':rotations,'dynamic_12_cell_standin':dynamic,'screenshots':captures})
        assert session.sram()==sram and session.lib.session_errors()==0 and original.lib.session_errors()==0
        return {'status':'passed','target_sha256':hashlib.sha256(target).hexdigest(),'sign_records':len(rows),'native_widget_cases':len(cases),
            'choice_labels_renderer_only':sum(r['kind'] in ('frisbee_choice','popuri_choice','heart_event_choice') for r in proofs.values()),'guarded_renderer_lines':renderer,'native_waits_verified':sum(len(c['wait_offsets_verified']) for c in cases),
            'source_scripts_CODE_JUMP_unchanged':len({r['script_id'] for r in proofs.values()}),'untranslated_strings_byte_identical':untouched,
            'original_RAW_glyphs_unchanged':glyphs,'cases':cases,'sram_unchanged':True,'emulator_error_count':0,
            'limitations':['Native UI fixtures hosted in the house, not natural encounters with every sign.',
                'Three choice labels tested by renderer and source call, not the native choice widget.',
                'Variables preserved in ROM; layout fixtures substitute twelve digits, not proof of native variable values.',
                'Manual language/layout review and physical-map completeness pending.']}
    finally:session.close();original.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path)
    p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'));p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'))
    p.add_argument('--output-dir',type=Path,default=Path('build/signs'));a=p.parse_args()
    if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library,a.sram)):p.error('inputs must be outside output-dir')
    report=run(a);(a.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},ensure_ascii=False))
if __name__=='__main__':main()
