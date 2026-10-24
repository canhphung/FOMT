#!/usr/bin/env python3
"""Export a context/QA queue without modifying translations or approving them.

Only a newly extracted catalog supplies original text and source addresses.
Manual QA is bound to exact source/translation hashes; changed text goes stale.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from fomt_text import FormatError,check_translation,encode

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_TRANSLATIONS=tuple(ROOT/'localization/vi'/name for name in
    ('pilot.json','items.json','new_game.json','intro.json','start_menu.json','item_descriptions_tools.json','signs.json'))
FIELDS=('id','bucket','context_status','context','speaker','original_english',
        'vietnamese_translation','translation_status','language_review','renderer_check',
        'playtest','layout_review','source_reference','control_codes','blocked_reason','qa_stale')


def digest(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()


def index_records(records,label):
    result={}
    for row in records:
        identifier=row['id']
        if identifier in result:raise FormatError(f'duplicate {label} ID: {identifier}')
        result[identifier]=row
    return result


def queue(catalog,translations,registry):
    originals=index_records(catalog['records'],'catalog')
    vi=index_records(translations,'translation');qa=index_records(registry['records'],'QA')
    unknown=(vi.keys()|qa.keys())-originals.keys()
    if unknown:raise FormatError('unknown ID: '+sorted(unknown)[0])
    result=[]
    for identifier,original in originals.items():
        translated=vi.get(identifier,{})
        if translated and translated['original_english']!=original['original_english']:
            raise FormatError('stale translation source: '+identifier)
        text=translated.get('vietnamese_translation','')
        manual=qa.get(identifier,{})
        stale_source=bool(manual and manual.get('source_sha256')!=digest(original['original_english']))
        stale_text=bool(manual.get('translation_sha256') and manual['translation_sha256']!=digest(text))
        claimed=manual.get('language_review')=='reviewed' or manual.get('layout_review')=='reviewed' or any(manual.get(k,{}).get('status')=='passed' for k in ('renderer_check','playtest'))
        stale=stale_source or stale_text or bool(claimed and not manual.get('translation_sha256'))
        context=original['context']
        evidence=translated.get('context_evidence','')
        # Existing classified catalog entries have provenance in the extractor.
        status='needs_context' if context=='script_string_unclassified' else 'verified'
        if status=='needs_context' and evidence:status='documented'
        if manual and not stale_source:
            status=manual.get('context_status',status)
            if status=='verified' and not manual.get('context_evidence'):
                raise FormatError('verified QA context needs evidence: '+identifier)
        elif stale_source:status='needs_context'
        errors=[]
        if manual.get('language_review')=='reviewed' and not manual.get('language_reviewer'):
            errors.append('Language review needs a named reviewer.')
        if manual.get('layout_review')=='reviewed' and not manual.get('layout_reviewer'):
            errors.append('Layout review needs a named reviewer.')
        for stage in ('renderer_check','playtest'):
            proof=manual.get(stage,{})
            if proof.get('status')=='passed' and (not proof.get('evidence') or not proof.get('target_sha256')):
                errors.append(stage+' needs an evidence path and target ROM hash.')
        if translated.get('translation_status') in ('translated','reviewed') and not text:
            errors.append('Active translation is empty.')
        if text:
            try:
                check_translation(original['original_english'],text,original['max_columns'],
                    padding_reflow=original.get('source',{}).get('sign_context',{}).get('padding_reflow',False))
                if len(encode(text,True))>original.get('max_encoded_bytes',1<<30):
                    raise FormatError('exceeds encoded-byte limit before rendering')
            except FormatError as exc:errors.append(str(exc))
        language='stale' if stale else manual.get('language_review','pending')
        renderer='stale' if stale else manual.get('renderer_check',{}).get('status','not_run')
        layout='stale' if stale else manual.get('layout_review','pending')
        playtest='stale' if stale else manual.get('playtest',{}).get('status','not_run')
        reason=manual.get('blocked_reason','')
        if status!='verified':reason=reason or 'Verify speaker/function/context before translating.'
        if errors:reason='; '.join(errors)
        if reason:bucket='blocked'
        elif not text:bucket='translate'
        elif language=='reviewed' and layout=='reviewed' and renderer=='passed' and playtest=='passed':bucket='done'
        else:bucket='qa'
        source=original.get('source',{})
        result.append({'id':identifier,'bucket':bucket,'context_status':status,
            'context':context,'speaker':translated.get('speaker') or original.get('speaker'),
            'original_english':original['original_english'],'vietnamese_translation':text,
            'translation_status':translated.get('translation_status','untranslated'),
            'language_review':language,'renderer_check':renderer,'playtest':playtest,'layout_review':layout,
            'source_reference':source.get('reference',original.get('rom_address','')),
            'rom_address':original.get('rom_address'),'source':source,
            'control_codes':original.get('control_codes',[]),'blocked_reason':reason,
            'validation_errors':errors,'qa_stale':stale,
            'context_evidence':manual.get('context_evidence',evidence),
            'source_sha256':digest(original['original_english']), 'translation_sha256':digest(text) if text else None})
    return result


def select(rows,*,batch=None,bucket=None,context=None,speaker=None,limit=None):
    if batch is not None:
        ids=batch['record_ids']
        if len(ids)!=len(set(ids)):raise FormatError('duplicate batch ID')
        missing=set(ids)-{r['id'] for r in rows}
        if missing:raise FormatError('unknown batch ID: '+sorted(missing)[0])
        indexed={r['id']:r for r in rows};rows=[indexed[i] for i in ids]
    rows=[r for r in rows if (not bucket or r['bucket']==bucket)
          and (not context or r['context']==context) and (not speaker or r['speaker']==speaker)]
    return rows if limit is None else rows[:limit]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,default=ROOT/'localization/en/catalog.json')
    p.add_argument('--translations',type=Path,nargs='+',default=DEFAULT_TRANSLATIONS)
    p.add_argument('--qa',type=Path,default=ROOT/'localization/qa/records.json')
    p.add_argument('--batch',type=Path)
    p.add_argument('--bucket',choices=('translate','qa','blocked','done'))
    p.add_argument('--context');p.add_argument('--speaker');p.add_argument('--limit',type=int)
    p.add_argument('--output',type=Path,default=ROOT/'build/localization-queue.json')
    p.add_argument('--csv',type=Path)
    args=p.parse_args()
    if args.limit is not None and args.limit<0:p.error('--limit must be nonnegative')
    inputs=[args.catalog,args.qa,*args.translations,*([args.batch] if args.batch else [])]
    outputs=[args.output,*([args.csv] if args.csv else [])]
    if len({p.resolve() for p in outputs})!=len(outputs) or {p.resolve() for p in inputs}&{p.resolve() for p in outputs}:
        p.error('outputs must be distinct and must not overwrite inputs')
    try:
        read=lambda path:json.loads(path.read_text(encoding='utf-8'))
        catalog=read(args.catalog)
        rows=queue(catalog,[r for path in args.translations for r in read(path)['records']],read(args.qa))
        rows=select(rows,batch=read(args.batch) if args.batch else None,bucket=args.bucket,
                    context=args.context,speaker=args.speaker,limit=args.limit)
        counts={state:sum(r['bucket']==state for r in rows) for state in ('translate','qa','blocked','done')}
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps({'schema_version':1,'summary':counts,'records':rows},ensure_ascii=False,indent=2)+'\n')
        if args.csv:
            args.csv.parent.mkdir(parents=True,exist_ok=True)
            with args.csv.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');writer.writeheader()
                for row in rows:
                    item={**row,'control_codes':' '.join(row['control_codes'])}
                    # Spreadsheet imports must not turn user-edited cells into formulas.
                    writer.writerow({k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for k,v in item.items()})
        print(json.dumps({'records':len(rows),**counts},ensure_ascii=False))
    except (OSError,ValueError,KeyError) as exc:p.exit(1,f'error: {exc}\n')


if __name__=='__main__':main()
