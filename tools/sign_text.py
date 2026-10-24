"""Explicit signs/bulletin source contracts, including two padding-only reflows."""
import hashlib
import json
from pathlib import Path
from fomt_text import FormatError, ROM_BASE, SCRIPT_TABLE, decode, parse_script, u32
from npc_context import instructions
from object_text import HANDLERS, verify as verify_handlers

CONTRACT = Path(__file__).resolve().parents[1]/'localization/signs.json'


def verify(base):
    base = bytes(base)
    verify_handlers(base)
    data = json.loads(CONTRACT.read_text())
    if data['schema_version'] != 1 or data['record_ids'] != [r['id'] for r in data['source_proofs']] or len(set(data['record_ids'])) != len(data['record_ids']):
        raise FormatError('invalid sign contract')
    scripts = {}
    for row in data['source_proofs']:
        sid, index = row['script_id'],row['string_index']
        if row['id'] != f'script.{sid:04d}.{index:03d}':
            raise FormatError('sign ID mismatch')
        if sid not in scripts:
            script = parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
            code = dict(script['chunks'])[b'CODE'][4:]
            scripts[sid] = script,code,list(instructions(code))
        script,code,ins = scripts[sid]
        if hashlib.sha256(code).hexdigest() != row['code_sha256'] or decode(script['strings'][index]['raw']) != row['original_english']:
            raise FormatError('sign source mismatch: '+row['id'])
        sites = [{'code_offset':pc,'native_call':arg,'text_flags':{33:256,34:64,35:0}[arg]}
                 for j,(pc,op,arg) in enumerate(ins) if op == 0x21 and arg in HANDLERS and j
                 and ins[j-1][1] in (0x17,0x22,0x23) and ins[j-1][2] == index]
        if sites != row['show_text_sites']:
            raise FormatError('sign display site mismatch')
        if row['kind'] == 'frisbee_choice':
            # Exact contiguous stack arguments: header index 1, choices 2 and 3.
            sequence = [(608,0x23,0),(610,0x23,1),(612,0x23,2),(614,0x23,3),(616,0x21,36)]
            if sid != 492 or index not in (1,2,3) or not all(x in ins for x in sequence):
                raise FormatError('sign choice call mismatch')
        elif not sites:
            raise FormatError('sign missing display call')
        if row['padding_reflow'] and row['id'] not in ('script.0497.000','script.0507.000'):
            raise FormatError('unverified sign padding permission')
    return data


def annotate_records(base,records):
    proofs = {r['id']:r for r in verify(base)['source_proofs']}
    found = set()
    for row in records:
        proof = proofs.get(row['id'])
        if proof is None:
            continue
        if row['original_english'] != proof['original_english']:
            raise FormatError('sign catalog mismatch')
        row['context'] = proof['kind']
        row['speaker'] = None
        row['source']['sign_context'] = {'code_sha256':proof['code_sha256'],
            'display_sites':proof['show_text_sites'],'padding_reflow':proof['padding_reflow']}
        row['source']['context_reference'] = 'localization/signs.json; docs/SIGN_LOCALIZATION.md'
        found.add(row['id'])
    if found != proofs.keys():
        raise FormatError('missing classified sign')
