"""Display-only date assets/hooks: verified sources and bounded OBJ resources."""
import hashlib
import os
import struct
from pathlib import Path
import pytest
from fomt_text import FormatError,verified_rom
import date_ui


@pytest.fixture(scope='module')
def rom():
    path=os.environ.get('FOMT_ROM')
    if not path:pytest.skip('set FOMT_ROM to the legally supplied USA rev 0 ROM')
    return verified_rom(path)


@pytest.mark.parametrize('site',[*date_ui.HUD_SITES.values(),date_ui.DIGITS,date_ui.CALENDAR_POINTER,
                                date_ui.CALENDAR_ASSET,date_ui.CALENDAR_HEADER_SITE,date_ui.CALENDAR_WEEK_X_SITE])
def test_reject_changed_source(rom,site):
    bad=bytearray(rom);bad[site]^=1
    with pytest.raises(FormatError):
        date_ui.build_hud_cache(bad)
        date_ui.build_calendar_asset(bad)


def sections(asset):
    out=[];at=0
    for stride in (4,16,8,32,32,8,4):
        count=struct.unpack_from('<I',asset,at)[0]
        out.append(asset[at+4:at+4+count*stride]);at+=4+count*stride
    assert at==len(asset)
    return out


def test_calendar_preserves_numbers_palettes_animation_and_fits_native_reservation(rom):
    original=sections(rom[date_ui.CALENDAR_ASSET:date_ui.CALENDAR_ASSET+date_ui.CALENDAR_ASSET_SIZE])
    translated=sections(date_ui.build_calendar_asset(rom))
    for index in (0,2,4,5,6):assert translated[index]==original[index]
    assert translated[1][:10*16]==original[1][:10*16]
    assert translated[3][:40*32]==original[3][:40*32]
    assert len(translated[3])//32==124<=128
    for i in range(22):
        frame=struct.unpack_from('<8H',translated[1],i*16)
        assert (frame[3]+frame[2])*32<=len(translated[3])
        assert frame[0]+frame[1]<=9


def test_hud_cache_retains_original_numerals_and_all_day_hour_minute_values(rom):
    cache=date_ui.build_hud_cache(rom)
    native=lambda n:rom[date_ui.DIGITS+32*n:date_ui.DIGITS+32*(n+1)]
    assert len(cache['season'])==4*96
    assert len(cache['week'])==7*96
    for hour in range(24):
        assert cache['hour'][hour*96:(hour+1)*96]==native(hour//10)+native(hour%10)+native(10)
    for minute in range(60):
        assert cache['minute'][minute*64:(minute+1)*64]==native(minute//10)+native(minute%10)
    for day in range(1,31):
        assert cache['day'][(day-1)*64:day*64]==(native(day//10) if day>=10 else bytes(32))+native(day%10)
