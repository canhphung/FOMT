"""Actual object-label source guards, corpus coverage and mixed-script safety."""
import json,os
from pathlib import Path
import pytest
from fomt_text import FormatError,check_translation,encode,extract,parse_script,u32,SCRIPT_TABLE,ROM_BASE,verified_rom
from localization_queue import DEFAULT_TRANSLATIONS
import object_text

@pytest.fixture
def base():
    if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
    return verified_rom(os.environ['FOMT_ROM'])

def test_explicit_object_corpus_and_consistent_terms(base):
    contract=object_text.verify(base);cat={r['id']:r for r in extract(base)['records']}
    vi={r['id']:r for p in DEFAULT_TRANSLATIONS for r in json.loads(p.read_text())['records']}
    terms={};count=0
    for proof in contract['records']:
        row=cat[proof['id']];translated=vi[row['id']]
        assert row['context']=='interactive_object_label' and row['speaker'] is None
        assert translated['original_english']==row['original_english']
        check_translation(row['original_english'],translated['vietnamese_translation'],28)
        label=translated['vietnamese_translation'].removesuffix('{WAIT}').removesuffix('{CR}{LF}')
        assert terms.setdefault(proof['label_english'],label)==label
        count+=1
    assert count==261 and len(terms)==68
    assert vi['script.0351.001']['vietnamese_translation']=='Bàn{WAIT}'
    assert cat['script.0343.046']['context']=='interactive_object_label'
    assert cat['script.0343.000']['context']=='script_string_unclassified'
    assert cat['script.0483.004']['context']=='script_string_unclassified'

def test_changed_native_handler_and_literal_fail_closed(base):
    entry=object_text.contract()['records'][0];sid=entry['script_id']
    script=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
    for where in (0x3F904+33*4,script['address']+24,script['strings'][entry['string_index']]['address']):
        broken=bytearray(base);broken[where]^=1
        with pytest.raises(FormatError,match='object'):object_text.verify(broken)

def test_forged_display_site_rejected(base,monkeypatch):
    data=object_text.contract();data['records'][0]['show_text_sites'][0]['code_offset']+=1
    monkeypatch.setattr(object_text,'contract',lambda:data)
    with pytest.raises(FormatError,match='object display call mismatch'):object_text.verify(base)

def test_mixed_event_scripts_keep_code_jumps_and_nonlabel_strings(base):
    from text_inserter import build
    rows=[r for p in DEFAULT_TRANSLATIONS for r in json.loads(p.read_text())['records']]
    vi={r['id']:r for r in rows};target,_=build(base,{'rom_sha1':__import__('fomt_text').ROM_SHA1,'records':rows})
    for sid in (229,335,343,351,404,483):
        original=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
        inserted=parse_script(target,u32(target,SCRIPT_TABLE+sid*4)-ROM_BASE)
        for tag in (b'CODE',b'JUMP'):assert dict(original['chunks']).get(tag)==dict(inserted['chunks']).get(tag)
        assert len(original['strings'])==len(inserted['strings'])
        for a,b in zip(original['strings'],inserted['strings']):
            key=f"script.{sid:04d}.{a['index']:03d}"
            assert b['raw']==(encode(vi[key]['vietnamese_translation'],True) if key in vi else a['raw'])
