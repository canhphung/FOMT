# Font và bảng mã tiếng Việt

## Bản sửa hình học v2

Revision hiện tại: `native-outline-aligned-v2`. Bảng mã `FOMT-VI-EB-v1` không
đổi: 134 chữ Việt vẫn ở `EB40`–`EBC5`, ASCII vẫn là byte ASCII. Thay đổi nằm ở
bitmap và renderer, không phải bản dịch, pointer ID hoặc control stream.

Lỗi của bản thử trước: chữ thường có dấu bị đẩy xuống 1px; chữ hoa được vẽ lại
thành thân 7px trong khi chữ gốc cao 10px; O hoa dùng thân rộng 6px và lệch trái
so với O gốc 5px. d/đ và y bị sửa nét riêng, ị bị mất chấm trên. Những lỗi này
làm thân chữ nhảy cao/thấp và khoảng trống hai bên khác với chữ không dấu.
Kiểm tra “134 glyph khác nhau” không phát hiện được các lỗi hình học này.

V2 lấy nguyên outline 8×12 của ROM, không scale/trim/căn giữa từng chữ. ASCII
và thân chữ Việt cùng có offset y=4 trong mask 8×16, cùng baseline hàng 13
(tọa độ bắt đầu từ 0), cùng advance **8px**. Thân chữ hoa vẫn cao 10px, chữ
thường 7px, d giữ ascender và y giữ descender gốc. Khi thêm dấu, không dịch
thân chữ sang trái/phải hoặc co chữ hoa. Đ/đ chỉ bổ sung gạch ngang; dấu móc
có điểm nối vào nét gốc. ị giữ chấm trên của i và thêm chấm dưới.

Ô chữ của game vốn cố định 8px; i/l có nét hẹp hơn m/o nên khoảng trắng theo
mực chữ không giống nhau. Bản sửa giữ cơ chế đó, không tuyên bố có kerning hoặc
variable-width font. Sai khác giữa a và á, O và Ô, d và đ đã được xử lý từ outline
và baseline thay vì đổi advance riêng từng glyph rồi làm lệch cửa sổ.

## Font OTF người dùng cung cấp

Đã kiểm tra ZIP `harvest-moon-friends-of-mineral-town.otf.zip`:

- Font: *Harvest Moon - Friends of Mineral Town*, Mokura, FontStruct.
- [Nguồn](https://fontstruct.com/fontstructions/show/73236), metadata giấy phép
  [CC BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/).
- SHA-256 OTF: `6287c385d8723ea01c1708c03e67f42c3d32776f0392bd124a6e13d03a37f5f0`.
- Cmap có 197 ký tự, chỉ chứa **32/134** chữ Việt cần dùng; thiếu Ă, Đ, Ơ, Ư,
  nhóm dấu kép, dấu hỏi, dấu nặng và nhiều biến thể khác.
- unitsPerEm=2000; advance ASCII=750, tương đương 6px ở 16ppem. Vì vậy không
  thể lấy hmtx này làm advance cho renderer GBA đang dùng ô 8px.
- Các outline chữ/số plain ở raster 16ppem khớp nét ROM khi đặt đúng bearing.

OTF được dùng làm tham chiếu, không được nhúng hoặc đóng gói trong repo/bản vá.
Build không phụ thuộc fontTools hoặc font OTF bên ngoài. Nét gốc được lấy từ
ROM người dùng cung cấp; dấu Việt do công cụ ghép vào mask. Báo cáo phép đo có
trong `docs/evidence/font-metrics.json`.

## Địa chỉ đã xác minh trên đúng bản USA

| Thành phần gốc | GBA bus address | Nguồn |
| --- | --- | --- |
| Hàm chọn/vẽ glyph | `0x080D0D28` | `asm/code_809E804.s` |
| Sheet glyph hẹp 8×12, 1bpp | `0x084F90CC` | `asm/data/data_0813B288.s` |
| Lookup một byte, 256 số s16 | `0x084FA7A0` | cùng file |
| Sheet glyph rộng 16×12 | `0x084FA9A0` | cùng file |
| Lookup JIS | `0x08523290` | cùng file |
| Routine giải glyph hẹp gốc, ARM | `0x0300085C` | copy vào IWRAM lúc boot |
| Routine giải glyph rộng gốc, ARM | `0x03000714` | copy vào IWRAM lúc boot |
| Vẽ chuỗi vào tile buffer, Thumb | `0x0804E8F0` | `asm/code_0803EE94.s` |

Font gốc là 1bpp, MSB ở trái, 12 hàng. Hàm gốc sinh foreground index 1 và
shadow index 2: bóng lệch sang phải 1px, và phải-xuống 1px; foreground thắng
bóng. Staging buffer là **128 byte / bốn tile 16×16**, kể cả advance 8px.

## Cache và hook v2

Không thay routine IWRAM 12 hàng để đọc quá dữ liệu. Công cụ build mask 8×16
thành staging 4bpp hoàn chỉnh ở ROM, đúng tile order và shadow gốc. Cache gồm:

- 95 glyph ASCII + 134 glyph Việt = 229 entry.
- 128 byte/entry = **29.312 byte ROM**, so với 1.608 byte bitmap Việt của v1.
- Runtime chỉ copy 128 byte bằng 8 cặp LDMIA/STMIA; không tăng buffer RAM/VRAM,
  không tính lại dấu/shadow mỗi frame. Hook 80 byte, trong reservation 128 byte.

Thay đúng 8 byte đầu `0x080D0D28`, xác minh prologue `70 B5 04 1C 0A 1C 00 26`.
Printable ASCII và EB40–EBC5 dùng cache. Nếu buffer null, trả width=1 mà không
copy. Lead EB riêng lẻ vẫn đi đường gốc và trả 0, để wrapper gom byte tiếp theo.
Glyph khác phát lại prologue rồi nhảy Thumb đến `0x080D0D30` như trước.
10 probe legacy/SJIS xác nhận fallback không đổi. Chưa thống nhất font của các
ký tự legacy/Japanese chưa Việt hóa; chúng vẫn theo đường render gốc.

Không có BLX/Thumb-2; dispatcher/copy chạy trên ARM7TDMI. ASCII trong v2 giữ
nguyên nét, bearing và shadow, **dịch xuống đồng loạt 2px** so với output gốc.
Do đó kết quả render ASCII không còn byte-identical với v1; phép thử mới so
với raster ROM gốc sau đúng phép dịch 2px/cắt bóng ở mép ô. Không còn phép kiểm
tra cũ mang tên `ascii_glyphs_unchanged`.

## Bố cục và dữ liệu font

Mask có 16 hàng, chữ hoa bắt đầu tại hàng 4, chữ thường tại hàng 7, baseline
hàng 13; y xuống hàng 14, dấu nặng hàng 15. Phần foreground nằm trong ô 16px;
bóng ngoài hàng 15 bị cắt có chủ đích. Dấu mũ/breve/thanh dùng các hàng trống
trên thân chữ. Giữ ô cao 16px và advance 8px của renderer/cửa sổ hiện có.

`localization/font/encoding.json` là bản xuất mask 1bpp và metadata, không phải
font OTF hoặc bảng 4bpp trực tiếp. Sửa mẫu trong `tools/vietnamese_font.py`, build
lại cache và chạy test; không sửa JSON rồi coi đó là đầu vào build. Bảng mã
không đổi nên các bản dịch hiện có vẫn dùng được. ROM mới phải được tạo từ ROM
USA gốc đúng SHA-1, không áp IPS mới chồng lên ROM đã patch.
Phải boot lại ROM mới thay vì nạp savestate v1: cache lớn hơn làm thay đổi
địa chỉ allocation mới, trong khi savestate giữ pointer RAM của ROM trước.
Đã thử một save SRAM trong game của v1 (ngày 2) bằng cold boot trên v2 và load
thành công, giữ nguyên byte SRAM. Không cam kết mọi save/savestate đều tương thích.

## Kiểm thử và ảnh so sánh

- Test hình học so toàn bộ thân chữ Việt với outline/bearing/baseline ROM gốc;
  kiểm tra riêng i/ị và ascender Đ/đ, đủ 134 bitmap khác nhau.
- 95 ASCII qua CPU mGBA so raster với ROM gốc dịch đúng 2px.
- 134 glyph Việt được so pixel/canary; 134 code qua đường gom byte/vẽ chuỗi thật,
  kể cả EB7F, dấu nặng sát đáy và các chữ hoa có dấu kép.
- 7 menu, 15 tên nông sản, ASCII và các chuỗi trộn chữ/dấu qua renderer chuỗi.
- Chơi mới bằng nút thật đến hội thoại Thomas/nhà ngày 2; chọn đủ menu; ghi Diary
  và cold-boot load SRAM. Ảnh thực tế và báo cáo ở `docs/evidence`.
- `font-spacing-comparison.png` lấy output renderer mGBA v1/v2 trên các chuỗi
  chẩn đoán; đây không phải ảnh NPC encounter. `vietnamese-font.png` là atlas
  mask 8×16 phóng 3 lần, không phải ảnh game.

Có thể tái tạo phép đo và ảnh:

```bash
.venv/bin/python tools/font_metrics.py "$FOMT_ROM"
.venv/bin/python tools/font_atlas.py "$FOMT_ROM" --encoding-output localization/font/encoding.json
.venv/bin/python tools/font_preview.py /path/to/old-patched.gba build/fomt-vi-demo.gba
# Chỉ khi muốn kiểm tra lại OTF tham chiếu:
.venv/bin/python -m pip install fonttools==4.62.1
.venv/bin/python tools/font_metrics.py "$FOMT_ROM" --reference-font /path/to/font.zip
```

Đã chạy toàn bộ glyph/string/menu/intro/save-load probe trên cả mGBA 0.10.5
(tag `0.10.5`, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`) và bản 0.11-dev
đã dùng ở phiên trước. Adapter lấy đúng define từ CMake của từng bản để tránh
lệch ABI `USE_DEBUGGERS`/`ENABLE_DEBUGGERS`; không sửa SRAM game để làm test qua.

Chưa kiểm tra mọi UI/biến thể cửa sổ, phần cứng GBA thật hoặc nhập tên có dấu.
Font của lịch/đồng hồ/đồ họa title là hệ riêng. Không tuyên bố đã Việt hóa toàn bộ
font/toàn game hoặc đã thêm proportional spacing vào các hàm tile-aligned.

Hai prompt title **Bắt đầu** và **Tiếp tục** dùng artwork riêng, revision
`native-thin-double-outline-v5`. Giữ nét mảnh đã duyệt: thân hoa 10px/thường
7px, dấu Việt và descender nguyên vẹn. Từ ngoài vào: viền đen, viền trắng,
nét xanh ngọc (#00DE73); không giãn nét hoặc thay font hội thoại.

Canvas trong suốt cao 32px (Start rộng 56px, Continue 80px) để cả dấu trên,
dấu nặng ụ và hai lớp viền đều nằm gọn. Mask xuống 2px, OAM lên 2px nên vị
trí nét trên màn hình không đổi; nguyên số OBJ và chuyển động title.
Khoảng chữ 3px, khoảng từ 5px. Xem [TEXT_SYSTEM.md](TEXT_SYSTEM.md) để đối
chiếu RAM/VRAM và `title-start.png`, `title-continue.png` trong evidence.
