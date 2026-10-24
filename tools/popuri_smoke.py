#!/usr/bin/env python3
"""Native fixtures for verified Popuri standard dialogue."""
import argparse,json
from pathlib import Path
from sign_text import verify
from signs_smoke import run
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'localization/popuri_context.json'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path);p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'));p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'));p.add_argument('--output-dir',type=Path,default=Path('build/popuri'));a=p.parse_args()
 if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library,a.sram)):p.error('inputs must be outside output-dir')
 from npc_context import script_parts
 script_parts(a.base_rom.read_bytes(),993)
 proof=verify(a.base_rom.read_bytes(),CONTRACT)
 result=run(a,verifier=lambda base:verify(base,CONTRACT),capture_ids={'script.0993.006','script.0993.043','script.0993.057','script.0993.125','script.0993.136','script.0993.005','script.0993.021','script.0993.092'})
 result['limitations']=['Native UI fixtures, not natural object encounters.','Dialogue variables substitute twelve digits for layout; original VAR preserved.','Manual language/layout review and other unclassified interactions remain pending.']
 (a.output_dir/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
if __name__=='__main__':main()
