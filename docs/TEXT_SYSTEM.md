# Hệ thống văn bản FOMT USA

## Phạm vi và nguồn

Phân tích trên ROM do người dùng cung cấp, 8,388,608 byte, game code `A4NE`,
revision 0. SHA-1 bắt buộc:
`a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`.
SHA-256: `ca6cebe7211b6f2693af210709f76222204bf9f7621dec08b30ca268117460dd`.

Nguồn chính: [StanHash/fomt](https://github.com/StanHash/fomt), commit
`b8471ae065744869f64283473ed68372f82321c9`. Toàn bộ 190 file tracked được đọc
để lập `reference_inventory.json` với kích thước/hash; phân tích ngữ nghĩa tập
trung vào VM, dữ liệu vật phẩm, font và các hàm gọi render. Đây không phải tuyên
bố đã hiểu mọi hàm của game. Checkout tham khảo nằm ngoài repo sản phẩm.

Tài liệu phụ: [StanHash/FOMT-DOC](https://github.com/StanHash/FOMT-DOC).
Nhiều địa chỉ trong đó ghi **MFOMTU**, thuộc *More Friends of Mineral Town*.
Không được sao chép các địa chỉ đó sang bản FOMT. Địa chỉ trong tài liệu này đã
đối chiếu với source chính và ROM đúng hash. `rea` chưa cần dùng.

## Địa chỉ và byte order

GBA bus address = `0x08000000 + file_offset`. Word/pointer dùng little endian.
Ví dụ bus `0x080F89D4` tương ứng file offset `0x0F89D4`. Công cụ kiểm tra miền
pointer, không cắt bit để biến một pointer sai thành địa chỉ hợp lệ.

## Bảng vật phẩm

Chứng cứ: `tools/scripts/dump_item_tables.py`, `data/item/*.def`,
`src/item.cc` (`Tool/Food/Article::GetName/GetDesc`).

| Nhóm | File offset bảng | Số phần tử | Stride | Name pointer | Description pointer |
| --- | --- | ---: | ---: | ---: | ---: |
| tool | `0x0EAB0C` | 81 | 12 | +0 | +8 |
| food | `0x0EDCD8` | 171 | 16 | +0 | +12 |
| article | `0x0EFED4` | 95 | 12 | +0 | +8 |

Tên và mô tả là C-string kết thúc bằng byte `00`. Các trường icon, giá,
stamina, fatigue và thuộc tính vật phẩm không bị sửa. Bảng product định tuyến
sang food/article, không phải một bản sao độc lập của tất cả tên.

Tổng trích xuất nhóm này: 347 tên + 347 mô tả. Không sửa lỗi gốc ngoài phạm vi:
ví dụ hai nhãn len đều hiện `Wool (P)`; bản dịch giữ nhãn P theo văn bản nguồn.
Nhãn `Flower` của food 66 đã xác minh là bột mì bằng bảng tạp hóa và sách trong ROM; English nguồn được giữ nguyên. Xem [vật phẩm/UI](ITEM_LOCALIZATION.md), gồm 26 literal mới, ngân sách byte và bản sửa scanner NUL.

## Menu tạm dừng

7 pointer liên tiếp tại file `0x0F1A34`, theo thứ tự Diary, Rucksack, World Map,
Farm Map, Earnings, Memo, Tutorial. Trước khi xuất, extractor kiểm tra đúng cả
7 nhãn nguồn. Chứng cứ: `asm/code_0803A8A4.s`, literal `0x0803C0C4` trỏ
đến `gUnk_080F1A34`, truy cập `table[index]`.

Ngân sách dịch thử: 12 ô × 8 pixel. Cả 7 nhãn đã được chọn bằng nút Right trong
game và xem ảnh chụp. Các chữ trong màn hình Diary, hướng dẫn, tên NPC và logo
title chưa được tích hợp vào adapter static text; title có thành phần đồ họa.

## Script hội thoại/sự kiện

Chứng cứ chính: `src/script_engine.cc` và `include/script_engine.hh`:
`AScriptEngine::Load`, `GetString`, `ScriptEngine::LoadById`.

Bảng pointer tại file `0x0F89D4`, dài `0x14C4` byte = 1,329 phần tử. Phần tử 0
null; 1,328 phần tử còn lại trỏ đến container `RIFF`/`SCR `. Chúng chứa tổng
8,368 chuỗi. Chuỗi byte `RIFF` tại `0x03EF48` là literal trong code, không phải
container SCR — scanner chỉ tìm magic sẽ đếm sai.

```
container +00  "RIFF"
          +04  u32 total_container_bytes
          +08  "SCR "
          +0C  các chunk: tag[4], u32 payload_bytes, payload

CODE payload: u32 bytecode_bytes, bytecode[...]
JUMP payload: bảng nhảy VM (tùy script)
STR  payload: u32 count, u32 relative_offsets[count], string_pool
```

**Khác RIFF chuẩn**: trường length của game là tổng kích thước container, không
phải tổng trừ 8. Không thêm padding lẻ/chẵn giữa các chunk. Container tiếp theo
thường được căn 4 byte bên ngoài container. Offset của từng string tính từ đầu
`string_pool`, không phải đầu ROM/container/chunk. String kết thúc bằng `00`.
Giữ nguyên số lượng/thứ tự ID; VM gọi string theo index.

Importer giữ nguyên byte `CODE` và `JUMP`, tái tạo `STR ` và trường length,
đặt container mới ngoài ROM gốc rồi sửa đúng pointer trong bảng script. Nó kiểm
tra lại toàn bộ string và so sánh bytecode/bảng nhảy sau rebuild. Không patch
các word có giá trị giống pointer ở nơi chưa rõ chức năng.

## Bảng mã và control stream

Renderer tương thích ASCII/Shift-JIS với một số glyph một byte tùy chỉnh của
bản USA. Không phải Unicode/UTF-8. JSON dùng token để đảm bảo round trip:

| Byte | Token | Ý nghĩa xác minh |
| --- | --- | --- |
| `00` | không xuất như text | kết thúc C-string |
| `05` | `{WAIT}` | chờ nút tiến hội thoại |
| `0A` | `{LF}` | chuyển dòng, không tự đặt x=0 |
| `0C` | `{PAGE}` | xóa/chuyển trang hộp thoại |
| `0D` | `{CR}` | đặt x về đầu dòng |
| `FF xx` | `{VAR:XX}` | yêu cầu bộ mở rộng biến; giữ nguyên cả cặp |
| byte khác ngoài ASCII | `{RAW:...}` | giữ nguyên, chưa gán nghĩa tùy tiện |

`{VAR:21}` hiện tên người chơi trong đoạn Thomas, đã quan sát bằng tên A.
Chưa lập đầy đủ ý nghĩa mọi variable ID. `{RAW:8140}` thường là khoảng trắng
rộng theo CP932 nhưng vẫn giữ nguyên byte thay vì thay thành dấu cách ASCII.
Không diễn giải byte `FF` thành ký tự Private Use của Python CP932.

Đã kiểm tra round trip cho 9.121 bản ghi: 9.120 C-string qua codec lossless;
riêng tiêu đề Birthday là 8 mã glyph `u16le`, được kiểm tra theo đúng định dạng.
Importer yêu cầu token và thứ tự token giống hoàn toàn nguồn. Phần tử `RAW`
không được xóa/đổi để làm validator qua. Văn bản thường được chuẩn hóa NFC.

## Font, giới hạn và import

Xem [VIETNAMESE_FONT.md](VIETNAMESE_FONT.md). Hộp thoại có ba dòng hiển thị và
ngang 28 ô; source `func_0804EFAC` dùng phép kiểm tra x+width với `0x1B`,
cuộn dòng theo display manager. Công cụ đo chiều ngang, tách CR/LF đúng nghĩa,
và dự phòng 12 ô cho mỗi biến chưa biết chiều dài. Ngân sách tên vật phẩm 20 ô
là giới hạn dịch thử bảo thủ, **chưa chứng minh mọi cửa sổ đều có đủ 20 ô**.
Chưa có kiểm tra tự động đầy đủ chiều dọc, mọi expansion, buffer copy theo byte
hoặc mọi biến thể cửa sổ. Dấu/chữ dùng 2 byte nhưng rộng 1 ô.
Font v2 dùng mask 8×16, giữ outline/bearing gốc và căn ASCII/Việt cùng baseline;
cache 4bpp 229 glyph dùng đúng staging 128 byte của engine, không đổi advance 8px.

ROM đầu ra 16 MiB. Mọi allocation mới bắt đầu từ offset `0x800000`, căn 4 byte;
không tận dụng vùng FF bên trong ROM gốc bằng suy đoán. Chỉ sửa 8 byte prologue
renderer, các slot pointer và 8 byte call-site vẽ con trỏ title đã xác minh.
Header và SRAM routine giữ nguyên.
Mỗi build có audit report liệt kê các write, allocation, layout và hash.

## Đồ họa Start / Continue ở title

`Start` và `Continue` là sprite, không phải ASCII/SCR. Constructor
`func_08000914` trong StanHash/fomt (`b8471ae`, `asm/intro_scene.s`) gọi
`Unpack` qua literal ROM offset `0xCB4` → `0x08747A74`. Asset nguồn dài
`0x2F4C`, magic `0x70`, Popuri Huff8/LZSS2/no-delta (220), giải nén `0x4C0C`.
Đã đối chiếu trực tiếp với OBJ VRAM khi không có save và khi có SRAM hợp lệ:

| Prompt nguồn | Offset trong asset giải nén | Tile live gốc | Segment gốc |
| --- | --- | --- | --- |
| Start | `0x3D80..0x3F3F` | 864..877 | 32×16 + 16×16 + 8×16 |
| Continue | `0x3F40..0x41BF` | 896..915 | 32×16 + 32×16 + 16×16 |
| Mũi tên Continue | `0x41C0..0x41DF` | 916 | 8×8 |

`localization/vi/title_start.json` và `title_continue.json` lưu **Bắt đầu** /
**Tiếp tục**. `native_title_mask(rom,text,width)` tạo nét 1px từ thân ROM gốc
và dấu Việt, khoảng chữ 3px/từ 5px. Revision `native-thin-double-outline-v5`
có đủ hai vòng: đen ngoài (palette 14, `0x0000`), trắng trong (13, `0x7FFF`),
xanh ngọc ở nét (3, `0x3B60`, #00DE73). Dùng OBJ palette bank 2 sẵn có.

Hai lớp viền quanh dấu trên và dấu nặng ụ vượt chiều cao 16px. Adapter giữ
nguyên nét/độ cao chữ, mở canvas trong suốt lên 32px: Start 56×32, Continue
80×32. Mask dịch xuống 2px và ba OBJ chữ dịch lên 2px ở mọi frame, nên vị trí
nét trên màn hình không đổi. Số OBJ và độ rộng không đổi. Tile mới nằm trong
các allocation title đã xác minh: Start 864..891, Continue 896..935, mũi tên
936, copyright 960..1019; không chồng nhau và đều dưới 1024 tile OBJ.

Asset mới có 603 tile thay 569, dài 20.556 byte, nhỏ hơn buffer constructor
`this+0x10..this+0x6A10` (27.136 byte). Chỉ đổi descriptor của ba frame Start /
ba frame Continue, tile count/base của các frame bị dịch trong pool. Logo,
copyright, mũi tên, palette, bảng animation và lệnh animation giữ nguyên byte.
Không giả định vùng FF/VRAM trống. Công cụ kiểm tra hash nguồn, giới hạn RAM,
VRAM và round trip; đóng gói literal 040, append ROM mở rộng và sửa duy nhất
literal `0xCB4` ở ROM gốc. Gameplay/codec/font hội thoại không đổi.

Smoke so raster VRAM và đối chiếu OAM với đúng các thay đổi descriptor dự kiến
qua 180 frame, cả hai trạng thái save. Có kiểm tra mũi tên gốc, Start vào tạo
nhân vật, Continue vào load menu, load SRAM sau cold boot và ảnh thực tế.
OAM Y canvas là 110..112 thay 112..114; vị trí và chuyển động nét vẫn như cũ.
Không tuyên bố toàn bộ framebuffer đồng nhất từng frame vì blink nền có thể
khác pha. Hai artwork không cộng vào 544 bản ghi dịch/9.121 mục catalog.

### Căn con trỏ theo viền chữ Việt

Khung Continue rộng 80px, nhưng viền ngoài của “Tiếp tục” bắt đầu ở x=13 trong
khung; “Bắt đầu” có inset 2px trong khung 56px. Giữ con trỏ bám mép khung gốc
làm nó xa chữ Việt. `tools/title_cursor.py` tính inset từ pixel thực tế và
chỉ điều chỉnh X của bàn tay, giữ nguyên text/bitmap cursor/Y và nhịp ±1px.

Call-site riêng cho cursor tại ROM `0x277C` (`intro_scene.s`, draw this+6C40)
có 8 byte nguồn `1a20215e68460180`: đọc signed X và ghi tham số render lên
stack. Importer kiểm tra đúng bytes rồi trỏ tới hook Thumb ở ROM mở rộng.
Hook cộng 13px khi anchor=136 (Continue), 2px khi anchor=24/80 (Start có/không
save), giữ nguyên các giá trị khác và trở về `0x08002785`. Không sửa API cursor
dùng chung, handler chọn menu hoặc routine save/load.

Vị trí bàn tay trung tâm chu kỳ: Continue x=134 thay 121, Start có save x=11
thay 9, Start không save x=67 thay 65; Y=114. Bitmap tay có pixel tận cùng
x=15 nên đầu ngón bám mép viền chữ, với dao động gốc ±1px. Smoke kiểm tra
OAM/VRAM, đổi trái/phải, Start tạo game mới và Continue nạp SRAM.

## Phân loại còn thiếu

9.121 là số bản ghi trong **các cấu trúc đã hỗ trợ**, không phải khẳng định đã tìm
hết mọi chữ game có thể hiển thị. Script còn chứa TV, sách, sự kiện, menu chọn,
lời NPC và hướng dẫn; phần lớn chưa nối được đến speaker/call-site, nên giữ
`script_string_unclassified`. Chưa dịch tự động nhóm này. Tên NPC, UI static
ngoài luồng tạo game mới, đồ họa chữ và lịch/đồng hồ cần adapter riêng. Không có
địa chỉ hay hội thoại tự đặt nào được đưa vào catalog dưới tên nội dung gốc.

## Tạo game mới

Adapter [new_game_ui.py](../tools/new_game_ui.py) hỗ trợ 19 C-string có con trỏ,
4 hàng mùa cố định và một tiêu đề bằng bảng glyph. Xem [NEW_GAME_UI.md](NEW_GAME_UI.md)
về địa chỉ xác minh, giới hạn byte trước khi render, cache OBJ và ô nền tổng kết.

## Intro và hồi tưởng

[intro_text.py](../tools/intro_text.py) hỗ trợ 28 C-string có literal pointer
trong `func_0805F5F4`, gồm 23 lời thoại và 5 nhãn người nói. Trích xuất thêm
28 mục này; phân loại 117 mục SCR đã có thành intro/hướng dẫn có context xác minh.
Không quét ASCII rồi coi mọi kết quả là chuỗi có thể chèn.

Nhãn người nói gốc bị chia nhóm **4 byte**, không phải 4 ký tự. Hook tại
`0x50B50` chỉ xử lý các pointer nhãn intro đã chuyển vùng, copy cache đúng ba
buffer gốc; tên khác đi nguyên đường native. Chi tiết, giới hạn menu 12 byte
và kiểm chứng trong [INTRO_LOCALIZATION.md](INTRO_LOCALIZATION.md).

## Menu con START

Adapter `tools/start_menu.py` thêm 162 chuỗi native và dòng sách mẹo đã xác minh.
Xem [START_MENU.md](START_MENU.md) cho bảng con trỏ, ngân sách ô/byte, hai hook
tiêu đề Ba lô và cache tiêu đề sách. CLI build mặc định nạp `start_menu.json`.

## Lịch và khung ngày giờ

Đây là đồ họa tile, không bổ sung các nhãn này vào catalog ASCII/SCR.
`tools/date_ui.py` xác minh và dựng resource lịch, cache HUD cùng sáu setter
chỉ thay cách vẽ. Xem [DATE_UI.md](DATE_UI.md) cho cấu trúc và kiểm chứng.
