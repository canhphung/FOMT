#!/usr/bin/env python3
"""Native fixtures for all four Popuri heart-event dialogue scripts."""
import argparse,json
from pathlib import Path
from popuri_heart_events import verify
from signs_smoke import run
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'localization/popuri_heart_events.json'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--base-rom',required=True,type=Path);p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'));p.add_argument('--sram',type=Path,default=Path('local-data/fixtures/day2.sram'));p.add_argument('--output-dir',type=Path,default=Path('build/popuri-hearts'));a=p.parse_args()
 if any(f.resolve().is_relative_to(a.output_dir.resolve()) for f in (a.rom,a.base_rom,a.library,a.sram)):p.error('inputs must be outside output-dir')
 proof=verify(a.base_rom.read_bytes())
 result=run(a,verifier=lambda base:verify(base),capture_ids={'script.0036.011','script.0037.003','script.0038.019','script.0038.026','script.0039.025','script.0039.027'},speaker_labels=True)
 result['limitations']=['Native UI fixtures, not natural object encounters.','Dialogue variables substitute twelve digits for layout; original VAR preserved.','Manual language/layout review and other unclassified interactions remain pending.']
 (a.output_dir/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))
if __name__=='__main__':main()
