"""Verify the exact screenshot instructions without changing sleep behavior."""
import json
import os

import pytest
from fomt_text import FormatError, ROM_BASE, SCRIPT_TABLE, parse_script, u32, verified_rom
from interaction_hints_smoke import BATCH, verify


def test_hint_source_and_unchanged_sleep_choices():
    if not os.environ.get('FOMT_ROM'):
        pytest.skip('legally supplied ROM required')
    base = verified_rom(os.environ['FOMT_ROM'])
    batch = verify(base)
    assert batch['record_ids'] == ['script.0223.003','script.0342.003','script.0464.000']
    for proof in batch['source_proofs']:
        script = parse_script(base,u32(base,SCRIPT_TABLE+proof['script_id']*4)-ROM_BASE)
        broken = bytearray(base)
        broken[script['strings'][proof['string_index']]['address']] ^= 1
        with pytest.raises(FormatError,match='hint source mismatch'):
            verify(broken)


def test_hint_caller_proof_cannot_be_forged(tmp_path,monkeypatch):
    if not os.environ.get('FOMT_ROM'):
        pytest.skip('legally supplied ROM required')
    import interaction_hints_smoke
    base = verified_rom(os.environ['FOMT_ROM'])
    data = json.loads(BATCH.read_text())
    data['source_proofs'][0]['show_text_sites'][0]['code_offset'] += 1
    path = tmp_path/'forged.json'
    path.write_text(json.dumps(data))
    monkeypatch.setattr(interaction_hints_smoke,'BATCH',path)
    with pytest.raises(FormatError,match='display site mismatch'):
        verify(base)
