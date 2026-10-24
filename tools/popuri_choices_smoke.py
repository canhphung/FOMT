#!/usr/bin/env python3
"""Isolated native two-choice fixture with actual translated ROM strings."""
import argparse,json,hashlib
from pathlib import Path
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
from mgba_session import Session
from intro_smoke import widgets,text_ranges
from fomt_text import u32,verified_rom
from popuri_text import CONTRACT
from sign_text import verify
from signs_smoke import raw_glyph,assert_cache
from object_labels_smoke import cache_pixels,expected_pixels

def run(a):
 verify(verified_rom(a.base_rom),CONTRACT);target=a.rom.read_bytes();a.output_dir.mkdir(parents=True,exist_ok=True)
 rows=[r for r in json.loads(Path('localization/vi/pilot.json').read_text())['records'] if r['id'] in ('script.0993.038','script.0993.039')];ranges=text_ranges(target,rows)
 s=Session(a.rom,a.library);source=Session(a.base_rom,a.library)
 try:
  s.frames(360);source.frames(360);g=raw_glyph(source,0x8166);assert g==raw_glyph(s,0x8166)
  saved=a.sram.read_bytes();s.load_sram(saved);s.lib.session_reset(s.handle);s.frames(360)
  for key,settle in ((8,180),(8,360),(1,360),(1,360)):s.press(key,settle=settle)
  s.press(1,settle=150);root,_,_,data=next(w for w in widgets(s) if w[1]==5);context=u32(data,0xF8);initial=s.state()
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
  code=bytes(Ks(KS_ARCH_ARM,KS_MODE_THUMB).asm(assembly,addr=0x03006000)[0]);before=s.read(0x02000000,0x40000)
  s.write(0x04000208,b'\0\0');s.write(0x03006000,code);s.call(0x03006001,root,ranges[0][0],ranges[1][0],0)
  s.call(0x08050B3D,root);s.call(0x08050C19,root)
  after=s.read(0x02000000,0x40000);s.restore(initial);i=0
  while i<len(after):
   if before[i]==after[i] or 0x3F000<=i<0x3F004:i+=1;continue
   start=i
   while i<len(after) and before[i]!=after[i] and not 0x3F000<=i<0x3F004:i+=1
   s.write(0x02000000+start,after[start:i])
  s.frames(90);assert_cache(cache_pixels(s,root),[{(x+16,y) for x,y in expected_pixels(verified_rom(a.base_rom),r['vietnamese_translation'])} for r in rows]+[set()]);s.screenshot(a.output_dir/'choices-initial.png');print('before',s.read(root+0x158,12).hex(),flush=True)
  ready=s.state();cases=[]
  for down in (False,True):
   s.restore(ready)
   if down:s.press(128,settle=30)
   selected=s.read(root+0x158,12).hex();s.screenshot(a.output_dir/('choice-second.png' if down else 'choice-first.png'))
   s.press(1,settle=30);cases.append({'down':down,'selection_fields':selected,'after_A_state':u32(s.read(root+8,4),0)})
  assert cases[0]['selection_fields'].startswith('01000000') and cases[1]['selection_fields'].startswith('02000000');assert all(c['after_A_state']==0 for c in cases);assert s.sram()==saved and s.lib.session_errors()==0
  return {'status':'passed','target_sha256':hashlib.sha256(target).hexdigest(),'RAW_8166_staging_sha256':hashlib.sha256(g[2]).hexdigest(),'RAW_8166_matches_original':True,'both_choice_label_bitmaps_verified':True,'cases':cases,'sram_unchanged':True,'limitations':['Native choice fixture, not natural Starry Night encounter or event branch completion.']}
 finally:s.close();source.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path);p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'));p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'));p.add_argument('--output-dir',type=Path,default=Path('build/popuri-choices'));a=p.parse_args()
 if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library,a.sram)):p.error('inputs must be outside output-dir')
 r=run(a);(a.output_dir/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
