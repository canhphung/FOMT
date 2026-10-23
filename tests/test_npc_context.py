"""NPC source provenance, exact dialogue coverage and native branch boundaries."""
import json
import os
from pathlib import Path
import pytest
from fomt_text import FormatError, ROM_BASE, SCRIPT_TABLE, check_translation, extract, u32, verified_rom
from npc_context import SPECS, script_parts, thomas_route, witnesses

@pytest.fixture
def base():
    if not os.environ.get('FOMT_ROM'):pytest.skip('legally supplied ROM required')
    return verified_rom(os.environ['FOMT_ROM'])

def test_npc_attribution_requires_actor_literal_and_exact_code(base):
    for sid,(_,literal,_,_) in SPECS.items():
        script,_,_=script_parts(base,sid)
        for at in (literal,script['address']+24):
            broken=bytearray(base);broken[at]^=1
            with pytest.raises(FormatError,match='identity mismatch'):script_parts(broken,sid)

def test_only_verified_npc_scopes_are_classified_and_translated(base):
    catalog={r['id']:r for r in extract(base)['records']}
    vi={r['id']:r for r in json.load(open('localization/vi/pilot.json'))['records']}
    assert len(witnesses(base))==85
    for proof in witnesses(base):
        row=catalog[proof['id']];translated=vi[row['id']]
        assert row['speaker']==proof['speaker']==translated['speaker']
        assert translated['original_english']==row['original_english']
        assert row['source']['npc_context']['show_text_code_offsets']
        check_translation(row['original_english'],translated['vietnamese_translation'],28)
    assert catalog['script.0993.092']['context']=='script_string_unclassified'
    assert catalog['script.0993.001']['context']=='script_string_unclassified'
    assert catalog['script.0993.000']['speaker']=='Popuri'

def test_thomas_three_friendship_bands_and_repeat_dialogue(base):
    for state in (14,15,30):
        for friendship,first in ((0,20),(100,20),(101,22),(200,22),(201,24),(255,24)):
            for repeat in (False,True):
                result=thomas_route(base,state,friendship,repeat)
                assert result['record_ids']==[f'script.1017.{first+int(repeat):03d}']

def test_thomas_weather_and_hour_boundaries(base):
    # Script state 5 uses actual OnCall61 keys 3(hour) and 6(weather).
    assert thomas_route(base,5,50,False,13,0)['record_ids']==['script.1017.015','script.1017.016']
    assert thomas_route(base,5,50,False,13,1)['record_ids']==['script.1017.017']
    assert thomas_route(base,5,50,False,16,1)['record_ids']==['script.1017.014']
    assert thomas_route(base,5,50,False,10,0)['record_ids']==['script.1017.018']
    assert thomas_route(base,5,50,False,9,0)['record_ids']==['script.1017.019']
    assert thomas_route(base,21,100,False)['record_ids']==['script.1017.030']
    assert thomas_route(base,21,101,True)['record_ids']==['script.1017.033']

def test_npc_pronoun_scopes_do_not_leak_to_spouse_dialogue(base):
    profiles=json.load(open('localization/character_profiles.json'))['profiles']
    for proof in witnesses(base):
        match=[p for p in profiles if proof['id'] in p['source_ids']]
        assert len(match)==1
        assert (match[0]['self'],match[0]['player'])==(('bác','cháu') if proof['speaker']=='Thomas' else ('mình','bạn'))
    assert not any('script.0993.092' in p['source_ids'] for p in profiles)
