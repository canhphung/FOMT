import json,os
from pathlib import Path
import pytest
from fomt_text import verified_rom,check_translation
from sign_text import verify
from npc_context import script_parts
ROOT=Path(__file__).resolve().parents[1]
def test_popuri_source_and_scoped_voice():
 if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
 b=verified_rom(os.environ['FOMT_ROM']);script_parts(b,993);proof=verify(b,ROOT/'localization/popuri_context.json');assert len(proof['record_ids'])==144
 vi={r['id']:r for r in json.loads((ROOT/'localization/vi/pilot.json').read_text())['records']}
 for key in proof['record_ids']:
  row=vi[key];check_translation(row['original_english'],row['vietnamese_translation'],28,drop_apostrophe=key in ('script.0993.005','script.0993.021','script.0993.092'))
 assert 'lo cho' in vi['script.0993.125']['vietnamese_translation']
 assert 'cha Carter' in vi['script.0993.136']['vietnamese_translation']
 assert 'Em' in vi['script.0993.006']['vietnamese_translation']
 assert all(f'script.0993.{i:03d}' in proof['record_ids'] for i in (5,21,38,39,92))


def test_apostrophe_exception_cannot_remove_other_controls():
 from fomt_text import FormatError
 original="I{RAW:8166}m {VAR:29}!{WAIT}"
 with pytest.raises(FormatError):check_translation(original,"Em {VAR:29}!{WAIT}",28)
 check_translation(original,"Em {VAR:29}!{WAIT}",28,drop_apostrophe=True)
 for wrong in ("Em!{WAIT}","Em {VAR:29}!","Em{RAW:8166}{RAW:8166} {VAR:29}!{WAIT}"):
  with pytest.raises(FormatError):check_translation(original,wrong,28,drop_apostrophe=True)

def test_choice_byte_budget_and_scoped_punctuation_in_editor():
 if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
 from fomt_text import extract
 from translation_workbench import Repository
 rows=extract(verified_rom(os.environ['FOMT_ROM']))['records']
 assert {r['id'] for r in rows if r['source'].get('popuri_context',{}).get('drop_apostrophe')}=={'script.0993.005','script.0993.021','script.0993.092','script.0038.026'}
 repo=Repository(ROOT)
 assert repo.validate('script.0993.039','Xin lỗi, mình có hẹn.')['valid']
 assert any(e['code']=='bytes' for e in repo.validate('script.0993.039','Xin lỗi, mình có hẹn rồi.')['errors'])
 assert any(e['code']=='tokens' for e in repo.validate('script.0993.092','Em đang làm việc!{WAIT}')['errors'])
