#!/usr/bin/env python3
"""All four native heart-event menus, including all nine selections."""
import argparse,json,hashlib
from pathlib import Path
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
from mgba_session import Session
from intro_smoke import widgets,text_ranges
from fomt_text import u32,verified_rom
from popuri_heart_events import verify
from signs_smoke import assert_cache
from object_labels_smoke import cache_pixels,expected_pixels

def run(a):
 base=verified_rom(a.base_rom);proof=verify(base);target=a.rom.read_bytes();a.output_dir.mkdir(parents=True,exist_ok=True)
 vi={r['id']:r for r in json.loads(Path('localization/vi/pilot.json').read_text())['records']}
 s=Session(a.rom,a.library)
 try:
  s.frames(360);saved=a.sram.read_bytes();s.load_sram(saved);s.lib.session_reset(s.handle);s.frames(360)
  for key,settle in ((8,180),(8,360),(1,360),(1,360)):s.press(key,settle=settle)
  s.press(1,settle=150);root,_,_,data=next(w for w in widgets(s) if w[1]==5);context=u32(data,0xF8);initial=s.state();menus=[]
  for group in proof['choice_groups']:
   sid=group['script_id'];rows=[vi[f'script.{sid:04d}.{i:03d}'] for i in group['choice_indices']];ranges=text_ranges(target,rows)
   assembly=f'''push {{r4,lr}}
sub sp,#16
movs r4,#0
str r4,[sp]
str r4,[sp,#4]
str r4,[sp,#8]
ldr r4,ctx
str r4,[sp,#12]
ldr r4,fn
bl via
add sp,#16
pop {{r4}}
pop {{r3}}
bx r3
via: bx r4
.balign 4
ctx: .word {context}
fn: .word 0x08050479'''
   code=bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(assembly,addr=0x03006000)[0]);s.restore(initial);before=s.read(0x02000000,0x40000)
   s.write(0x04000208,b'\0\0');s.write(0x03006000,code);s.call(0x03006001,root,ranges[0][0],ranges[1][0],ranges[2][0] if len(rows)==3 else 0)
   s.call(0x08050B3D,root);s.call(0x08050C19,root)
   after=s.read(0x02000000,0x40000);s.restore(initial);i=0
   while i<len(after):
    if before[i]==after[i] or 0x3F000<=i<0x3F004:i+=1;continue
    start=i
    while i<len(after) and before[i]!=after[i] and not 0x3F000<=i<0x3F004:i+=1
    s.write(0x02000000+start,after[start:i])
   s.frames(90);expected=[{(x+16,y) for x,y in expected_pixels(base,r['vietnamese_translation'])} for r in rows]+[set()]*(3-len(rows));assert_cache(cache_pixels(s,root),expected)
   ready=s.state();cases=[]
   for option in range(len(rows)):
    s.restore(ready)
    for _ in range(option):s.press(128,settle=30)
    selected=u32(s.read(root+0x158,4),0);assert selected==option+1
    name=f'event-{sid}-option-{option+1}.png';s.screenshot(a.output_dir/name)
    s.press(1,settle=30);assert u32(s.read(root+8,4),0)==0
    cases.append({'source_id':rows[option]['id'],'native_selection':selected,'script_response_entry':group['routes'][option]['target'],'A_confirmed':True,'screenshot':name})
   menus.append({'script_id':sid,'all_label_bitmaps_verified':True,'cases':cases})
  assert s.sram()==saved and s.lib.session_errors()==0
  return {'status':'passed','target_sha256':hashlib.sha256(target).hexdigest(),'menus':menus,'native_choices_confirmed':9,'sram_unchanged':True,'limitations':['Native menu UI fixtures, not natural event activation or subsequent gameplay effects.','Response entry values separately verified against source JUMP table; fixture does not execute the entire event.']}
 finally:s.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path);p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'));p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'));p.add_argument('--output-dir',type=Path,default=Path('build/heart-choices'));a=p.parse_args()
 if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library,a.sram)):p.error('inputs must be outside output-dir')
 r=run(a);(a.output_dir/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
