# Tiêu đề lịch: Năm {số} — Mùa {tên mùa}

V19 sửa khoảng cách và số năm trên lịch. Nhãn Năm/Mùa/tên mùa dùng cùng
bitmap native như trước. Số năm giữ dáng đậm của số lịch gốc nhưng được
raster riêng vào vùng 9x13, thay vùng nhìn thấy 8–12x15 trước đó. Không dùng
font vector, anti-aliasing hoặc scaling trong game. Bản sao số nhỏ chỉ dùng
ở tiêu đề; số ngày, màu cuối tuần và toàn bộ lưới lịch giữ nguyên.

## Bố cục

- Căn giữa cả dòng theo chiều rộng mực/bóng, thay hai tọa độ cố định 40/128.
- Năm ↔ số năm: 4 cột trống; số ↔ cụm mùa: 6 cột trống.
- Các từ trong “Mùa Xuân”, “Mùa Đông”, v.v. có 4 cột giữa foreground,
  còn 3 cột sau khi tính bóng. Dùng advance và metric, không thêm space lặp.
- Dấu phân cách mảnh 5x1, cùng màu chữ và bóng gốc; có khoảng trống với từ,
  không vẽ đậm hơn chữ. Nó vẫn nằm trong nhãn mùa để không thêm OAM.
- Số năm dùng advance cố định 10 pixel; năm 1–200 có một/hai/ba chữ số.
  Có 12 layout (bốn mùa × ba độ dài) được tính từ chính bitmap rồi nhúng vào ROM.

Những canvas trong suốt không được dùng làm khoảng cách giữa từ. Bộ vẽ
đặt từng frame theo bounding box thật. Mỗi nhãn mùa dùng hai OBJ 32x16,
Năm dùng một OBJ 32x16, mỗi chữ số năm dùng OBJ 16x16 với phần mực nhỏ hơn.
Không thay kích thước màn lịch hoặc icon lễ hội/con trỏ.

## Resource và VRAM

Vẫn đúng 22 frame/animation native. Frame 0–9 giữ shape/parts của số ngày;
phần bitmap đầu 4 tile là bản sao **nguyên byte** của số gốc. Thêm 4 tile
số năm nhỏ ngay sau mỗi số ngày. Native uploader 080A2BA4 tải từng frame,
nên không đặt số năm vào dữ liệu cuối không có frame tham chiếu.

Bốn nhãn mùa tăng từ 48 lên 64 pixel để đủ chữ và khoảng trống. Hai part
32x16 mới nối vào bảng part; các part cũ giữ nguyên. Palette, animation,
frame index, thứ trong tuần và tính ngày/sự kiện không đổi.

Tổng texture 180 tile = 5.760 byte. Constructor 080A220C cấp phát bằng API
native order 8 (256 tile = 8.192 byte), thay order 7 (128 tile). Offset file
**0xA234A**, kiểm tra sáu byte nguồn `072165f702fc` trước khi đổi immediate
`0721` thành `0821`. Tăng reservation 4 KiB OBJ VRAM; không tăng object RAM.
Không sửa allocator chung, không ghi vào vùng VRAM chưa được cấp phát.

Khi vẽ số năm, wrapper tạm chọn 4 tile bổ sung bằng entry cache tại
object+0x140+digit*2; native frame renderer lập draw command, rồi wrapper
trả lại entry ngay. Các số ngày về sau vẫn dùng tile gốc. Mỗi fixture
kiểm cache 10 chữ số đã trả lại, đồng thời đối chiếu toàn bộ texture thật
trong VRAM và tọa độ/tile index của tất cả OBJ tiêu đề.

## Kiểm chứng

106 pytest đạt, gồm từ chối source allocator bị sửa, bảo toàn số ngày,
parts/palette/animation, kiểm khoảng cách và căn giữa 800 tổ hợp năm/mùa.
Hai mGBA 0.10.5/0.11-dev kiểm:

- 56 fixture lịch: năm 1/7/8/10/99/100/200 × bốn mùa × ngày 1/30.
  Vùng từ y=40 trở xuống, grid và event marker khớp từng pixel với ROM gốc.
- Tọa độ mọi OBJ tiêu đề khớp layout; đủ 180 tile thật trong OBJ VRAM;
  glyph số năm đúng tile; cache số ngày được trả lại sau mỗi lượt vẽ.
- Tám lần mở/đóng lịch bằng nút A/B: số handle/refcount tài nguyên trở lại
  như trước; không thay SRAM nếu không dùng thao tác lưu.
- Chín ảnh HUD giữ nguyên từng pixel so với v18. START/font/title và
  Diary save/cold boot/load chạy lại trên bản ROM cùng hash.

[Ảnh trước/sau](evidence/calendar-heading.png) ·
[Báo cáo máy đọc được](evidence/date-ui-validation.json).

Đây là kiểm tra emulator và fixture giao diện, chưa phải chơi xuyên mùa
hoặc kiểm chứng trên GBA thật. Bản vá IPS yêu cầu ROM USA rev 0 trong README.
