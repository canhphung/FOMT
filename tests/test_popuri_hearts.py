import json,os
from pathlib import Path
import pytest
from fomt_text import verified_rom,FormatError,check_translation,extract
from popuri_heart_events import verify,response_blocks,CONTRACT
ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def base():
 if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
 return verified_rom(os.environ['FOMT_ROM'])
def test_complete_four_events_and_speakers(base):
 p=verify(base);assert len(p['record_ids'])==99
 counts={sid:sum(r['script_id']==sid for r in p['source_proofs']) for sid in (36,37,38,39)}
 assert counts=={36:17,37:8,38:45,39:29}
 src={r['id']:r for r in extract(base)['records']};vi={r['id']:r for r in json.loads((ROOT/'localization/vi/pilot.json').read_text())['records']}
 for key in p['record_ids']:
  row=src[key];text=vi[key]['vietnamese_translation'];check_translation(row['original_english'],text,row['max_columns'],drop_apostrophe=key=='script.0038.026')
  assert row['speaker']==vi[key]['speaker']
 assert {r['speaker'] for r in src['script.0038.002']['source']['heart_event_context']['speaker_sites']}=={'May','Stu'}
 assert src['script.0039.000']['speaker']=='Rick' and src['script.0039.025']['speaker']=='Lillia'
 assert src['script.0038.019']['speaker']=='Popuri'
def test_choice_response_blocks_are_all_covered(base):
 b=response_blocks(base);assert len(b)==9
 by={(r['script_id'],r['selection']):r['dialogue_ids'] for r in b}
 assert by[36,1]==['script.0036.011','script.0036.012','script.0036.013']
 assert by[36,2]==['script.0036.014','script.0036.015','script.0036.016']
 assert by[37,1]==['script.0037.003'] and by[37,2]==[f'script.0037.{i:03d}' for i in range(4,8)]
 assert by[38,1]==[f'script.0038.{i:03d}' for i in range(15,34)]
 assert by[38,2]==[f'script.0038.{i:03d}' for i in range(34,45)]
 assert by[39,3]==[f'script.0039.{i:03d}' for i in range(23,29)]
def test_changed_literals_names_and_code_are_rejected(base):
 from fomt_text import u32,SCRIPT_TABLE,ROM_BASE,parse_script
 s=parse_script(base,u32(base,SCRIPT_TABLE+38*4)-ROM_BASE)
 for where in (s['strings'][26]['address'],s['address']+24,0x104258+3*8,0x104138):
  bad=bytearray(base);bad[where]^=1
  with pytest.raises(FormatError):verify(bad)
def test_forged_speaker_or_route_is_rejected(base,tmp_path,monkeypatch):
 import popuri_heart_events
 p=json.loads(CONTRACT.read_text());p['source_proofs'][0]['speaker_sites'][0]['speaker_id']=22
 path=tmp_path/'forged.json';path.write_text(json.dumps(p));monkeypatch.setattr(popuri_heart_events,'CONTRACT',path)
 with pytest.raises(FormatError):verify(base)
