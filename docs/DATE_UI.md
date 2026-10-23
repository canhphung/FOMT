# Lịch và khung ngày giờ tiếng Việt

Bản vá hiển thị lịch **Năm 1 — Mùa Xuân**, các mùa **Xuân/Hè/Thu/Đông**, hàng
thứ **CN, T2, T3, T4, T5, T6, T7**. HUD có hai dòng, ví dụ **Xuân 2 · T2** và
**06:50**. Giờ 24 tiếng thay AM/PM; giữ nhịp tăng 10 phút vốn có của game.

[Ảnh trước/sau và các mùa](evidence/date-ui.png) ·
[Kiểm chứng mGBA](evidence/date-ui-validation.json).

## Nguồn và cấu trúc

Áp dụng cho A4NE USA rev 0 có SHA-1 trong README; tham khảo StanHash/fomt b8471ae.
Không có giả định UTF-8 trong bộ vẽ GBA. Chữ Việt trong
`localization/vi/date_ui.json` được raster thành tile 4bpp ở lúc build.

| Thành phần | Offset file đã xác minh | Chứng cứ |
| --- | --- | --- |
| Tile chữ/số HUD | 0x75A440 | `asm/code_0803A8A4.s`; memcpy tile 8x8 từ bảng này |
| Tạo nội dung HUD | 0x3CD4C | Đọc năm/ngày/mùa/giờ/phút từ cấu trúc 4 byte |
| Cập nhật mùa/ngày | 0x3D080, 0x3D0F0 | Hàm setter gốc |
| Cập nhật giờ/phút/nháy dấu hai chấm | 0x3D240, 0x3D340, 0x3D2E8 | Hàm setter gốc; chỉ đổi cách vẽ |
| Resource chữ lịch | 0x74F34C, dài 0x1394 | Constructor 0xA220C, literal con trỏ 0xA2460 |
| Nhãn/năm/tháng trên lịch | Hook 0xA34B4, tiếp tục 0xA34EE | `asm/code_809E804.s`, trong hàm 0xA32A4 |
| Căn thứ trong tuần | 0xA34EE | Chỉ đổi tọa độ đầu hàng từ 6 sang 9 pixel |

Adapter `tools/date_ui.py` kiểm tra các prologue, literal, SHA-256 của tile số
và resource lịch. Inserter chỉ ghi vào những vị trí đã xác minh; cache mới,
resource mới và mã Thumb đều đặt sau ROM gốc ở vùng mở rộng. Build report ghi
địa chỉ và phiên bản trong `date_ui`.

## HUD — thân â đồng cỡ, khoảng cách H–è (v17)

V16 vẽ lại â trong Xuân bằng thân năm hàng
`0110/0001/0111/1001/0111`, thay thân bốn hàng gần giống o. Thân rộng 4 pixel,
từ y=2 đến y=6 như è; advance vẫn 5 pixel. Lòng chữ và lỗ mở được bảo vệ
khỏi bóng đổ. X, u, n, vị trí cả từ Xuân và khoảng cách ngày/thứ giữ nguyên.

Dấu mũ được nâng lên y=-1/0 bằng chính resource sprite dấu của v15. Có một
hàng trống y=1 trước thân y=2. Dấu căn giữa thân, gồm bốn điểm pixel và giữ
màu/palette native. Hè vẫn giữ đúng dấu huyền và thân e đã duyệt ở v15.
Thân e năm hàng 0110/1001/1111/1000/0111, V17 giảm bearing X từ 2 xuống 1 và advance từ 7 xuống 6 cho è.
Vì nhãn mùa căn phải, e/dấu huyền giữ nguyên tọa độ, chỉ H dịch phải một
pixel: khoảng trống giữa hai thân từ 3 còn 2 cột, giữa bóng H và e còn 1 cột.
Các glyph ngày/thứ cùng baseline y=6; clock giữ tile, advance 8 pixel và
vị trí x=8..47/y=8..15. Không có space thủ công, anti-aliasing hay font vector.

Hai OBJ/buffer HUD cũ và icon giữ nguyên. Spring/summer chia sẻ một tile
VRAM 32 byte, tối đa một OAM entry; không tăng thêm RAM/VRAM so với v15.
Mã mùa chọn tile dấu và đánh dấu cần upload lại, cả khi chuyển Xuân ↔ Hè.
Object vẫn 0x380 byte; resource được cấp phát/thu hồi bằng allocator native.
Cache cũ 40.192 byte, hai tile dấu thay phiên 64 byte trong ROM mở rộng.

[Chi tiết hook và tài nguyên](HUD_ACCENT_OVERLAY.md) ·
[Ảnh v16/v17](evidence/date-hud-he-spacing.png) ·
[Ảnh v15/v16](evidence/date-hud-a-balanced.png) ·
[Glyph a/â/è](evidence/hud-a-glyph.png).

Ảnh và quyết định v2–v16 giữ trong lịch sử tiến độ. Công thức thứ, packed
date, giờ 24 tiếng, nhịp tăng 10 phút và nháy hai chấm gốc không đổi. 23:59
chỉ là fixture bộ vẽ.

## Lịch tháng

Resource gốc có 22 frame: 10 chữ số, Year, 4 mùa và 7 thứ. Parser theo
0805E6CC đọc bảy section có stride 4/16/8/32/32/8/4 byte. Giữ nguyên frame số,
bitmap số, palette đỏ/xám/xanh, animation và tài nguyên lễ hội tách biệt.

Thay 12 frame nhãn bằng chữ có dấu từ font native đã dùng trong dự án. Hàng
thứ rút xuống một OBJ 16x16 mỗi nhãn; các mùa dùng 32x16 + 16x16, kể cả Thu.
Dữ liệu chữ giảm từ **134 xuống 124 tile**, không tăng cấu hình cấp phát gốc.
Hook tiêu đề đổi thứ tự thành Năm trước số năm, chừa đủ chỗ cho năm 1–200.
Màu Chủ nhật đỏ, Thứ Bảy xanh vẫn lấy từ palette gốc.

Không sửa hàm tính lịch, thứ tự ngày, dấu sinh nhật/lễ hội, lựa chọn bằng tay
trỏ hoặc nội dung mô tả lễ hội. Các popup mô tả lễ hội chưa thuộc phần dịch này.

## Kiểm thử

```bash
# Build theo README. emulator_smoke.py tạo một SRAM bằng thao tác lưu trong game.
.venv/bin/python tools/date_ui_smoke.py build/fomt-vi-demo.gba \
  --base-rom "$FOMT_ROM" \
  --sram build/date-full-0.10.5/save-test.sram \
  --library build/mgba_bridge-0.10.5.so \
  --output-dir build/date-final-0.10.5
```

104 pytest đạt; có kiểm tra khoảng trống bằng pixel cho toàn bộ 30 ngày × bảy thứ
và mép phải của bốn tên mùa. Kiểm tra baseline mọi chữ/số; advance cố định,
dấu huyền chéo ở giữa, sprite nâng dấu và kiểm tra tên Hè/tọa độ clock x=8.
Buffer mùa vẫn tám hàng; chỉ sprite dấu mở thêm hàng phía trên. Kiểm tra e/è có lòng
chữ và lỗ mở trong suốt, nét giữa không mất và metrics không đổi. Chạy cùng kiểm tra trên mGBA 0.10.5 và 0.11-dev:

- 2.580 trường hợp packed date/time qua CPU thật, có canh bộ nhớ; bao phủ mọi
  ngày 1–30, bốn mùa, bảy chu kỳ thứ và toàn bộ 24x60 giá trị giờ/phút.
- 300 lần gọi các setter riêng, giữ nguyên các thành phần lân cận và metadata.
- Chín fixture HUD qua đường upload thật, so byte buffer với OBJ VRAM; có ảnh
  06:50, 00:00, 12:00, 23:59, đủ bốn tên mùa với ngày một/hai chữ số và
  cặp ngày 9/10 để kiểm tra thay đổi độ dài. Vùng icon thời tiết x=196..239,
  y=140..159 khớp từng pixel ROM gốc trong cả chín fixture. So ảnh v16/v17:
  hai fixture Hè chỉ đổi pixel quanh H; cả e/dấu huyền giữ nguyên. Bảy
  fixture mùa khác không đổi pixel nào.
- Thêm 64 vòng cấp phát/thu hồi và ba trường hợp OAM 0/127/128 với guard;
  kiểm tra tile/palette/mosaic của sprite dấu qua native upload.
- Mở lịch tự nhiên bằng A tại lịch treo tường trong nhà. 56 fixture giao diện:
  năm 1/7/8/10/99/100/200 × bốn mùa × ngày chọn 1/30. Grid, event marker và
  toàn bộ pixel từ y=40 xuống dưới khớp ROM gốc. Các fixture chỉ đổi trường
  xem của UI và chạy hàm bố cục native; không phải chơi qua 200 năm.
- Đóng lịch trở về nhà, SRAM giữ nguyên; smoke chung chạy tạo game, font/title,
  lưu Diary rồi cold boot tải lại. Smoke menu START cũng chạy lại.

Đã duyệt ảnh trực tiếp, có hash trong báo cáo. Không có lỗi emulator. Chưa
kiểm tra trên máy GBA thật hoặc chơi xuyên mùa; các báo cáo intro/START chi
tiết cũ vẫn giữ hash của những bản build trước.
