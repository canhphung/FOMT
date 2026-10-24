"""Source-verified four Popuri heart events, speakers, choices and response blocks."""
import hashlib,json,struct
from pathlib import Path
from fomt_text import FormatError,ROM_BASE,SCRIPT_TABLE,decode,parse_script,u32,cstring
from npc_context import instructions
CONTRACT=Path(__file__).resolve().parents[1]/'localization/popuri_heart_events.json'
NAME_TABLE=0x104258

def verify(base):
 base=bytes(base);p=json.loads(CONTRACT.read_text());scripts={};found={}
 if p['record_ids']!=[r['id'] for r in p['source_proofs']]:raise FormatError('heart event IDs mismatch')
 if hashlib.sha256(base[NAME_TABLE:NAME_TABLE+43*8]).hexdigest()!=p['name_table_sha256']:raise FormatError('heart event name table mismatch')
 for key,name in p['speaker_names'].items():
  at=u32(base,NAME_TABLE+int(key)*8)-ROM_BASE
  if cstring(base,at,at+30).decode('ascii')!=name:raise FormatError('heart event speaker name mismatch')
 for call,row in p['native_handlers'].items():
  start=row['start']
  if u32(base,0x3F904+int(call)*4)!=ROM_BASE+start or hashlib.sha256(base[start:start+32]).hexdigest()!=row['sha256']:raise FormatError('heart event native handler mismatch')
 for sid,hashes in p['scripts'].items():
  sid=int(sid);s=parse_script(base,u32(base,SCRIPT_TABLE+sid*4)-ROM_BASE);chunks=dict(s['chunks']);code=chunks[b'CODE'][4:]
  if hashlib.sha256(code).hexdigest()!=hashes['CODE_sha256'] or hashlib.sha256(chunks[b'JUMP']).hexdigest()!=hashes['JUMP_sha256']:raise FormatError('heart event CODE/JUMP mismatch')
  ins=list(instructions(code));speaker=None;name_pc=None;sites={};who={}
  for j,(pc,op,arg) in enumerate(ins):
   if op==33 and arg==44 and j and ins[j-1][1] in (23,34,35):speaker=ins[j-1][2];name_pc=pc
   if op==33 and arg==33 and j and ins[j-1][1] in (23,34,35):
    index=ins[j-1][2];sites.setdefault(index,[]).append({'code_offset':pc,'native_call':33,'text_flags':256});who.setdefault(index,[]).append({'speaker_id':speaker,'speaker':p['speaker_names'][str(speaker)],'name_call_offset':name_pc})
  scripts[sid]=(s,chunks,ins,sites,who)
 for row in p['source_proofs']:
  sid,index=row['script_id'],row['string_index'];s,chunks,ins,sites,who=scripts[sid]
  if row['id']!=f'script.{sid:04d}.{index:03d}' or row['id'] in found or decode(s['strings'][index]['raw'])!=row['original_english']:raise FormatError('heart event literal/ID mismatch')
  if row['show_text_sites']!=sites.get(index,[]) or row['speaker_sites']!=who.get(index,[]):raise FormatError('heart event speaker/display site mismatch')
  choice=any(g['script_id']==sid and index in g['choice_indices'] for g in p['choice_groups'])
  expected_speaker=None if choice else ' / '.join(sorted({x['speaker'] for x in who.get(index,[])}))
  if row['speaker']!=expected_speaker or row['kind']!=('heart_event_choice' if choice else 'heart_event_dialogue'):raise FormatError('heart event speaker/kind mismatch')
  if row['drop_apostrophe'] != (row['id']=='script.0038.026'):raise FormatError('heart event punctuation permission mismatch')
  found[row['id']]=row
 for g in p['choice_groups']:
  s,chunks,ins,sites,who=scripts[g['script_id']];at=next(i for i,x in enumerate(ins) if x[0]==g['code_offset']);n=len(g['choice_indices']);previous=ins[at-n:at]
  if ins[at][1:]!=(33,g['native_call']) or [x[2] for x in previous]!=g['choice_indices'] or [x[0] for x in previous]!=g['choice_push_offsets'] or not all(x[1] in (23,34,35) for x in previous):raise FormatError('heart event choice arguments mismatch')
  switch=next(x for x in ins[at:] if x[1]==36);jump=chunks[b'JUMP'][4:];table=u32(jump,switch[2]*4);num,default=struct.unpack_from('<II',jump,table);routes=[{'value':v,'target':t} for v,t in struct.iter_unpack('<iI',jump[table+8:table+8+num*8])]
  if routes!=g['routes'] or switch[0]!=g['switch_offset'] or switch[2]!=g['switch_index']:raise FormatError('heart event choice routes mismatch')
 return p

def annotate_records(base,records):
 p=verify(base);by={r['id']:r for r in p['source_proofs']}
 for row in records:
  r=by.get(row['id'])
  if r is None:continue
  row['context']='popuri_'+r['kind'];row['speaker']=r['speaker']
  row['source']['heart_event_context']={'speaker_sites':r['speaker_sites'],'show_text_sites':r['show_text_sites'],'reference':'localization/popuri_heart_events.json; docs/POPURI_HEART_EVENTS.md'}
  if r['drop_apostrophe']:row['source']['popuri_context']={'drop_apostrophe':True,'reference':'popuri_heart_events.py exact 38.026 source guard'}
  if r['kind']=='heart_event_choice':row['max_columns']=26;row['max_encoded_bytes']=26

def response_blocks(base):
 """Describe source response regions; do not emulate world-state side effects."""
 p=verify(base);result=[]
 for g in p['choice_groups']:
  sid=g['script_id'];rows=[r for r in p['source_proofs'] if r['script_id']==sid]
  targets=[r['target'] for r in g['routes']]
  for route in g['routes']:
   start=route['target'];stop=min([t for t in targets if t>start]+[g['switch_offset']])
   ids=[r['id'] for r in rows if any(start<=s['code_offset']<stop for s in r['show_text_sites'])]
   result.append({'script_id':sid,'selection':route['value'],'entry_code_offset':start,'end_before':stop,'dialogue_ids':ids})
 return result
