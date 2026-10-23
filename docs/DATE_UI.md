# Lịch và khung ngày giờ tiếng Việt

Bản vá hiển thị lịch **Năm 1 — Mùa Xuân**, các mùa **Xuân/Hạ/Thu/Đông**, hàng
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

## HUD — metrics v6

`vietnamese-date-24h-metrics-v6` giữ nguyên hai OBJ 32x16, tổng 64x16 pixel,
vị trí OBJ, palette và icon thời tiết. Không thêm OBJ, heap hay VRAM. Các glyph
đều là bitmap pixel nguyên; chỉ dùng màu trong palette gốc, không anti-aliasing,
không font vector hay nội suy. Giữ nguyên bitmap chữ số và dấu hai chấm của
đồng hồ. Bitmap chữ Việt đã duyệt được giữ khi có thể; sửa vị trí thân/dấu ạ
để đúng baseline, bỏ cách nâng riêng cả nhãn Hạ của v5.

`HUDGlyph` tách bitmap, advance, bearing Y, điểm dấu và hàng trống. Tất cả
chữ/số của dòng ngày có baseline **y=6**; bearing Y được tính từ baseline và
chiều cao bitmap. Dấu mũ ở y=0/1, y=2 trống, thân â/ô ở y=3–6. Thân ạ cũng
ở y=3–6, y=7 trống cả mực lẫn bóng, dấu nặng ở y=8. Không cắt glyph: build
báo lỗi nếu mực hoặc bóng ra ngoài canvas.

| Metrics / vùng (tọa độ trong HUD) | Giá trị |
| --- | --- |
| Advance chữ hoa ngày/thứ | 6 pixel |
| Advance chữ thường và số ngày | 5 pixel |
| Advance dấu chấm giữa | 2 pixel |
| Khoảng cách giữa thành phần | 3 pixel sau advance, không chèn space vào nội dung |
| Mùa | x=0..23, y=0..15; căn phải mép bitmap tại x=23 |
| Ngày / dấu chấm / thứ | x=24..63, y=0..7; số ngày bắt đầu x=27 |
| Đồng hồ | x=24..63, y=8..15; baseline y=14 |
| Advance đồng hồ | 8 pixel cố định cho mỗi tile gốc, kể cả dấu hai chấm |

`draw_run()` đặt glyph bằng advance. Ngày, dấu chấm và thứ là ba run riêng;
không có chuỗi đệm dạng `"30 · T2"` hoặc thêm cột trắng trước bitmap. Số
ngày một chữ số tự kéo nhãn thứ về đúng vị trí theo tổng advance. Clock là
năm ô 8 pixel HH:MM: số 1 có nét hẹp hơn số 0 vốn có trong game, nhưng ô
và vị trí chữ số luôn cố định, không gây nhảy bố cục.

Dấu nặng dùng hàng đầu vùng trái bên dưới; đồng hồ chuyển từ x=8 sang x=24
để hai vùng không giao nhau. Không mở rộng HUD hoặc dịch icon. Không nâng
riêng chữ Hạ nữa: mọi thân chữ dòng ngày cùng baseline, dấu dưới có một hàng
trống và được bảo vệ khỏi đồng hồ bằng cả tọa độ X lẫn Y.

Hai buffer vẫn ở object+0x84 và +0x1A8 (256 byte mỗi buffer), cờ upload
+0x18C và +0x2B0. Cache tổng **40.576 byte**: mùa 4×192, ngày/thứ 210×160,
giờ 24×96, phút 60×64, nháy 2×32. Mùa dùng sáu tile gồm hai hàng; setter
chép 192 byte trong buffer đã có. Hour chép một tile vào +0x164 và hai tile
vào +0x228; minute vào +0x268, colon blink vào +0x248. Không ghi metadata
lân cận, ngày giờ gameplay hay dữ liệu save.

[Ảnh bố cục trước/sau, trái v5 — phải v6](evidence/date-hud-metrics.png).
Các ảnh v2–v5 là lịch sử, không phải ảnh bản hiện tại; xem tiến độ để biết
những sửa đổi trước. Năm packed date và công thức thứ giữ nguyên từ native
0803CD4C. Đồng hồ dùng 00–23, nhịp tăng 10 phút và nháy dấu hai chấm gốc;
23:59 chỉ là fixture kiểm tra bộ vẽ.

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

98 pytest đạt; có kiểm tra khoảng trống bằng pixel cho toàn bộ 30 ngày × bảy thứ
và mép phải của bốn tên mùa. Kiểm tra baseline mọi chữ/số; advance cố định,
đủ dấu nặng dưới baseline, khoảng trống cả bóng, từ chối cắt glyph. Chạy cùng kiểm tra trên mGBA 0.10.5 và 0.11-dev:

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
