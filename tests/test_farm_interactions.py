import json,os
from pathlib import Path
import pytest
from fomt_text import FormatError,check_translation,verified_rom
from sign_text import verify

def test_farm_contract_and_original_literals_fail_closed():
 if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
 root=Path(__file__).resolve().parents[1];base=verified_rom(os.environ['FOMT_ROM']);path=root/'localization/farm_interactions.json'
 proof=verify(base,path);assert len(proof['record_ids'])==23
 vi={r['id']:r for r in json.loads((root/'localization/vi/pilot.json').read_text())['records']}
 for p in proof['source_proofs']:
  r=vi[p['id']];check_translation(r['original_english'],r['vietnamese_translation'],28)
  bad=bytearray(base);bad[int(r['rom_offset'],16)]^=1
  with pytest.raises(FormatError,match='sign source mismatch'):verify(bad,path)
