"""Synthetic queue records; no synthetic sentence is presented as ROM content."""
import json
from pathlib import Path
import pytest
from fomt_text import FormatError
from localization_queue import queue,select,digest


def fixture_data():
    original={'id':'fixture.description','original_english':'Fixture{CR}{LF}Text.',
              'context':'item_description','max_columns':28,'control_codes':['{CR}','{LF}']}
    translated={**original,'vietnamese_translation':'Mẫu{CR}{LF}Nội dung.','translation_status':'translated'}
    manual={'id':original['id'],'source_sha256':digest(original['original_english']),
            'translation_sha256':digest(translated['vietnamese_translation']),
            'context_status':'verified','context_evidence':'Synthetic unit fixture.',
            'language_review':'pending','renderer_check':{'status':'not_run'},'playtest':{'status':'not_run'}}
    return {'records':[original]},[translated],{'records':[manual]}


def test_context_queue_never_promotes_unclassified_or_unknown_flower():
    c,v,q=fixture_data();c['records'][0]['context']='script_string_unclassified'
    assert queue(c,[],{'records':[]})[0]['bucket']=='blocked'
    q['records'][0].update(context_status='needs_context',blocked_reason='Unknown item referent.')
    assert queue(c,[],q)[0]['bucket']=='blocked'


def test_translation_or_source_edit_invalidates_old_qa():
    c,v,q=fixture_data();q['records'][0]['renderer_check']={'status':'passed','evidence':'fixture','target_sha256':'0'*64}
    v[0]['vietnamese_translation']='Mẫu{CR}{LF}Đã sửa.'
    row=queue(c,v,q)[0]
    assert row['qa_stale'] and row['renderer_check']=='stale' and row['bucket']!='done'
    c['records'][0]['original_english']=v[0]['original_english']='Changed{CR}{LF}Text.'
    assert queue(c,v,q)[0]['context_status']=='needs_context'


def test_invalid_control_stream_or_byte_limit_blocks_context_verified_translation():
    c,v,q=fixture_data();v[0]['vietnamese_translation']='Mất token.'
    row=queue(c,v,q)[0]
    assert row['bucket']=='blocked' and 'tokens' in row['blocked_reason']
    c,v,q=fixture_data();c['records'][0]['max_encoded_bytes']=4
    row=queue(c,v,q)[0]
    assert row['bucket']=='blocked' and 'encoded-byte' in row['blocked_reason']


def test_reviewed_translation_does_not_imply_playtesting():
    c,v,q=fixture_data();v[0]['translation_status']='reviewed'
    row=queue(c,v,q)[0]
    assert row['language_review']=='pending' and row['playtest']=='not_run' and row['bucket']=='qa'


def test_passed_qa_needs_payload_binding_and_evidence():
    c,v,q=fixture_data();m=q['records'][0]
    m['language_review']='reviewed';m['renderer_check']={'status':'passed'}
    assert queue(c,v,q)[0]['bucket']=='blocked'
    m['language_reviewer']='fixture-reviewer'
    m['layout_review']='reviewed';m['layout_reviewer']='fixture-reviewer'
    for stage in ('renderer_check','playtest'):m[stage]={'status':'passed','evidence':'fixture-report','target_sha256':'0'*64}
    assert queue(c,v,q)[0]['bucket']=='done'
    del m['translation_sha256']
    assert queue(c,v,q)[0]['qa_stale'] and queue(c,v,q)[0]['bucket']!='done'


def test_duplicates_stale_original_and_unknown_batch_fail_closed():
    c,v,q=fixture_data()
    with pytest.raises(FormatError,match='duplicate'):queue(c,v+v,q)
    v[0]['original_english']='Wrong source'
    with pytest.raises(FormatError,match='stale translation'):queue(c,v,q)
    with pytest.raises(FormatError,match='unknown batch'):select([],batch={'record_ids':['missing']})


def test_new_tools_batch_has_verified_sources_tokens_and_glossary_season():
    from fomt_text import check_translation
    root=Path(__file__).resolve().parents[1]
    rows=json.loads((root/'localization/vi/item_descriptions_tools.json').read_text())['records']
    assert len(rows)==16 and len({r['id'] for r in rows})==16
    for row in rows:
        assert row['source']['kind']=='pointer' and row['source']['pointer_offsets']
        assert row['translation_status']=='translated'
        check_translation(row['original_english'],row['vietnamese_translation'],28)
    glossary=json.loads((root/'localization/glossary.json').read_text())
    summer=next(t for t in glossary['terms'] if t['english']=='Summer' and t['category']=='new_game_ui')
    ui=json.loads((root/'localization/vi/new_game.json').read_text())['records']
    assert summer['vietnamese']==next(r['vietnamese_translation'] for r in ui if r['original_english']=='Summer')=='Hè'
