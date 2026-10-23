"""ROM-backed daily dialogue witnesses; no attribution by English keyword.

Actor constructor script literals, exact CODE hashes and native ShowText
call sites bind the scopes below. Thomas route probes interpret actual CODE
for selected map IDs; they are not full-game event simulation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
from fomt_text import FormatError, ROM_BASE, SCRIPT_TABLE, parse_script, u32, verified_rom

SPECS = {
    1017: ('Thomas', 0x361B8, '3b54ec6e358611a1dbc059c085e7dfe3abb48e94d75d20129b9644b73d1ac3ba', range(34)),
    993: ('Popuri', 0x35BFC, '3f11878d5c486bf852cdadbfc40cfac3e3e4c6e5bbf815885c4a6a767c1d8bd9', range(93, 144)),
}
WIDE = {0x13,0x14,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x21,0x24}


def instructions(code):
    pc = 0
    while pc < len(code):
        op = code[pc]
        if op > 0x24:
            raise FormatError('unsupported NPC opcode/relative flag')
        width = 5 if op in WIDE else 3 if op == 0x22 else 2 if op == 0x23 else 1
        if pc + width > len(code):
            raise FormatError('truncated NPC instruction')
        yield pc, op, int.from_bytes(code[pc+1:pc+width], 'little') if width > 1 else None
        pc += width


def script_parts(base, sid):
    actor, literal, expected, _ = SPECS[sid]
    if u32(base, literal) != sid:
        raise FormatError('NPC constructor script identity mismatch: ' + actor)
    script = parse_script(bytes(base), u32(base, SCRIPT_TABLE + sid * 4) - ROM_BASE)
    chunks = dict(script['chunks'])
    code = chunks[b'CODE'][4:]
    if hashlib.sha256(code).hexdigest() != expected:
        raise FormatError('NPC CODE identity mismatch: ' + actor)
    return script, code, chunks[b'JUMP'][4:]


def speech_sites(code):
    sites = {}
    previous = None
    for pc, op, arg in instructions(code):
        # Native OnCall 33 -> 080405DC -> GetString -> 0801268C.
        if op == 0x21 and arg == 33 and previous and previous[1] in (0x17,0x22,0x23):
            sites.setdefault(previous[2], []).append(pc)
        previous = pc, op, arg
    return sites


def witnesses(base):
    rows = []
    for sid, (actor, literal, _, indexes) in SPECS.items():
        script, code, jump = script_parts(base, sid)
        sites = speech_sites(code)
        for index in indexes:
            if index not in sites or index >= len(script['strings']):
                raise FormatError('missing verified native dialogue call')
            rows.append({'id': f'script.{sid:04d}.{index:03d}', 'speaker': actor,
                'script_id': sid, 'constructor_literal': hex(ROM_BASE + literal),
                'show_text_code_offsets': [hex(pc) for pc in sites[index]],
                'code_sha256': hashlib.sha256(code).hexdigest(),
                'scope': 'all 34 strings of Thomas standard NPC script' if sid == 1017 else 'adult daily dialogue 93..143; spouse/home 1..92 excluded; full trigger gates pending',
                'condition_status': 'map/friendship/time/weather probes available' if sid == 1017 and index >= 14 else 'speaker and dialogue call verified; full trigger path not yet replayed'})
    return rows


def annotate_records(base, records):
    verified = {r['id']: r for r in witnesses(base)}
    for row in records:
        if row['id'] in verified:
            proof = verified[row['id']]
            row['context'] = 'npc_standard_gift_dialogue' if proof['script_id'] == 1017 and row['source']['string_index'] < 12 else 'npc_daily_dialogue'
            row['speaker'] = proof['speaker']
            row['source']['npc_context'] = proof
            row['source']['context_reference'] = 'npc_context.py; docs/NPC_DAILY_LOCALIZATION.md'


def thomas_route(base, map_id, friendship, spoken_just_now, hour=12, weather=0):
    """Execute verified Thomas CODE from the ordinary-talk dispatch, read-only.

    Native OnCall 20 = actor current map ID (08012134 -> AEntity +4), 61(3) = hour,
    124(13) = GetFriendship, 130(13) = HasBeenSpokenToJustNow.
    No synthetic dialogue, guessed season predicate or game-state writes.
    """
    _, code, jump = script_parts(base, 1017)
    ins = {pc:(op,arg) for pc,op,arg in instructions(code)}
    pc, stack, shown, trace = 0x7A2, [], [], []
    for _ in range(500):
        if pc == 0xB2E:
            return {'map_id':map_id,'friendship':friendship,'spoken_just_now':spoken_just_now,'hour':hour, 'weather_raw':weather,
                    'record_ids':[f'script.1017.{i:03d}' for i in shown], 'native_queries':trace}
        op,arg = ins[pc]
        next_pc = pc + (5 if op in WIDE else 3 if op == 0x22 else 2 if op == 0x23 else 1)
        if op in (0x17,0x22,0x23):stack.append(arg)
        elif op == 0x12:
            b,a=stack.pop(),stack.pop();stack.append((a>b)-(a<b))
        elif op in (0x0C,0x0D):
            b,a=stack.pop(),stack.pop();stack.append(int(bool(a and b) if op==0x0C else bool(a or b)))
        elif op == 0x18:next_pc=arg
        elif 0x19 <= op <= 0x1E:
            v=stack.pop()
            if {0x19:v<0,0x1A:v<=0,0x1B:v==0,0x1C:v!=0,0x1D:v>=0,0x1E:v>0}[op]:next_pc=arg
        elif op == 0x24:
            value=stack.pop();at=u32(jump,arg*4);n,default=struct.unpack_from('<II',jump,at)
            table=dict(struct.iter_unpack('<iI',jump[at+8:at+8+n*8]))
            next_pc=table.get(value,default if 0<default<0x80000000 else next_pc)
        elif op == 0x21:
            value=stack.pop()
            if arg in (20,61,124,130):
                expected=(3,6) if arg==61 else (13,)
                if value not in expected:raise FormatError(f'unexpected native query argument {arg}({value}) at {pc:x}')
                result={20:map_id,61:(hour if value==3 else weather),124:friendship,130:int(spoken_just_now)}[arg]
                stack.append(result);trace.append({'code_offset':hex(pc),'call':arg,'argument':value,'result':result})
            elif arg==33:shown.append(value)
            elif arg!=47:raise FormatError('unmodelled Thomas native call: '+str(arg))
        else:raise FormatError('unmodelled Thomas route opcode: '+str(op))
        pc=next_pc
    raise FormatError('Thomas route did not terminate')


def branch_matrix(base):
    return [thomas_route(base,state,f,spoken,hour,weather) for state in (5,6,14,15,21,30)
            for f in (0,100,101,200,201,255) for spoken in (False,True) for hour in (9,10,12,13,15,16) for weather in (0,1)]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=Path('build/npc-context.json'))
    args=p.parse_args();base=verified_rom(args.rom)
    if args.rom.resolve()==args.output.resolve():p.error('output must not overwrite ROM')
    routes=branch_matrix(base)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'schema_version':1,'witnesses':witnesses(base),'thomas_routes':routes,
        'limitations':['Branch probes interpret source CODE; no natural encounter or full seasonal simulation claimed.','Unresolved triggers are retained as unresolved, not inferred from English keywords.']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'verified_dialogue_records':len(witnesses(base)),'thomas_branch_cases':len(routes)}))


if __name__=='__main__':main()
