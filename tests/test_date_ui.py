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


def test_hud_cache_retains_original_clock_numerals_and_all_hour_minute_values(rom):
    cache=date_ui.build_hud_cache(rom)
    native=lambda n:rom[date_ui.DIGITS+32*n:date_ui.DIGITS+32*(n+1)]
    assert len(cache['season'])==4*96
    assert len(cache['day_week'])==30*7*160
    for hour in range(24):
        assert cache['hour'][hour*96:(hour+1)*96]==native(hour//10)+native(hour%10)+native(10)
    for minute in range(60):
        assert cache['minute'][minute*64:(minute+1)*64]==native(minute//10)+native(minute%10)


def test_date_suffix_has_no_empty_digit_slot_and_consistent_word_gaps():
    # Measure ink including shadow, not nominal glyph advances. All seasons end
    # at x23; every suffix starts at x27, irrespective of day/weekday/season.
    for season in date_ui.SEASONS:
        pixels=date_ui.season_pixels(season)
        assert max(x for row in pixels for x,v in enumerate(row) if v)==23
    for day in range(1,31):
        for weekday in date_ui.WEEKDAYS:
            pixels=date_ui.day_week_pixels(day,weekday)
            occupied=[any(row[x] for row in pixels) for x in range(40)]
            assert occupied.index(True)==3
            assert max(x for x,v in enumerate(occupied) if v)<40
            # Word gaps are exactly three transparent columns. This also
            # checks that the two-digit suffix moves its weekday naturally.
            runs=[];run=0
            for value in occupied[3:]:
                if not value:run+=1
                else:
                    if run:runs.append(run)
                    run=0
            assert runs.count(3)==2,(day,weekday,runs)
            assert all(n<=3 for n in runs)


@pytest.mark.parametrize('vowel',['â','ô','ạ','è'])
def test_hud_accents_centered_and_separated_from_body_and_shadow(vowel):
    # Check blank scanlines for the original marks; the user-selected grave
    # instead has a diagonal, horizontally centered placement in the 8px row.
    pixels=date_ui.tiny_pixels(vowel,8,16)
    mark_rows=(0,1) if vowel=='è' else ((0,1) if vowel!='ạ' else (8,))
    gap=1 if vowel=='è' else (2 if vowel!='ạ' else 7)
    if vowel!='è':assert not any(pixels[gap])
    mark_x=[x for y in mark_rows for x,v in enumerate(pixels[y]) if v==1]
    body_x=[x for y in range(3,6) for x,v in enumerate(pixels[y]) if v==1]
    assert mark_x and body_x
    if vowel=='è':
        assert pixels[0][3]==pixels[1][4]==1
        assert pixels[0][4]==pixels[0][5]==0  # previous horizontal stroke is gone
        glyph=date_ui.hud_glyph(vowel)
        assert sum(x for x,y in glyph.marks)==2*glyph.bearing_x+len(glyph.bitmap[0])-1
        assert glyph.marks[1][0]-glyph.marks[0][0]==1
        assert glyph.marks[1][1]-glyph.marks[0][1]==1
    else:
        assert min(mark_x)+max(mark_x)==min(body_x)+max(body_x)
    assert any(pixels[y][x]==1 for y in range(3,6) for x in range(4))


def test_summer_name_and_clock_position_are_restored_without_lower_accents():
    assert date_ui.SEASONS[1]=='Hè'
    assert date_ui.CLOCK_X==8
    for season in date_ui.SEASONS:
        pixels=date_ui.season_pixels(season)
        assert len(pixels)==8
    for char in 'XHĐThuânèôg0123456789CN':
        assert date_ui.hud_glyph(char).baseline==6


def test_hud_metrics_reject_clipping_and_use_integer_advances():
    with pytest.raises(FormatError):date_ui.tiny_pixels('ạ',8,8)
    with pytest.raises(FormatError):date_ui.tiny_pixels('XX',8)
    for char in '0123456789':assert date_ui.hud_glyph(char).advance==5
    assert date_ui.CLOCK_ADVANCE==8
    pixels=[[0]*40 for _ in range(8)]
    assert date_ui.draw_run('T2',pixels,3)==14


def test_e_counter_and_right_opening_stay_clear_of_shadow():
    for char in ('e','è'):
        pixels=date_ui.tiny_pixels(char,8)
        left=date_ui.hud_glyph(char).bearing_x
        assert pixels[3][left+1:left+3]==[0,0], 'Upper counter must remain transparent'
        assert pixels[5][left+1:left+4]==[0,0,0], 'Right opening must remain transparent'
        assert pixels[4][left:left+4]==[1,1,1,1], 'Middle bar must remain distinct'
        assert pixels[5][left]==1, 'Lower stem must be present below the middle bar'
        assert pixels[6][left+3]==1, 'Tail must include the requested bottom-right pixel'
        assert date_ui.hud_glyph(char).advance==5+left
        assert date_ui.hud_glyph(char).baseline==6
