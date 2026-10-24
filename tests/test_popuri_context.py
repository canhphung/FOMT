import json,os
from pathlib import Path
import pytest
from fomt_text import verified_rom,check_translation
from sign_text import verify
from npc_context import script_parts
ROOT=Path(__file__).resolve().parents[1]
def test_popuri_source_and_scoped_voice():
 if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
 b=verified_rom(os.environ['FOMT_ROM']);script_parts(b,993);proof=verify(b,ROOT/'localization/popuri_context.json');assert len(proof['record_ids'])==139
 vi={r['id']:r for r in json.loads((ROOT/'localization/vi/pilot.json').read_text())['records']}
 for key in proof['record_ids']:
  row=vi[key];check_translation(row['original_english'],row['vietnamese_translation'],28)
 assert 'lo cho' in vi['script.0993.125']['vietnamese_translation']
 assert 'cha Carter' in vi['script.0993.136']['vietnamese_translation']
 assert 'Em' in vi['script.0993.006']['vietnamese_translation']
 assert not any(f'script.0993.{i:03d}' in proof['record_ids'] for i in (5,21,38,39,92))
