# Sprite dấu trên HUD — Xuân/Hè

V15 thực hiện thay đổi đã được người dùng đồng ý: thêm **một hàng hiển thị phía
trên** cho dấu huyền của Hè. Thân e, H, đuôi chữ, đồng hồ và icon không dịch.
Dấu vẫn gồm hai pixel chéo, căn giữa thân e, nhưng nâng từ y=0/1 lên y=-1/0
so với vùng HUD cũ. Giữa điểm dấu dưới và mái e có một hàng trống.

## Cách vẽ

Giữ hai OBJ 32x16 và buffer cũ. Bỏ hai pixel dấu khỏi bitmap mùa Hè, rồi vẽ
một OBJ 8x8 trong suốt riêng. Tile chỉ chứa hai điểm foreground, không thêm
bóng hay màu. Sprite dùng palette và cờ mosaic của HUD gốc. V16 dùng chung sprite
cho dấu mũ của Xuân và dấu huyền của Hè; Thu/Đông không thêm OAM entry. Không dùng font vector,
anti-aliasing hoặc scale trong ROM.

Ở vị trí HUD chuẩn (132,140), sprite mới có gốc (148,139), hai điểm tại
(152,139)/(153,140). Trước đó dấu ở (152,140)/(153,141). Thân e vẫn ở chỗ
cũ; clock vẫn bắt đầu (140,148). Độ cao **nhìn thấy** thành 17 pixel thay vì
16, đúng phần mở rộng một hàng đã được đồng ý; icon và khung cũ giữ nguyên.

## Bộ nhớ và tài nguyên

| Tài nguyên | Thay đổi |
| --- | --- |
| RAM object HUD | 0x35C → 0x380, thêm 36 byte ở cuối |
| VRAM OBJ | thêm 1 tile 4bpp 8x8 = 32 byte |
| OAM | tối đa thêm 1 entry, chỉ khi Xuân/Hè và danh sách còn chỗ |
| Cache thành phần HUD cũ | giữ 40.192 byte; hai tile dấu thay phiên, 64 byte riêng trong ROM |
| Save/gameplay | không đổi định dạng, nhịp giờ hay dữ liệu |

Các trường cũ giữ nguyên offset. Phần nối thêm gồm resource handle tại
+0x35C, lệnh upload tại +0x364, cờ upload +0x37C, mã dấu +0x37D (0: ẩn, 1: huyền, 2: mũ).
Setter mùa đánh dấu upload lại để đổi tile khi chuyển Xuân/Hè.
Constructor dùng allocator VRAM native (order 0, một tile), destructor hủy
lệnh truyền đang chờ, trả tile và giảm refcount bằng API native. Không dùng
địa chỉ RAM hoặc VRAM trống đoán trước.

## Điểm hook đã xác minh — A4NE USA rev 0

| Offset file | Vai trò | Kiểm tra |
| --- | --- | --- |
| 0x3C5B0 | constructor wrapper | 8 byte prologue |
| 0x3C5BE | kích thước cấp phát | `d7208000`, đổi immediate d7 → e0 |
| 0x3C7C8 | renderer wrapper | 16 byte prologue, giữ r3 là con trỏ danh sách OAM |
| 0xE0D70 | destructor wrapper | 8 byte prologue |

Các prologue sao chép vào stub chỉ chứa lệnh không phụ thuộc PC. Stub quay
lại phần native bằng BX; các hàm native nằm ngoài tầm BL ±4MiB của phần
ROM mở rộng nên gọi qua veneer BX, có Thumb bit. Renderer giữ và chuyển đủ
năm tham số, gồm r3/OAM và tham số queue ở stack. OAM count 128 được tôn
trọng; khi đầy, không ghi qua cuối bảng. Nguồn: StanHash/fomt b8471ae,
`asm/code_0803A8A4.s`, `asm/code_linkonce.s`, `asm/hardware.s`.

## V16 — chữ â đồng cỡ

Thân â năm hàng 0110/0001/0111/1001/0111, rộng 4 pixel như e, baseline y=6,
advance 5. Dấu mũ gốc được bỏ khỏi buffer mùa và nâng bằng sprite tại
(144,139), bốn điểm (147,139)/(148,139)/(146,140)/(149,140). Thân từ y=142
đến y=146, nên y=141 trống. Các phần X/u/n, ngày/thứ, clock/icon không dịch.
Resource VRAM và RAM của v15 được tái sử dụng; chỉ thêm tile thay phiên
32 byte trong ROM. V16 vẫn giữ nguyên pixel của toàn bộ Hè so với v15.

## V17 — thu hẹp H–è

Bearing X của è từ 2 xuống 1, advance 7 → 6. Dấu logic dịch theo bearing,
nhưng nhãn mùa căn phải giữ nguyên e/dấu trong game. H dịch phải một pixel,
để hai cột trống giữa foreground (một cột giữa bóng H và e). Không đổi
sprite dấu, tile/VRAM, RAM, OAM hay đồng hồ. Các mùa khác giữ nguyên.
[Ảnh trước/sau](evidence/date-hud-he-spacing.png).

## V18 — gần thêm một pixel theo ảnh mẫu

Bearing X của è về 0, advance về 5; dấu logic dịch cùng bearing. Nhãn căn
phải nên e/dấu vẫn giữ nguyên tọa độ màn hình, chỉ H tiến thêm một pixel
so với v17. Giữa foreground hai chữ còn một cột; bóng H chạm sát e nhưng
foreground không dính nhau. Không đổi màu, bitmap hoặc chiều cao.
[Ảnh trước/sau](evidence/date-hud-he-spacing-tight.png).

## Kiểm chứng

106 pytest đạt, gồm từ chối các prologue/kích thước nguồn bị thay đổi.
Trên cả mGBA 0.10.5 và 0.11-dev:

- 2.580 trường hợp date/time, 300 setter có guard và kiểm tra metadata.
- Chín fixture HUD: tile dấu được upload qua queue thật vào VRAM; OAM,
  palette, mosaic và trạng thái bật/tắt theo mùa được đối chiếu.
- So toàn ảnh 240x160 với v18: v19 chỉ sửa lịch, chín fixture HUD giữ
  nguyên từng pixel.
- 64 vòng constructor/destructor: refcount manager, số handle và bitmap
  slot tài nguyên trở lại đúng giá trị trước mỗi vòng.
- OAM count đầu 0/127/128 kết thúc 5/128/128, guard không đổi; renderer
  nhận đúng r3 và tham số thứ năm.
- 56 fixture lịch, mở/đóng lịch tự nhiên, smoke font/title/START và lưu
  Diary rồi cold boot tải lại. Dữ liệu SRAM giữ đúng như kiểm tra trước.

[Ảnh trước/sau v16](evidence/date-hud-a-balanced.png) ·
[Glyph a/â/è chín hàng, phóng 4x](evidence/hud-a-glyph.png) ·
[Báo cáo](evidence/date-ui-validation.json).

Đây là kiểm tra emulator và các fixture giao diện, không phải chơi xuyên mùa
hoặc kiểm tra trên GBA thật. Các fixture chỉ thay dữ liệu của UI để xem đủ
mùa/ngày; không thay packed date của gameplay hay save.
