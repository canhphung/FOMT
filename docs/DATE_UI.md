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

## HUD

Giữ nguyên hai OBJ 32x16 pixel, vị trí, palette, các cờ cập nhật, vùng đệm và
biểu tượng thời tiết. Không thêm heap object, OBJ hay VRAM. Chữ mùa/thứ dùng
font pixel có dấu: thân chữ hoa/số cao 6 pixel, chữ thường cao tối đa 5 pixel,
chữ hoa rộng 5 pixel và chữ thường/số rộng 4 pixel. Có phần cho dấu trên/dấu nặng;
nguyên âm có dấu dùng thân gọn 4 pixel để dành khoảng trống cho dấu.
Số ngày dùng cùng font; dấu nặng có thân nâng một hàng để dấu không dính. Chữ số đồng hồ giữ tile gốc.
Nội dung vừa vùng 64x16 pixel.

Hai buffer nằm tại object+0x84 và +0x1A8, mỗi buffer 256 byte. Cờ upload là
+0x18C và +0x2B0. Cache thành phần chiếm tổng 40.192 byte trong ROM: bốn mùa, 210 cặp
ngày/thứ, giờ, phút và hai pha nháy dấu hai chấm. Các setter chép đúng các tile
thành phần; không sửa cấu trúc ngày giờ nguồn hoặc dữ liệu save.

Bản `vietnamese-date-24h-spacing-v2` căn mép phải phần mực và bóng của tên
mùa tại x=23. Số ngày bắt đầu tại x=27; giữa mùa/ngày, ngày/dấu chấm và dấu
chấm/thứ đều có đúng ba cột trong suốt. Ngày và thứ được vẽ chung thành một
suffix 40x8: nhãn thứ dịch ngang theo độ dài số ngày, không còn ô hàng chục trống ở
ngày 1–9. Tên mùa ngắn không tạo khoảng trống lớn trước số ngày. Mỗi setter
ngày vẫn chép 160 byte như trước; cache tăng trong ROM, không tăng RAM/VRAM.

Bản `vietnamese-date-24h-large-v3` tăng thân chữ hoa/số từ 5 lên 6 pixel,
chữ thường từ 4 lên 5 pixel; chiều ngang thân chữ tăng thêm 1 pixel.
Giữ các mốc x và khoảng cách ba pixel của v2. Chữ lớn hơn vẫn vừa 64x8 ở
dòng trên, không đổi cỡ đồng hồ, vùng đệm, cache, RAM hay VRAM.

Bản `vietnamese-date-24h-accents-v4` sửa lỗi dấu ở v3: dấu mũ rộng 4 pixel,
cân giữa thân nguyên âm rộng 4 pixel; đỉnh tại x=1/2 và chân tại x=0/3.
Dấu mũ ở y=0/1, y=2 trống hoàn toàn (cả bóng), thân â/ô ở y=3–6.
Với ạ, thân ở y=2–5, y=6 trống hoàn toàn, dấu nặng cân giữa ở y=7.
Không vẽ bóng dưới dấu hoặc vào hàng phân cách. Giữ chiều ngang chữ lớn,
cỡ chữ hoa/số, khoảng cách 3 pixel và cùng dung lượng cache của v3.

[Ảnh sửa dấu: bên trái v3, bên phải v4](evidence/date-hud-accents.png) ·
[Ảnh tăng cỡ chữ ở v3](evidence/date-hud-size.png) ·
[Ảnh sửa khoảng cách ở bản v2](evidence/date-hud-spacing.png).

Năm trong packed date là mã chu kỳ gốc; phép tính thứ giữ nguyên công thức
của 0803CD4C. Giờ được vẽ 00–23, có số 0 đầu. Nhịp nháy dấu hai chấm được giữ.
Các giá trị 00:00, 12:00 và 23:59 có kiểm tra riêng; 23:59 là giá trị thử bộ vẽ,
không phải tuyên bố đồng hồ trong gameplay đổi sang tăng từng phút.

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

96 pytest đạt; có kiểm tra khoảng trống bằng pixel cho toàn bộ 30 ngày × bảy thứ
và mép phải của bốn tên mùa. Ba kiểm tra thêm cho â/ô/ạ xác minh dấu cân giữa
và hàng phân cách không chứa mực hoặc bóng. Chạy cùng kiểm tra trên mGBA 0.10.5 và 0.11-dev:

- 2.580 trường hợp packed date/time qua CPU thật, có canh bộ nhớ; bao phủ mọi
  ngày 1–30, bốn mùa, bảy chu kỳ thứ và toàn bộ 24x60 giá trị giờ/phút.
- 300 lần gọi các setter riêng, giữ nguyên các thành phần lân cận và metadata.
- Chín fixture HUD qua đường upload thật, so byte buffer với OBJ VRAM; có ảnh
  06:50, 00:00, 12:00, 23:59, đủ bốn tên mùa với ngày một/hai chữ số và
  cặp ngày 9/10 để kiểm tra thay đổi độ dài.
- Mở lịch tự nhiên bằng A tại lịch treo tường trong nhà. 56 fixture giao diện:
  năm 1/7/8/10/99/100/200 × bốn mùa × ngày chọn 1/30. Grid, event marker và
  toàn bộ pixel từ y=40 xuống dưới khớp ROM gốc. Các fixture chỉ đổi trường
  xem của UI và chạy hàm bố cục native; không phải chơi qua 200 năm.
- Đóng lịch trở về nhà, SRAM giữ nguyên; smoke chung chạy tạo game, font/title,
  lưu Diary rồi cold boot tải lại. Smoke menu START cũng chạy lại.

Đã duyệt ảnh trực tiếp, có hash trong báo cáo. Không có lỗi emulator. Chưa
kiểm tra trên máy GBA thật hoặc chơi xuyên mùa; các báo cáo intro/START chi
tiết cũ vẫn giữ hash của những bản build trước.
