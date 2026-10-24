"""Explicit ROM-backed examined-object labels, not automatic noun replacement."""
import hashlib
import json
from pathlib import Path
from fomt_text import FormatError, ROM_BASE, SCRIPT_TABLE, parse_script, u32
from npc_context import instructions

CONTRACT = Path(__file__).resolve().parents[1] / 'localization/object_labels.json'
HANDLERS = {33:(0x405DC,0x40628),34:(0x4053E,0x40588),35:(0x4058C,0x405D8)}


def contract():
    data=json.loads(CONTRACT.read_text())
    if data['schema_version']!=1:raise FormatError('unsupported object label contract')
    return data


def verify(base):
    data=contract();scripts={};seen=set()
    for call,(start,end) in HANDLERS.items():
        if u32(base,0x3F904+call*4)!=ROM_BASE+start or hashlib.sha256(base[start:end]).hexdigest()!=data['native_handler_sha256'][str(call)]:
            raise FormatError('object native display handler mismatch')
    for sid,expected in data['script_code_sha256'].items():
        sid=int(sid);script=parse_script(bytes(base),u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE)
        code=dict(script['chunks'])[b'CODE'][4:]
        if hashlib.sha256(code).hexdigest()!=expected:raise FormatError('object script CODE mismatch: '+str(sid))
        scripts[sid]=(script,list(instructions(code)))
    for row in data['records']:
        sid,index=row['script_id'],row['string_index']
        if row['id']!=f'script.{sid:04d}.{index:03d}' or row['id'] in seen:raise FormatError('invalid/duplicate object label ID')
        seen.add(row['id']);script,ins=scripts[sid]
        from fomt_text import decode
        if index>=len(script['strings']) or decode(script['strings'][index]['raw'])!=row['original_english']:
            raise FormatError('object literal mismatch: '+row['id'])
        actual=[]
        for j,(pc,op,arg) in enumerate(ins):
            if op==0x21 and arg in HANDLERS and j and ins[j-1][1] in (0x17,0x22,0x23) and ins[j-1][2]==index:
                actual.append({'code_offset':pc,'native_call':arg,'text_flags':{33:256,34:64,35:0}[arg]})
        if not actual or actual!=row['show_text_sites']:raise FormatError('object display call mismatch: '+row['id'])
    return data


def annotate_records(base,records):
    data=verify(base);labels={r['id']:r for r in data['records']}
    found=set()
    for row in records:
        if row['id'] not in labels:continue
        proof=labels[row['id']]
        if row['original_english']!=proof['original_english']:raise FormatError('object catalog source mismatch')
        row['context']='interactive_object_label';row['speaker']=None
        row['source']['object_context']={'label_english':proof['label_english'],'show_text_sites':proof['show_text_sites'],'code_sha256':data['script_code_sha256'][str(proof['script_id'])]}
        row['source']['context_reference']='object_text.py; localization/object_labels.json; docs/INTERACTIVE_OBJECTS.md'
        found.add(row['id'])
    if found!=labels.keys():raise FormatError('missing classified object labels')
