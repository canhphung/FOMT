#!/usr/bin/env python3
"""Verify relocated tool descriptions and native rendering without claiming UI encounters."""
import argparse
import hashlib
import json
from pathlib import Path
from fomt_text import ROM_BASE,encode,u32,verified_rom,check_translation,extract
from intro_smoke import probe_lines
from mgba_session import Session


def run(args):
    base=verified_rom(args.base_rom);target=args.rom.read_bytes()
    rows=json.loads(args.batch.read_text())['records']
    originals={r['id']:r for r in extract(base)['records']}
    session=Session(args.rom,args.library)
    try:
        session.frames(360)
        pointers=0
        for row in rows:
            payload=encode(row['vietnamese_translation'],True)+b'\0'
            original=originals[row['id']]
            assert original['context']=='item_description' and original['original_english']==row['original_english']
            for slot in original['source']['pointer_offsets']:
                assert u32(base,slot)==int(original['rom_address'],16),row['id']
                at=u32(target,slot)-ROM_BASE
                assert at>=len(base) and target[at:at+len(payload)]==payload,row['id']
                pointers+=1
            check_translation(row['original_english'],row['vietnamese_translation'],original['max_columns'])
        lines=probe_lines(session,rows)
        if args.preview:
            from PIL import Image,ImageDraw
            from font_preview import render_line
            state=session.state()
            sheet=Image.new('RGB',(512,500),'white');draw=ImageDraw.Draw(sheet)
            draw.text((4,4),'Native renderer diagnostic; NOT a gameplay window',fill='black')
            for index,record in enumerate(rows[i] for i in ((0,5,8,14) if len(rows)>14 else range(min(4,len(rows))))):
                y=24+index*118;draw.text((4,y),record['id'],fill='black')
                for line_index,line in enumerate(record['vietnamese_translation'].split('{CR}{LF}')):
                    image=render_line(session,state,line).resize((512,32),Image.Resampling.NEAREST)
                    sheet.paste(image,(0,y+16+line_index*32))
            args.preview.parent.mkdir(parents=True,exist_ok=True);sheet.save(args.preview)
        assert session.lib.session_errors()==0
        return {'target_sha256':hashlib.sha256(target).hexdigest(),'status':'passed',
                'record_ids':[r['id'] for r in rows],'translated_records':len(rows),
                'relocated_description_pointers_verified':pointers,
                'native_renderer_lines_with_buffer_guards':lines,'emulator_error_count':0,
                'checks_scope':'isolated native renderer and actual ROM pointer payloads',
                'natural_item_windows_tested':0,
                'limitations':['Upgraded/cursed/blessed tools not obtained through gameplay.',
                    'No natural item-description window encounter claimed; layout/playtest approval remains pending.',
                    'No real hardware test.']}
    finally:session.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--base-rom',type=Path,required=True)
    p.add_argument('--batch',type=Path,default=Path('localization/vi/item_descriptions_tools.json'))
    p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    p.add_argument('--preview',type=Path,help='optional labeled native-renderer diagnostic, not gameplay evidence')
    p.add_argument('--output',type=Path,default=Path('build/item-batch/report.json'))
    args=p.parse_args()
    inputs={path.resolve() for path in (args.rom,args.base_rom,args.batch,args.library)}
    outputs=[args.output,*([args.preview] if args.preview else [])]
    if len({path.resolve() for path in outputs})!=len(outputs) or inputs&{path.resolve() for path in outputs}:
        p.error('outputs must be distinct and must not overwrite inputs')
    report=run(args);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
