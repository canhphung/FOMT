#!/usr/bin/env python3
"""mGBA date UI checks: isolated setters plus natural calendar entry.

Calendar season/year cases alter the live UI object's view fields, then run
its native layout. They do not claim years of gameplay or modify save data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
import date_ui
from fomt_text import u32,verified_rom
from mgba_session import Session


def calendar_object(session):
    ram=session.read(0x02000000,0x40000)
    signature=struct.pack('<I',0x080E825C)
    found=[i-4 for i in range(4,len(ram)-0x228,4) if ram[i:i+4]==signature]
    assert len(found)==1,found
    return 0x02000000+found[0]


def expected_object(base,year,season,day,hour,minute,blink):
    """Independent native buffer layout; cache bits are tested against ROM digits."""
    obj=bytearray(b'\xA5'*0x35C)
    obj[0x84:0x184]=bytes(256);obj[0x1A8:0x2A8]=bytes(256)
    groups=date_ui.build_hud_cache(base)
    obj[0x84:0xE4]=groups['season'][season*96:(season+1)*96]
    weekday=((year+6)*120+season*30+day-1)%7
    suffix=groups['day_week'][((day-1)*7+weekday)*160:((day-1)*7+weekday+1)*160]
    obj[0xE4:0x104]=suffix[:32]
    obj[0x1A8:0x228]=suffix[32:]
    obj[0x124:0x184]=groups['hour'][hour*96:(hour+1)*96]
    obj[0x164:0x184]=groups['blink'][blink*32:(blink+1)*32]
    obj[0x228:0x268]=groups['minute'][minute*64:(minute+1)*64]
    obj[0x18C]=obj[0x2B0]=1
    return bytes(obj)


def probes(session,base):
    root=0x02038020;handle=0x0203B000;source=handle+16
    state=session.state();count=0
    def check(y,s,d,h,m,b):
        nonlocal count
        session.write(root-16,b'\xCC'*16+b'\xA5'*0x35C+b'\xCC'*16)
        session.write(handle,struct.pack('<I',root))
        session.write(source,bytes((y,s|((d-1)<<2)))+struct.pack('<H',h|(m<<5)))
        before=session.read(source,4)
        session.call(0x0803CD4C,handle,source,b)
        result=session.read(root-16,0x37C)
        assert result[:16]==result[-16:]==b'\xCC'*16
        assert result[16:-16]==expected_object(base,y,s,d,h,m,b),(y,s,d,h,m,b)
        assert session.read(source,4)==before,'HUD wrote to packed date/time'
        count+=1
    try:
        # Every native weekday cycle, season and day: 840 combinations.
        for y in range(1,8):
            for s in range(4):
                for d in range(1,31):check(y,s,d,6,50,1)
        # Every hour/minute including midnight, noon, 23:59; both colon phases.
        for h in range(24):
            for m in range(60):check(1,0,2,h,m,m%2)
        # Incremental callbacks must keep adjacent components/metadata intact.
        cache=date_ui.build_hud_cache(base)
        for key,values in [('season',range(4)),('hour',range(24)),('minute',range(60)),('blink',range(2))]:
            for value in values:
                check(1,0,2,6,50,1)
                before=session.read(root,0x35C);want=bytearray(before)
                if key=='season':want[0x84:0xE4]=cache[key][value*96:(value+1)*96]
                elif key=='hour':want[0x124:0x184]=cache[key][value*96:(value+1)*96]
                elif key=='minute':want[0x228:0x268]=cache[key][value*64:(value+1)*64]
                else:want[0x164:0x184]=cache[key][value*32:(value+1)*32]
                session.call(0x08000000+date_ui.HUD_SITES[key],handle,value)
                assert session.read(root,0x35C)==want,(key,value)
        for day in range(1,31):
            for weekday in range(7):
                check(1,0,2,6,50,1)
                want=bytearray(session.read(root,0x35C))
                p=cache['day_week'][((day-1)*7+weekday)*160:((day-1)*7+weekday+1)*160]
                want[0xE4:0x104]=p[:32];want[0x1A8:0x228]=p[32:]
                session.call(0x0803D0F0,handle,day,weekday)
                assert session.read(root,0x35C)==want,(day,weekday)
        return {'packed_date_time_cases_with_guards':count,'incremental_setter_cases':4+24+60+2+210,
                'packed_date_time_unchanged':True,'metadata_and_guard_bytes_unchanged':True}
    finally:session.restore(state)


def run(args):
    from PIL import Image
    out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
    base=verified_rom(args.base_rom);rom=args.rom.read_bytes()
    sessions=[Session(args.base_rom,args.library),Session(args.rom,args.library)]
    report={'target_sha256':hashlib.sha256(rom).hexdigest(),'revision':date_ui.REVISION,
            'limitations':['Calendar fixtures change UI view fields, not elapsed gameplay years',
                           'HUD game time still advances at native ten-minute ticks',
                           'No real hardware or full-season playthrough']}
    try:
        for session in sessions:session.frames(360)
        report['isolated_hud']=probes(sessions[1],base)
        house_states=[]
        for index,session in enumerate(sessions):
            session.load_sram(args.sram.read_bytes());session.lib.session_reset(session.handle);session.frames(360)
            session.press(8,settle=180);session.press(8,settle=360)
            session.press(1,settle=360);session.press(1,settle=360)
            session.screenshot(out/('hud-'+('native' if index==0 else 'vi')+'.png'))
            house_states.append(session.state())
            # Calendar is a wall interaction: stand at x168, face north, A.
            session.frames(24,16);session.frames(60,64);session.frames(30)
            session.press(1,settle=200)
            session.screenshot(out/('calendar-'+('native' if index==0 else 'vi')+'.png'))
        objects=[calendar_object(s) for s in sessions]
        states=[s.state() for s in sessions]
        checks=[];shots=[]
        # View-only HUD fixtures, then resume the original CPU context so the
        # native upload path puts the resulting tiles into actual OBJ VRAM.
        session=sessions[1]
        game=u32(session.read(objects[1]+8,4),0)
        hud_views=[]
        for season,day,hour,minute in ((0,2,6,50),(1,30,0,0),(2,30,12,0),(3,30,23,59),
                                            (0,9,6,0),(0,10,6,0),(1,2,6,0),(2,2,6,0),(3,2,6,0)):
            session.restore(house_states[1])
            ram=session.read(0x02000000,0x40000)
            signature=struct.pack('<I',0x080E77D0)
            roots=[i-0x70 for i in range(0x70,len(ram)-0x35C,4)
                   if ram[i:i+4]==signature and ram[i-0x70+0x198:i-0x70+0x19C]==signature]
            assert len(roots)==1,roots
            root=0x02000000+roots[0]
            packed_before=session.read(game+0x10,4)
            caller=session.state()
            handle=0x0203B000;source=handle+16
            session.write(handle,struct.pack('<I',root))
            session.write(source,bytes((1,season|((day-1)<<2)))+struct.pack('<H',hour|(minute<<5)))
            session.call(0x0803CD4C,handle,source,1)
            rendered=session.read(root,0x35C)
            session.restore(caller);session.write(root,rendered);session.frames(2)
            assert session.read(game+0x10,4)==packed_before
            vram=session.read(0x06010000,0x8000);oam=session.read(0x07000000,1024)
            for x,offset in ((132,0x84),(164,0x1A8)):
                tiles_found=[]
                for i in range(128):
                    a,b,c=struct.unpack_from('<HHH',oam,i*8)
                    if a&255==140 and b&511==x and a&0xC000==0x4000 and b&0xC000==0x8000:
                        tiles_found.append(c&1023)
                assert len(tiles_found)==1,tiles_found
                at=tiles_found[0]*32
                assert vram[at:at+256]==session.read(root+offset,256),'HUD tiles not uploaded through native path'
            name=f'hud-{season}-{hour:02d}{minute:02d}.png' if day==30 or (season==0 and day==2) else f'hud-{season}-day{day}.png'
            session.screenshot(out/name)
            hud_views.append({'season':season,'day':day,'hour':hour,'minute':minute,'screenshot':name})
        report['hud_view_fixtures_with_vram_checks']=hud_views
        for year in (1,7,8,10,99,100,200):
            for season in range(4):
                for day in (1,30):
                    pixels=[];fields=[]
                    for index,session in enumerate(sessions):
                        session.restore(states[index]);p=objects[index]
                        game=u32(session.read(p+8,4),0)
                        packed_before=session.read(game+0x10,4)
                        session.write(p+0x1DE,bytes((season|((day-1)<<2),)))
                        session.write(p+0x1E0,struct.pack('<hh',year-1,season))
                        # session.call is an isolated CPU probe and stops at a
                        # sentinel. Restore its calling context, carrying only
                        # the native layout result back into the live UI object.
                        caller = session.state()
                        session.call(0x080A303C,p)
                        laid_out = session.read(p,0x228)
                        session.restore(caller)
                        session.write(p,laid_out)
                        session.frames(12)
                        assert session.read(p+0x1E0,4)==struct.pack("<hh",year-1,season)
                        fields.append(session.read(p+0x1B4,0x42))
                        assert session.read(game+0x10,4)==packed_before,'calendar view changed game time'
                        raw=session.lib.session_pixels(session.handle)
                        import ctypes
                        pixels.append(ctypes.string_at(raw,240*160*4))
                        if index==1:
                            name=f'calendar-y{year}-{season}-{day}.png'
                            if year in (1,100,200):session.screenshot(out/name);shots.append(name)
                    assert fields[0]==fields[1],(year,season,day,'calendar grid/events changed')
                    assert pixels[0][40*240*4:]==pixels[1][40*240*4:],(year,season,day,'calendar body pixels changed')
                    checks.append({'year':year,'season':season,'selected_day':day,'grid_events_and_body_pixels_match_native':True})
        assert len({(out/name).read_bytes() for name in shots})>4, 'calendar fixtures did not reach the screen'
        sessions[1].restore(states[1]);sessions[1].press(2,settle=180)
        sessions[1].screenshot(out/'calendar-closed.png')
        assert sessions[1].sram()==args.sram.read_bytes(), 'calendar changed SRAM without an in-game save'
        report['calendar_exit_and_sram_unchanged']=True
        report['natural_calendar_entry']=True
        report['calendar_ui_fixtures']=checks
        report['calendar_source_tiles']=134;report['calendar_localized_tiles']=124
        report['calendar_tile_budget']=128
        report['screenshots']=shots
        # Selected native/translated screenshots for review, each at native scale.
        sheet=Image.new('RGB',(720,360),'#222')
        for i,name in enumerate(('calendar-native.png','calendar-vi.png','hud-vi.png',
                                  'calendar-y1-1-30.png','calendar-y1-2-30.png','calendar-y1-3-30.png')):
            sheet.paste(Image.open(out/name),(i%3*240,i//3*180))
        sheet.save(out/'date-overview.png')
        assert all(s.lib.session_errors()==0 for s in sessions)
        report['emulator_error_count']=0;report['status']='passed'
        return report
    finally:
        for session in sessions:session.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('--base-rom',type=Path,required=True)
    p.add_argument('--sram',type=Path,required=True);p.add_argument('--library',type=Path,default=Path('build/mgba_bridge.so'))
    p.add_argument('--output-dir',type=Path,default=Path('build/date-ui'))
    args=p.parse_args();report=run(args)
    (args.output_dir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('calendar_ui_fixtures','screenshots')},ensure_ascii=False))


if __name__=='__main__':main()
