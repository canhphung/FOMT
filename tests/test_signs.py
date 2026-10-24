"""ROM-backed sign coverage, constrained padding and preservation of event code."""
import json
import os
from pathlib import Path
import pytest
from fomt_text import FormatError,ROM_BASE,ROM_SHA1,SCRIPT_TABLE,check_translation,encode,extract,parse_script,tokens,u32,verified_rom
from localization_queue import DEFAULT_TRANSLATIONS,queue
import sign_text

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def base():
    if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
    return verified_rom(os.environ['FOMT_ROM'])


def test_sign_corpus_and_source_guards(base):
    proof=sign_text.verify(base)
    assert len(proof['record_ids'])==48 and len({r['script_id'] for r in proof['source_proofs']})==31
    for sid,index in ((161,0),(403,13),(492,0)):
        script=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
        for address in (script['strings'][index]['address'],script['address']+24):
            bad=bytearray(base);bad[address]^=1
            with pytest.raises(FormatError,match='sign'):sign_text.verify(bad)


def test_padding_reflow_is_scoped_and_cannot_remove_arrows(base):
    source={r['id']:r for r in extract(base)['records']}
    vi=json.loads((ROOT/'localization/vi/signs.json').read_text())['records']
    relaxed=[]
    for row in vi:
        original=source[row['id']];allow=original['source']['sign_context']['padding_reflow']
        check_translation(original['original_english'],row['vietnamese_translation'],28,padding_reflow=allow)
        if allow:
            relaxed.append(row['id'])
            with pytest.raises(FormatError):check_translation(original['original_english'],row['vietnamese_translation'],28)
            broken=row['vietnamese_translation'].replace('{RAW:81A9}','')
            with pytest.raises(FormatError):check_translation(original['original_english'],broken,28,padding_reflow=True)
    assert relaxed==['script.0497.000','script.0507.000']
    with pytest.raises(FormatError):check_translation('A{RAW:8140}','A',28)
    with pytest.raises(FormatError):check_translation('A{RAW:8140}','A{RAW:8140}{RAW:8140}',28,padding_reflow=True)


def test_sign_build_keeps_all_code_and_unselected_event_strings(base):
    from text_inserter import build
    rows=[r for p in DEFAULT_TRANSLATIONS for r in json.loads(p.read_text())['records']]
    vi={r['id']:r for r in rows};target,report=build(base,{'rom_sha1':ROM_SHA1,'records':rows})
    assert report['translated_records']==1479
    for sid in {r['script_id'] for r in sign_text.verify(base)['source_proofs']}:
        a=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
        b=parse_script(target,u32(target,SCRIPT_TABLE+sid*4)-ROM_BASE)
        for tag in (b'CODE',b'JUMP'):assert dict(a['chunks']).get(tag)==dict(b['chunks']).get(tag)
        assert len(a['strings'])==len(b['strings'])
        for x,y in zip(a['strings'],b['strings']):
            key=f"script.{sid:04d}.{x['index']:03d}"
            assert y['raw']==(encode(vi[key]['vietnamese_translation'],True) if key in vi else x['raw'])


def test_workbench_and_queue_accept_only_verified_padding(base):
    from translation_workbench import Repository
    repo=Repository(ROOT)
    vi={r['id']:r for r in json.loads((ROOT/'localization/vi/signs.json').read_text())['records']}
    row=vi['script.0497.000'];result=repo.validate(row['id'],row['vietnamese_translation'])
    assert not result['errors']
    assert any(e['code']=='tokens' for e in repo.validate(row['id'],row['vietnamese_translation'].replace('{RAW:81AA}',''))['errors'])
    all_rows=[r for p in DEFAULT_TRANSLATIONS for r in json.loads(p.read_text())['records']]
    selected=[r for r in queue(extract(base),all_rows,json.loads((ROOT/'localization/qa/records.json').read_text())) if r['id'] in vi]
    assert len(selected)==48 and all(r['bucket']=='qa' and not r['validation_errors'] for r in selected)
