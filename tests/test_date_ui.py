"""Display-only date assets/hooks: verified sources and bounded OBJ resources."""
import hashlib
import os
import struct
from pathlib import Path
import pytest
from fomt_text import FormatError,verified_rom
import date_ui
import hud_accent
import calendar_layout


@pytest.fixture(scope='module')
def rom():
    path=os.environ.get('FOMT_ROM')
    if not path:pytest.skip('set FOMT_ROM to the legally supplied USA rev 0 ROM')
    return verified_rom(path)


@pytest.mark.parametrize('site',[*date_ui.HUD_SITES.values(),date_ui.DIGITS,date_ui.CALENDAR_POINTER,
                                date_ui.CALENDAR_ASSET,date_ui.CALENDAR_HEADER_SITE,date_ui.CALENDAR_WEEK_X_SITE,
                                *hud_accent.SITES.values(),hud_accent.SIZE_SITE,calendar_layout.RESERVATION_SITE])
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
    for index in (0,4,5,6):assert translated[index]==original[index]
    assert translated[2][:len(original[2])]==original[2]
    assert len(translated[2])==11*8
    for digit in range(10):
        before=struct.unpack_from('<8H',original[1],digit*16)
        after=struct.unpack_from('<8H',translated[1],digit*16)
        assert after[:2]+after[4:]==before[:2]+before[4:]
        assert translated[3][after[3]*32:after[3]*32+128]==original[3][before[3]*32:before[3]*32+128]
    assert len(translated[3])//32==180<=256
    for i in range(22):
        frame=struct.unpack_from('<8H',translated[1],i*16)
        assert (frame[3]+frame[2])*32<=len(translated[3])
        assert frame[0]+frame[1]<=11


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
    # Logical marks remain in the eight-row glyph; spring/summer overlays
    # raise them in-game. Body height and counters must survive that split.
    pixels=date_ui.tiny_pixels(vowel,8,16)
    mark_rows=(0,1) if vowel=='è' else ((0,1) if vowel!='ạ' else (8,))
    gap=1 if vowel=='è' else (2 if vowel!='ạ' else 7)
    if vowel not in ('è','â'):assert not any(pixels[gap])
    if vowel=='â':
        glyph=date_ui.hud_glyph(vowel)
        assert glyph.bearing_y==date_ui.hud_glyph('è').bearing_y==2
        assert len(glyph.bitmap)==5
        assert pixels[3][:2]==[0,0], 'Upper opening must not fill with shadow'
        assert pixels[5][1:3]==[0,0], 'Lower counter must remain open'
        assert glyph.advance==date_ui.hud_glyph('a').advance==5
    mark_x=[x for y in mark_rows for x,v in enumerate(pixels[y]) if v==1]
    body_x=[x for y in range(3,6) for x,v in enumerate(pixels[y]) if v==1]
    assert mark_x and body_x
    if vowel=='è':
        assert pixels[0][1]==pixels[1][2]==1
        assert pixels[0][2]==pixels[0][3]==0  # previous horizontal stroke is gone
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


def test_calendar_header_spacing_all_years_and_seasons(rom):
    label=date_ui.calendar_pixels(rom,'Năm',32)
    left,right=calendar_layout.visible_bounds(label)
    for season in date_ui.SEASONS:
        heading=date_ui.calendar_pixels(rom,'— Mùa '+season,64)
        start,end=calendar_layout.visible_bounds(heading)
        # The thin separator and both word boundaries survive shadowing.
        assert all(heading[y][start+x]==11 for y in (9,) for x in range(5))
        occupied=[any(row[x] for row in heading) for x in range(start,end+1)]
        gaps=''.join('1' if v else '0' for v in occupied).split('1')
        assert sum(len(gap)>=3 for gap in gaps)==2,season
        for year in range(1,201):
            a,b,c,_=calendar_layout.layout(year,season,label,heading)
            number_width=len(str(year))*calendar_layout.YEAR_ADVANCE-1
            assert b-(a+right+1)==calendar_layout.WORD_GAP
            assert c+start-(b+number_width)==calendar_layout.GROUP_GAP
            assert a+left>=0 and c+end<240
            assert abs((a+left)+(c+end)-239)<=1
