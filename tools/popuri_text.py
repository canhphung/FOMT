"""Narrow source-verified punctuation exception and choice context for Popuri."""
from pathlib import Path
from npc_context import script_parts
from sign_text import verify
CONTRACT=Path(__file__).resolve().parents[1]/'localization/popuri_context.json'
DROP_IDS={'script.0993.005','script.0993.021','script.0993.092'}
def annotate_records(base,records):
 script_parts(base,993)
 proof=verify(base,CONTRACT);ids=set(proof['record_ids'])
 for row in records:
  if row['id'] not in ids:continue
  choice=row['id'] in ('script.0993.038','script.0993.039')
  row['context']='popuri_player_choice' if choice else 'popuri_standard_dialogue'
  row['speaker']=None if choice else 'Popuri'
  row['source']['popuri_context']={'drop_apostrophe':row['id'] in DROP_IDS,'reference':'localization/popuri_context.json; docs/POPURI_LOCALIZATION.md'}
  if choice:
   row['max_columns']=26
   row['max_encoded_bytes']=26
