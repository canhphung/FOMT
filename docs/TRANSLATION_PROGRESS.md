# Tiến độ Việt hóa

**Hiện tại:** 706/9.283 bản ghi dịch nháp, 2 prompt title đồ họa, lịch/HUD tiếng Việt, 93 test đạt.
Đã Việt hóa các màn tạo game mới, intro, menu con START và lịch/HUD; mục cuối ghi phiên triển khai.
Các mục cũ bên dưới giữ số liệu theo từng phiên lịch sử.

## Phiên 2026-10-22 — nền tảng và bản thử đầu tiên

Đã chuyển repo từ README trống thành pipeline localization có kiểm tra ROM,
trích xuất lossless, bảng mã/font Việt, chèn con trỏ/container và tạo IPS.
**Chưa hoàn thành mục tiêu Việt hóa 100%.** Không có chuỗi nào được đánh dấu
`reviewed`; toàn bộ bản dịch hiện là nháp.

### Dữ liệu có nguồn gốc xác minh

| Nhóm | Trích xuất | Có bản dịch nháp | Chưa dịch |
| --- | ---: | ---: | ---: |
| Tên vật phẩm | 347 | 346 | 1 |
| Mô tả vật phẩm | 347 | 21 | 326 |
| Nhãn menu tạm dừng | 7 | 7 | 0 |
| Chuỗi SCR | 8.368 | 11 | 8.357 |
| **Tổng catalog đã hỗ trợ** | **9.069** | **385** | **8.684** |

Khoảng 4,25% số bản ghi trong catalog hiện có bản dịch nháp; đây không phải
phần trăm Việt hóa toàn bộ nội dung game. Một số tên riêng được giữ nguyên.
349 payload khác nội dung nguồn; 36 bản ghi giữ nguyên chữ hiển thị, chủ yếu tên
riêng/tên định danh như Album. Không tính các tên giữ nguyên là câu đã đổi tiếng.
Không đếm câu giả lập trong test là văn bản game.

`localization/en/catalog.json` đã được sinh đầy đủ trong workspace và có thể
tái tạo từ ROM đúng hash, nhưng không track Git. Các subset EN/VI và glossary
có trong repo. `pilot.json` có 48 ID; `items.json` thêm 337 ID, không trùng.

### Kiểm chứng v1 (lịch sử)

- ROM nguồn khớp SHA-1 decomp tham khảo; 190 file source được lập inventory.
- 9.069 bản ghi round trip đúng byte; không sửa script CODE/JUMP khi rebuild.
- 42 kiểm thử pytest qua, không skip trong phiên này vì đã cung cấp `FOMT_ROM`.
- Build lặp lại cùng input tạo cùng hash; áp dụng IPS dựng lại đúng ROM đích.
- ROM 16 MiB boot trong mGBA, tạo game mới, qua các cảnh mở đầu đến nhà ngày 2.
- Đã xem hội thoại Thomas tiếng Việt qua luồng game bình thường và ảnh cả
  7 nhãn menu: Nhật ký, Ba lô, Bản đồ vùng, Bản đồ trại, Thu nhập, Ghi chú, Hướng dẫn.
- 134 glyph Việt khác nhau, đều qua CPU/render mGBA, đúng pixel, advance 1,
  không đụng canary. Cả 134 code qua đường gom byte/vẽ chuỗi, gồm EB7F.
- 95 glyph ASCII cho kết quả byte giống ROM gốc. 7 nhãn menu và 15 tên nông sản
  lấy từ pointer ROM mới qua renderer chuỗi và kiểm tra buffer đích.
- Ghi save thật bằng menu Diary, xuất SRAM 32 KiB, nạp vào core mới, boot lại,
  game nhận save và load về nhà ngày 2. Payload SRAM sau boot/load giữ nguyên.
- Không có log mức error/fatal trong lượt mGBA cuối.

Chứng cứ hiện tại trong `docs/evidence/` đã cập nhật sang v2; hash/kích thước ở
`patches/manifest.json`. Báo cáo ghi chính xác hash target đã chạy test.
`make compare` của decomp gốc chưa chạy: không cần matching build/agbcc cho
pipeline patch trực tiếp này. Không thay đổi code gameplay để làm test qua.

### Vấn đề phát hiện và xử lý trong phiên

- Tài liệu phụ dùng địa chỉ MFOMT: đã đối chiếu lại địa chỉ bản FOMT USA.
- RIFF của game dùng total length và không padding giữa chunk: parser theo
  loader thật, không theo thư viện RIFF phổ thông.
- FF là expansion prefix, không phải ký tự CP932 PUA: codec giữ cặp byte.
- Routine giải glyph IWRAM chạy ARM, không phải Thumb: hook dùng đúng state.
- Glyph advance 8 px vẫn dùng staging 128 byte: canary dựa trên đo thực tế.
- Bộ font thử đầu có O/o trùng bitmap: sửa mẫu O hoa, thêm kiểm thử đủ 134
  bitmap khác nhau để không lặp lại lỗi này.
- Một câu có tên người chơi vượt ngân sách khi dự phòng biến: đã viết lại
  câu tiếng Việt, không bỏ token hoặc nới validator để che lỗi.
- Savestate của emulator không chứa SRAM như bài test cần: kiểm thử save/load
  cuối dùng boot khởi tạo đầy đủ và SRAM riêng, không dựa vào EWRAM savestate.

### Phần chưa giải quyết

1. Phân loại speaker/call-site cho 8.357 chuỗi SCR chưa dịch: hội thoại NPC,
   sự kiện, TV, sách, hướng dẫn và lựa chọn đang lẫn trong cùng loại container.
   Không dịch những chuỗi chưa rõ chức năng.
2. 326 mô tả vật phẩm; một nhãn food `Flower` cần xác minh trước khi dịch.
3. UI static ngoài menu tạm dừng: Diary/options, shop, tên NPC, hướng dẫn,
   name-entry, đồ họa chữ title/lịch/đồng hồ chưa có adapter đầy đủ.
4. Duyệt xưng hô/thuật ngữ: hiện Popuri dùng mình/bạn, Thomas dùng bác/cháu ở
   đoạn đã xác minh. Chưa áp một bộ xưng hô suy đoán cho mọi nhân vật.
5. Lời chào Popuri đã rebuild/kiểm tra token, chưa gặp Popuri bằng luồng chơi
   tự nhiên trong lượt replay này. Không xem đó là bằng chứng encounter đã qua.
6. Chưa kiểm tra mọi cửa sổ vật phẩm, mọi byte-buffer copy, số dòng, cảnh/sự kiện,
   mùa/lễ hội/hôn nhân, hàng trăm giờ gameplay hoặc save cũ của người chơi.
7. Chưa kiểm tra flashcart/GBA thật, thẩm mỹ font trên LCD, nhập tên có dấu.

### Bước tiếp theo cho phiên sau

- Tiếp tục từ catalog đúng SHA-1, không quét/patch ASCII hàng loạt.
- Truy vết caller của GetString/VM text functions để gắn context và speaker,
  ưu tiên NPC thường gặp, cửa hàng và hướng dẫn đầu game.
- Hoàn thiện mô tả vật phẩm và adapter Diary; dùng các ID đã có, giữ nguyên
  control stream hoặc nghiên cứu validator mới trước khi đổi cách chia trang.
- Thêm save/replay theo từng milestone để kiểm tra Popuri, hộp thoại dài,
  cửa hàng, thùng xuất hàng, chuyển cảnh và save/load dài hạn.
- Chỉ nâng trạng thái sang `reviewed` sau khi duyệt ngôn ngữ và ảnh đúng context;
  cập nhật bảng đếm, test và manifest sau mỗi phiên.


## Phiên 2026-10-22 — sửa baseline/bearing font v2

Người dùng phản hồi chữ có dấu không đều và gửi ZIP font OTF tham khảo. Đã đo
bitmap thực tế và xác nhận lỗi v1: chữ thường lệch xuống 1px, chữ hoa bị co từ
10px còn 7px, O hoa rộng/lệch ngang, d/y bị sửa outline và ị mất chấm trên.
Độ rộng advance của engine vẫn luôn là 8px; kiểm thử v1 chưa kiểm tra hình học
thân chữ nên không phát hiện được lỗi này.

Đã thay bằng mask 8×16 dùng nguyên thân/bearing ROM gốc. ASCII và Việt dùng cùng
baseline hàng 13, không trim/scale/căn giữa riêng từng glyph, giữ advance 8px.
Dấu được thêm ở hàng trống; d giữ ascender, y giữ descender, ị giữ chấm trên.
Cache 4bpp sinh trước ở ROM gồm 229 glyph × 128 byte; dispatcher copy vào đúng
staging buffer cũ, không tăng VRAM hoặc sửa kích thước cửa sổ/bytecode gameplay.
Font OTF có 197 ký tự, chỉ 32/134 chữ Việt, được dùng làm tham chiếu; không đóng
gói OTF và không dùng metric 6px của OTF để đổi advance GBA 8px.

Kiểm thử hiện tại: **47 pytest đạt, không skip**, gồm hồi quy baseline/bearing,
outline hoa/thường, dấu trên/dưới i, ascender Đ/đ và cache 4bpp. mGBA xác minh
95 ASCII theo phép dịch đồng nhất 2px từ raster ROM gốc, 134 glyph/chuỗi Việt,
10 glyph fallback legacy/SJIS, 7 menu, 15 tên nông sản và 9 chuỗi ASCII/trộn dấu.
Lượt replay qua mở đầu, chọn menu, ghi Diary, boot core mới và load lại SRAM
vẫn đạt, không log error/fatal. 385 ID dịch không đổi; codec EB40–EBC5 không đổi.
Đã chạy lại cùng bộ probe trên mGBA **0.10.5** như người dùng đang dùng và 0.11-dev.
Adapter được sửa để đọc define CMake thực tế của từng version, tránh lệch ABI
ở hàm xuất SRAM khi tên macro debugger khác nhau; không thay code save của game.

`docs/evidence/font-spacing-comparison.png` là so sánh output renderer v1/v2
trên chuỗi chẩn đoán; ảnh Thomas/menu/save cũng được chụp lại từ ROM v2.
`font-metrics.json` lưu phép đo và metadata OTF, manifest trỏ đúng hash ROM/bản vá
mới. Bản vá mới phải áp lên ROM USA gốc, không chồng lên ROM đã Việt hóa v1.
Đã thử thêm SRAM của release v1 trên ROM v2: cold boot/load về nhà ngày 2,
byte SRAM không đổi. Khi nâng bản, dùng save trong game và boot lại; savestate
v1 giữ các pointer của layout ROM cũ nên không được xem là tương thích.

Giới hạn còn lại: ô chữ vẫn cố định 8px (chưa có kerning/VWF); chưa chơi thử
mọi UI và phần cứng GBA thật. Native glyph ngoài ASCII/Việt, lịch, đồng hồ và
đồ họa title vẫn theo hệ gốc. Các hạng mục dịch chưa giải quyết ở trên vẫn giữ
nguyên, không tăng số chuỗi dịch để tính việc sửa font.

## Phiên 2026-10-22 — Việt hóa prompt title “Start”

Đã xác minh `Start` là sprite đồ họa trong asset Popuri ở ROM `0x747A74`,
được constructor title tham chiếu qua literal `0xCB4`. Giải nén và đối chiếu
448 byte/14 tile tại offset `0x3D80` với VRAM thực tế; không tìm địa chỉ bằng
suy đoán hoặc thay ASCII hàng loạt.

Thêm adapter `tools/title_graphics.py`, mask `localization/vi/title_start.json`
và tích hợp build mặc định. Prompt hiện là **Bắt đầu**, đủ dấu tiếng Việt,
khung 56×16, dùng palette/viền/bóng gốc. Asset giải nén giữ cùng kích thước;
chỉ thay tile prompt, đóng gói literal mode 040 (format byte 0x04), append vào
ROM mở rộng và sửa literal đã xác minh. Chuyển động title và thao tác nút Start
giữ nguyên.

Kiểm thử: **55 pytest đạt, không skip**; gồm source/pointer mismatch,
truncation, Popuri word boundary, round trip, bố trí ba segment tile và xác
nhận chỉ 448 byte trong asset thay đổi. Bộ smoke mGBA kiểm tra VRAM đúng
artwork, OAM khớp gốc qua 180 frame, prompt dao động y=112..114 và frame đầu
không thay pixel ngoài vùng prompt. Replay tiếp tục qua tạo game mới, thoại,
menu, save Diary và load SRAM sau cold boot. Ảnh `docs/evidence/title-start.png`
là framebuffer thật, không vẽ chồng bản dịch lên screenshot.

Số bản ghi văn bản dịch vẫn **385/9.069**; thêm **1 asset đồ họa**. Đây vẫn là
bản thử. Các nhóm title khác, lịch/đồng hồ, Diary/options và các hạng mục chưa
dịch nêu trên còn nguyên; chưa kiểm tra GBA thật hoặc toàn bộ gameplay.

## Phiên 2026-10-22 — sửa độ rõ chữ “Bắt đầu” ở title

Người dùng phản hồi prompt khó đọc. Artwork trước có thân hoa 7px/thường 5px,
nét xanh mảnh kèm viền trắng + viền đen hai lớp. Các lớp viền dính vào dấu và
thân chữ, giảm độ rõ trên nền nhân vật. Đã thay riêng artwork này bằng revision
`native-bold-white-v2`: lấy outline ROM gốc cùng dấu của font Việt v2, làm đậm
ngang 1px, tô trắng đặc với viền đen 1px và bóng tối. Thân hoa trở lại 10px,
thân thường 7px, baseline hàng 13; tách 3px giữa chữ, 5px giữa hai từ.

Hàm `native_title_mask(rom)` tái tạo mask đã lưu trong JSON. Không đổi font hội
thoại, codec, kích thước 56×16, số OBJ/tile hoặc handler Start. Chỉ 448 byte tile
trong asset giải nén thay đổi; cùng literal đã xác minh trỏ tới asset mới.

Đã xem framebuffer cold boot và so sánh trước/sau ở kích thước nguyên pixel.
Bộ 55 pytest và smoke trên mGBA 0.10.5/0.11-dev kiểm tra lại artwork trong VRAM,
OAM/chuyển động title, Start vào tạo nhân vật, hội thoại, menu và save/load.
Bản vá/manifest và evidence được cập nhật; số chuỗi dịch vẫn 385 + 1 asset.
Giới hạn: chưa thử GBA thật; phần nội dung chưa dịch không thay đổi.

## Phiên 2026-10-22 — làm mảnh title theo ảnh tham khảo

Người dùng muốn chữ “Bắt đầu” thanh hơn và gửi mẫu chữ pixel tối trên nền trắng.
Đã đổi riêng title sang `native-thin-ink-v3`: bỏ giãn nét ngang, giữ nguyên nét
1px của thân chữ ROM/dấu Việt. Nét tối với halo trắng 1px, bỏ bóng đổ; giữ dáng
vuông, thân hoa 10px/thường 7px, baseline hàng 13 và khoảng chữ/từ 3px/5px.
Đây là thiết kế theo hình tham khảo, không khẳng định nhận diện được tên font
trong ảnh hoặc sao chép chính xác từng pixel của font đó.

Đã xem framebuffer cold boot, ảnh so sánh bản dày/bản mảnh và mẫu artwork trên
nền trắng. Bộ 55 pytest cùng smoke mGBA 0.10.5/0.11-dev kiểm tra tile/VRAM,
chuyển động title, Start vào game mới, menu, hội thoại và lưu/nạp SRAM.
Kiểm tra byte chứng minh ngoài asset title mở rộng không thay đổi gì so với
release trước; font hội thoại và gameplay không đổi. Cập nhật IPS/manifest,
ảnh evidence và báo cáo; vẫn 385 chuỗi dịch + 1 asset, chưa thử GBA thật.

## Phiên 2026-10-22 — đổi cặp màu title sang xanh ngọc/trắng

Người dùng duyệt nét mảnh và yêu cầu dùng cặp màu trong ảnh Start gốc. Đã đổi
nét tối sang xanh ngọc bằng OBJ palette bank 2 index 3 (`0x3B60`, #00DE73),
giữ halo trắng index 13 (`0x7FFF`). Revision `native-thin-mint-v4` giữ nguyên
mask, dấu, khoảng cách và halo v3; không giãn nét hay thêm bóng/viền mới.
Không sửa palette dùng chung hoặc font hội thoại.

Kiểm tra byte xác nhận tile chỉ đổi nibble màu E thành 3; nibble 0/D giữ nguyên,
và toàn bộ byte ngoài asset title mở rộng không đổi. Bộ 55 pytest và smoke
mGBA 0.10.5/0.11-dev kiểm tra lại title, Start, hội thoại/menu và save/load.
Cập nhật IPS, manifest và ảnh framebuffer/mẫu màu/so sánh. Vẫn là bản thử,
385 chuỗi dịch + 1 asset; chưa kiểm tra phần cứng GBA thật.

## Phiên 2026-10-22 — Continue → Tiếp tục và viền đen đầy đủ

Đã xác minh Continue bằng đối chiếu asset giải nén `0x3F40..0x41BF` với OBJ
VRAM 896..915 khi có save. Thêm `localization/vi/title_continue.json`, bản dịch
**Tiếp tục**; đồng bộ hai prompt với viền đen ngoài, trắng trong, nét xanh ngọc.
Giữ nét mảnh/font đã duyệt. Để dấu ế, descender p và dấu nặng ụ không cắt viền,
canvas tăng từ 16 lên 32px cao, mask xuống 2px và OAM lên 2px; nét vẫn ở vị trí
màn hình cũ. Số OBJ không đổi, cần thêm 34 tile trong allocation title đã xác
minh; không chồng copyright hoặc nhân vật. Asset 20.556 byte nằm gọn buffer
27.136 byte. Giữ nguyên logo, copyright, mũi tên, palette và lệnh animation.

**57 pytest đạt, không skip**. Smoke mGBA 0.10.5/0.11-dev so đúng VRAM và OAM
qua 180 frame cả khi không save/khi có save; giữ mũi tên; Start vào game mới,
Continue mở load menu và nạp SRAM thành công sau cold boot; không log error.
Test mới kiểm tra hai vòng màu, stride segment, RAM/VRAM và dữ liệu bảo toàn.
Ảnh `title-continue.png` chụp framebuffer từ ROM build thực tế.

Số bản ghi dịch vẫn 385/9.069; nay có **2 prompt đồ họa** trong cùng 1 asset.
Nội dung gameplay/font hội thoại không đổi; chưa thử GBA thật hoặc mọi save
người chơi. Diary/options và các nhóm nội dung chưa dịch vẫn còn tiếng Anh.

## Phiên 2026-10-22 — căn con trỏ cạnh “Tiếp tục”

Con trỏ cũ bám mép khung 80px trong khi chữ Việt được căn giữa và có inset
13px; vì vậy cách “Tiếp tục” quá xa. Đã thêm hook tại đúng call-site vẽ bàn
tay title `0x277C`, kiểm tra 8 byte nguồn trước khi patch. Hook lấy inset từ
artwork: Continue +13px, Start +2px cả có/không save, không đổi Y. Bàn tay còn
nhịp ±1px như ROM gốc. Không sửa cursor API dùng chung hoặc logic chọn menu.

Font, viền, màu, vị trí chữ và toàn bộ asset đồ họa giữ nguyên byte. Chỉ đổi
8 byte call-site cursor và thêm hook Thumb vào vùng mở rộng. Test kiểm tra
inset, bytes nguồn và build whitelist; smoke kiểm tra đầu ngón theo viền chữ,
bitmap tay không đổi, chuyển trái/phải, tạo game khi có save và nạp SRAM.
59 pytest đạt; mGBA 0.10.5/0.11-dev đều đạt. Cập nhật IPS/manifest và ảnh
`title-cursor-start.png`, `title-cursor-continue.png`, so sánh trước/sau.
Vẫn 385 chuỗi + 2 prompt đồ họa; chưa thử GBA thật hoặc mọi save người chơi.

## Phiên 2026-10-22 — Việt hóa luồng tạo game mới

Thêm adapter có nguồn xác minh cho 24 ID: đặt tên nhân vật/nông trại/chó,
Xong, xác nhận tên, sinh nhật, Xuân/Hạ/Thu/Đông và xác nhận tạo game. Catalog
hiện **9.093** mục, có **409** bản dịch nháp (khoảng 4,50% catalog đã hỗ trợ),
cộng hai prompt title đồ họa. Các mục lịch sử phía trên giữ nguyên số liệu cũ.

19 C-string được chuyển con trỏ sang vùng mở rộng; 4 hàng mùa giữ cấu trúc
`char[4][7]`; tiêu đề Birthday được trích xuất đúng dạng glyph u16, không coi
byte u16 là ASCII. Cache sinh nhật vẫn 43 ô 8×16, không tăng VRAM hoặc OBJ.
Tài liệu nguồn/địa chỉ và quyết định bố cục: [NEW_GAME_UI.md](NEW_GAME_UI.md).

Hai lỗi được phát hiện khi chạy mGBA và đã xử lý:

- Nhãn đầu tổng kết thay đổi làm tile nền cũ chứa nét chữ: chuyển fill sang
  cột trống được dành riêng, thêm kiểm tra để bản dịch sau không ghi vào cột này.
- Popup gốc dùng giới hạn `strlen` 28 byte cho câu hỏi: câu Việt vừa số ô vẫn
  có thể bị ẩn. Bổ sung giới hạn byte có nguồn từ hàm thật, dùng “Bắt đầu nhé?”.

**Kiểm chứng:** 67 pytest đạt, không skip; build lặp lại và IPS apply tái tạo
đúng hash ROM đích. mGBA 0.10.5 và 0.11-dev đều qua 8 ca 4 mùa × ngày 1/30,
đối chiếu tên/ngày sinh giữa ROM gốc và ROM Việt, xóa ký tự, tên dài 12 ký tự,
quay lại sửa tên/ngày sinh/tổng kết. Smoke toàn pipeline trên cả hai mGBA vẫn
qua boot/title/font/intro/menu/Diary save và load SRAM sau cold boot, không
log error/fatal. Đã xem ảnh framebuffer thật, gồm nhãn/câu hỏi/nút tiếng Việt
và nền tổng kết sạch; xem [ảnh tổng hợp](evidence/new-game-setup.png).

Cập nhật glossary, EN/VI subset, IPS/manifest và báo cáo evidence. Giới hạn còn
lại: bàn phím chưa nhập tên Việt có dấu; phần lớn hội thoại/menu khác còn tiếng
Anh; chưa thử GBA thật hoặc toàn bộ save/cảnh. Các bước tiếp theo là adapter
Diary/options/shop, phân loại hội thoại và mô tả vật phẩm còn thiếu.

## Phiên 2026-10-22 — intro mở đầu và hướng dẫn đầu ngày

Tách `intro.json` EN/VI gồm **145 ID**: 28 mục native của hồi tưởng thời thơ ấu,
10 câu Thomas nhận trại (chuyển từ pilot), 22 mục buổi sáng Thomas/Zack và
85 mục hướng dẫn tùy chọn trồng trọt/nuôi gà/bò/cừu. Thêm 135 bản dịch so với
phiên trước; hiện **706/9.283** mục catalog có bản dịch nháp, khoảng **5,96%**.
Pilot nay còn 38 ID; bốn subset mặc định không trùng ID. Hai prompt title
đồ họa giữ nguyên. Chưa Việt hóa toàn bộ game.

Đã xác minh 28 C-string và literal slot trong scene native `0x0805F5F4`,
phân loại 117 ID SCR có context intro/hướng dẫn. Giữ nguyên CODE/JUMP, tất cả
placeholder/control code và các symbol ???/RAW:8149. Glossary bổ sung xưng hô
bố/mẹ–con, ông–cháu, cô bé tớ–cậu, Zack tôi–cậu và thuật ngữ hướng dẫn.

Các vấn đề đã xử lý:

- Nhãn người nói chia nhóm 4 byte làm hỏng code Việt: thêm cache 12 ô cho năm
  nhãn intro, giữ ba OBJ và native fallback cho tên khác. Không tăng VRAM.
- Menu bốn mục chỉ nhận 12 byte/mục: “Mẹo hữu ích” bị ẩn; đổi “Mẹo hay” và
  kiểm tra budget byte dựa trên hàm thật, không bỏ qua validator.
- Replay cũ nhấn A cố định có thể mở TV sau intro và chặn Start/Diary: bài
  smoke nay dừng ở WAIT của câu chuyển ngày rồi mới mở menu, không đổi game.

**Kiểm chứng:** 72 pytest đạt, không skip. mGBA 0.10.5 và 0.11-dev đều đi qua
129/129 ID hội thoại bằng input game, 199 ảnh chờ nút, đủ năm nhãn người nói,
menu Có/Không/bốn chủ đề/chọn vật nuôi. Người chơi dùng tên dài 12 ký tự; đã
chạy cả bốn demo. 460 dòng qua renderer CPU với canary trong probe cô lập;
bốn ca native-name fallback khớp control ROM. Smoke toàn pipeline và tám ca
sinh nhật vẫn qua trên cả hai core, gồm Diary save và cold-boot load SRAM,
không log error/fatal. Build lặp lại và IPS apply phải trùng hash release.

Xem [nguồn và phương pháp](INTRO_LOCALIZATION.md),
[ảnh intro](evidence/intro-opening.png), `evidence/validation.json` và manifest.
Đã xem các cảnh chính và menu; chưa duyệt thủ công từng ảnh, chưa thử GBA thật.
Những phần còn lại: Diary/options/shop, hội thoại NPC/sự kiện/TV/sách, các mô
tả vật phẩm chưa dịch và nhập tên Việt có dấu. Toàn bộ bản dịch vẫn là nháp.


## Phiên 2026-10-22 — menu START và các màn con

Thêm 162 bản ghi nháp có nguồn xác minh, tổng 706/9.283 mục trong catalog.
Dịch Nhật ký/lưu/tải/tùy chọn, Ba lô, mô tả bản đồ và lịch mở cửa, tiêu đề bảng
thống kê/Ghi chú, hướng dẫn và sách mẹo. Không thay gameplay hoặc dữ liệu save.

Sửa hai buffer tiêu đề Ba lô cắt chuỗi theo byte; giữ char[12], 8 ô và trường
sức chứa túi gốc. Bổ sung cache glyph cho tiêu đề Mẹo điều khiển vốn vẽ từng
byte, dùng lại upload OBJ gốc. Pad nhãn bảng theo vùng tile để bỏ nét sót.

79 pytest đạt. mGBA 0.10.5 và 0.11-dev: 197 con trỏ đúng, 239 dòng qua renderer
có canh bộ nhớ, kiểm tra hai buffer Ba lô và cache tiêu đề sách trong VRAM;
replay các menu và kiểm thử tạo game, font/title, lưu SRAM/cold boot tải lại.
Xem [START_MENU.md](START_MENU.md), ảnh và báo cáo có hash ROM đích.

Chưa dịch chữ đồ họa SP/Mon/AM và đơn vị ngày D. Chưa có save chứa đầy đủ cá/
vật nuôi để replay mọi danh sách, chưa duyệt mọi hotspot bản đồ hoặc chơi xuyên
mùa/máy thật. Không đánh dấu reviewed; không tuyên bố Việt hóa 100% game.


## Phiên 2026-10-23 — lịch và khung ngày giờ

Đã triển khai phần đồ họa đã thống nhất: Năm 1 — Mùa Xuân; CN/T2…T7;
Xuân 2 · T2; HH:MM 24 tiếng. Dữ liệu 706/9.283 bản ghi không đổi vì các nhãn
này nằm trong tile đồ họa, không phải chuỗi ASCII mới trích xuất. Profile mới
`localization/vi/date_ui.json` ghi 12 nhãn lịch và cách hiển thị HUD.

Xác minh resource 22 frame ở 0x74F34C, bảng tile HUD 0x75A440 và sáu hàm cập
nhật. Thay 12 frame chữ, giữ nguyên chữ số/palette/biểu tượng; giảm 134 xuống
124 tile. HUD dùng lại hai OBJ/vùng đệm 64x16 pixel và giữ nháy dấu hai chấm.
Không sửa bộ đếm thời gian, bước 10 phút, cách lưu hoặc hàm tính ngày/thứ.

92 pytest đạt. Trên mGBA 0.10.5 và 0.11-dev: 2.580 trường hợp packed date/time
có canh bộ nhớ, 300 setter riêng, bốn fixture HUD so byte với VRAM, mở/đóng lịch
bình thường và 56 fixture lịch. Phần grid/biểu tượng/pixel thân lịch khớp ROM
gốc. Lưu Diary và cold boot tải lại đạt; smoke START chạy lại đạt.

Xem [DATE_UI.md](DATE_UI.md), ảnh và báo cáo có hash đích. Fixture năm/mùa là
kiểm tra trạng thái UI, không phải chơi xuyên mùa hoặc 200 năm. Popup mô tả
lễ hội và các đơn vị/ngày tiếng Anh ngoài hai giao diện này còn chưa dịch.
Chưa kiểm tra trên GBA thật. Các bản dịch vẫn ở trạng thái nháp.


## 2026-10-23 — Sửa khoảng cách dòng ngày trên HUD

Nguyên nhân: bố cục cũ dành ba cột tile cố định cho mùa, hai cho số ngày,
ba cho thứ; ngày 1–9 vẫn bỏ trống ô hàng chục. Số ngày dùng font lớn hơn
mùa/thứ, khiến khoảng cách và cỡ chữ không đồng đều.

Đổi sang `vietnamese-date-24h-spacing-v2`: số ngày dùng cùng font nhỏ với
mùa/thứ. Căn tên mùa theo mép mực bên phải, ghép ngày/dấu chấm/thứ thành
một suffix để ngày một chữ số không có ô trống. Các khoảng cách giữa từ
là ba pixel trong suốt, kể cả bóng. Cache ROM tăng từ 9.184 lên 40.192 byte;
không tăng RAM, OBJ, VRAM hay số byte chép mỗi lần cập nhật ngày.

93 pytest đạt. mGBA 0.10.5 và 0.11-dev đều qua 2.580 trường hợp HUD có canh
bộ nhớ, 300 setter, chín fixture HUD kiểm chứng OBJ VRAM (bốn mùa, ngày 2,
9, 10, 30), 56 fixture lịch giữ nguyên nội dung từ y=40 trở xuống. Smoke
font/title, START và lưu Diary/cold boot tải lại đều đạt. Bản vá IPS và
manifest được cập nhật; 706 bản ghi dịch nháp không đổi. Ảnh trước/sau:
[evidence/date-hud-spacing.png](evidence/date-hud-spacing.png); kết quả:
[evidence/date-ui-validation.json](evidence/date-ui-validation.json).

Đã duyệt ảnh HUD trước/sau, ngày một/hai chữ số và bốn mùa. Chưa kiểm trên
máy GBA thật hoặc chơi xuyên mùa; các giới hạn thử nghiệm trước vẫn áp dụng.
