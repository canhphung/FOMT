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

## HUD — Hè và vị trí đồng hồ cũ (v8)

`vietnamese-date-24h-he-v7` đưa đồng hồ từ x=24 trở lại **x=8..47, y=8..15**
trong HUD, đúng vị trí trước v6. Đổi tên mùa trên HUD/lịch từ **Hạ → Hè**,
không còn dấu nặng ở sát dòng giờ. Bitmap mới của è có dấu huyền tại (1,0),
(2,1), hàng y=2 trong suốt và thân bốn hàng y=3–6. Dấu và bóng không dính nhau.

Giữ advance/bearing của v6: chữ hoa 6 pixel, chữ thường/số ngày 5 pixel,
dấu chấm giữa 2 pixel, khoảng cách thành phần 3 pixel. `draw_run()` bố trí
các run bằng advance, không thêm space vào chuỗi. Thân chữ dòng ngày cùng
baseline y=6; clock có baseline y=14 và advance 8 pixel theo tile gốc.
Mùa chỉ dùng vùng 24x8 ở dòng trên; glyph nào vượt vùng đó bị từ chối thay
vì cắt dấu hoặc tràn vào đồng hồ.

Giữ nguyên hai OBJ 32x16, tổng HUD 64x16, vị trí OBJ, palette, biểu tượng
thời tiết và số tile VRAM. Bitmap đồng hồ gốc không đổi; không anti-aliasing,
font vector hay nội suy. Mùa còn lại và suffix ngày/thứ giữ bitmap v6.
Chỉ đổi bearing/layout đã nêu và thêm glyph è; cả lịch tháng dùng nhãn Hè.

Buffer vẫn ở object+0x84 và +0x1A8, mỗi buffer 256 byte; cờ upload +0x18C và
+0x2B0. Cache giảm về **40.192 byte**: mùa 4×96, ngày/thứ 210×160,
giờ 24×96, phút 60×64, nháy 2×32. Setter mùa chỉ chép 96 byte dòng trên;
hour vào +0x124, minute +0x228, colon blink +0x164 như v5. Không ghi
metadata lân cận, ngày giờ gameplay hoặc dữ liệu save.

Bản `vietnamese-date-24h-open-e-v8` vẽ lại thân e/è 4x4: thêm khoảng rỗng
hai pixel ở hàng thứ hai, nét ngang ba pixel ở hàng thứ ba và lỗ mở bên phải.
`clear_pixels` trong metrics bảo vệ lòng chữ/lỗ mở khỏi bóng đổ. Dấu huyền,
advance 5 pixel, baseline y=6, nhãn Hè và vị trí giờ đều giữ nguyên.

[Ảnh vẽ lại e, trái v7 — phải v8](evidence/date-hud-e.png) ·
[Ảnh khôi phục đồng hồ ở v7](evidence/date-hud-he.png).
Ảnh v2–v6 được giữ làm lịch sử. Công thức thứ, packed date, giờ 24 tiếng,
nhịp tăng 10 phút và nháy dấu hai chấm giữ nguyên. 23:59 chỉ là fixture
bộ vẽ, không phải thay đổi nhịp gameplay.

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

100 pytest đạt; có kiểm tra khoảng trống bằng pixel cho toàn bộ 30 ngày × bảy thứ
và mép phải của bốn tên mùa. Kiểm tra baseline mọi chữ/số; advance cố định,
dấu huyền của è, khoảng trống cả bóng, từ chối cắt glyph; kiểm tra tên Hè
và tọa độ clock x=8, mọi mùa nằm gọn trong tám hàng. Kiểm tra e/è có lòng
chữ và lỗ mở trong suốt, nét giữa không mất và metrics không đổi. Chạy cùng kiểm tra trên mGBA 0.10.5 và 0.11-dev:

- 2.580 trường hợp packed date/time qua CPU thật, có canh bộ nhớ; bao phủ mọi
  ngày 1–30, bốn mùa, bảy chu kỳ thứ và toàn bộ 24x60 giá trị giờ/phút.
- 300 lần gọi các setter riêng, giữ nguyên các thành phần lân cận và metadata.
- Chín fixture HUD qua đường upload thật, so byte buffer với OBJ VRAM; có ảnh
  06:50, 00:00, 12:00, 23:59, đủ bốn tên mùa với ngày một/hai chữ số và
  cặp ngày 9/10 để kiểm tra thay đổi độ dài. Vùng icon thời tiết x=196..239,
  y=140..159 khớp từng pixel ROM gốc trong cả chín fixture.
- Mở lịch tự nhiên bằng A tại lịch treo tường trong nhà. 56 fixture giao diện:
  năm 1/7/8/10/99/100/200 × bốn mùa × ngày chọn 1/30. Grid, event marker và
  toàn bộ pixel từ y=40 xuống dưới khớp ROM gốc. Các fixture chỉ đổi trường
  xem của UI và chạy hàm bố cục native; không phải chơi qua 200 năm.
- Đóng lịch trở về nhà, SRAM giữ nguyên; smoke chung chạy tạo game, font/title,
  lưu Diary rồi cold boot tải lại. Smoke menu START cũng chạy lại.

Đã duyệt ảnh trực tiếp, có hash trong báo cáo. Không có lỗi emulator. Chưa
kiểm tra trên máy GBA thật hoặc chơi xuyên mùa; các báo cáo intro/START chi
tiết cũ vẫn giữ hash của những bản build trước.
