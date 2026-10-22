# Việt hóa màn tạo game mới

Nguồn đối chiếu: StanHash/fomt commit
`b8471ae065744869f64283473ed68372f82321c9`, `asm/new_game.s`,
`asm/code_0803EE94.s` và `src/code_0800E2E4.cc`. Chỉ áp dụng FOMT USA revision 0,
SHA-1 `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`.

## Phạm vi và nguồn

`localization/en/new_game.json` và `localization/vi/new_game.json` có 24 ID:
19 chuỗi có con trỏ, 4 hàng mùa và một tiêu đề bằng glyph. Mỗi ID ghi byte nguồn,
ROM offset, literal slot hoặc cấu trúc dữ liệu nguồn. Các offset dưới đây là
file offset; địa chỉ CPU tương ứng cộng `0x08000000`.

| Phần | Dữ liệu nguồn | Nơi tham chiếu |
| --- | --- | --- |
| Your / Farm's / Dog's | `0xE8934`, `0xE893C`, `0xE8944` | literal `0x4EE8`–`0x4EF0` |
| Name / End | `0xE8BF4`, `0xE8BFC`, `0xE8C14` | `0x5F18`, `0x66F4`, `0x6710`, `0x6770` |
| Xác nhận tên | `0xE8C2C`, `0xE8C44`, `0xE8C48` | `0x7028`–`0x7030` |
| Nhãn tổng kết | `0xE8958`, `0xE8968`, `0xE8978`, `0xE8988` | `0x54B8`–`0x54C4` |
| Xác nhận tạo game | `0xE8998`, `0xE89A4`, `0xE89A8` | `0x5904`–`0x590C` |
| Xác nhận ngày sinh | `0xFBD18`, `0xFBD28`, `0xFBD2C` | `0x6DEB4`–`0x6DEBC` |
| Bốn mùa | `char[4][7]` tại `0xF04EE` | getter `0x0800E2E4`, literal `0xE300` |
| Birthday | 8 mã `u16le` từ `0xFBD76` | bảng 43 mã `0xFBD30`, renderer `0x0806E234` |

Các chuỗi con trỏ được chuyển sang ROM mở rộng, căn 4 byte. Bốn mùa dùng bảng
chung với các màn gọi getter mùa, nên Nhật ký/tổng kết cũng hiện Xuân/Hạ/Thu/Đông.
Mỗi hàng vẫn 7 byte, gồm NUL; Đông chiếm đúng 6 byte theo bảng mã Việt của game.
Không tìm kiếm rồi thay thế mọi chuỗi ASCII trùng nội dung.

## Bố cục và giới hạn

- Các nhãn hoàn chỉnh “Tên bạn”, “Tên trại”, “Tên chó” nằm ở vùng tiền tố cũ.
  Vùng Name phía sau được thay bằng 6 khoảng trắng; ô nhập và con trỏ giữ vị trí.
- End thành Xong; biến thể dùng khoảng trắng rộng giữ nguyên 10 token RAW:8140.
- `func_08050664` kiểm tra `strlen` trước khi vẽ: câu hỏi tối đa **28 byte**,
  lựa chọn trong bố cục hai nút tối đa **26 byte**. Bộ chèn kiểm tra cả byte lẫn
  số ô hiển thị theo metadata trích xuất lại từ ROM, không tin budget sửa ở JSON.
  Câu xác nhận cuối dùng “Bắt đầu nhé?” để nằm trong giới hạn byte này.
- Bảng sinh nhật gồm `0123456789SpringSummerFall  Winter_Birthday`. Hook tại
  `0x6E3BC` thay đoạn chuẩn bị gọi renderer bằng copy 64 byte từ cache mới,
  quay lại `0x0806E3CF`. 43 ô × 64 byte = 2.752 byte được nối vào ROM mở rộng;
  loader, sprite count, tile allocation và palette gốc giữ nguyên.
- “Sinh nhật” raster hóa trong dải 64px với bước 7px; các mùa ở dải 48px dùng
  bước 8px. Dấu nặng vẫn nằm trong ô cao 16px. Không giả định game đọc UTF-8.
- Tổng kết dùng tile 100 (cột 4 của nhãn đầu) làm nền trống. Trong “Your name”
  cột này là khoảng trắng; trong “Tên bạn” nó có nét chữ. Đổi lệnh tại `0x5702`
  từ `movs r1,#100` sang `movs r1,#109`: cột 13 được dành làm ô trống. Importer
  từ chối nhãn đầu có ký tự ở cột này để tránh tái phát nền lặp nét chữ.

## Kiểm chứng

67 pytest đạt, gồm pointer identity, byte nguồn, 43 ô cache, giới hạn byte/hàng
cố định, ô nền và bảo toàn bảng ký tự bàn phím. `tools/new_game_smoke.py` chạy
cùng nút trên ROM gốc và ROM Việt từ cold boot, kiểm tra 8 trường hợp
**4 mùa × ngày 1/30**, tên khác nhau cho nhân vật/trại/chó, xóa ký tự, tên dài
12 ký tự và hủy xác nhận tên/ngày sinh/tổng kết. Đối chiếu vùng chọn ngày sinh
và các trường hiển thị trong object tổng kết; không dùng địa chỉ heap cố định.

Các vtable/field được đối chiếu source: name-entry `0x080E5AB4`, chuỗi `+0x461C`;
birthday `0x080E7AC4`, chọn mùa/ngày `+0x449/+0x44A`; summary `0x080E5A98`,
chuỗi tên/ngày/trại/chó `+0x1A34/+0x1A44/+0x1A54/+0x1A64`.

Cả mGBA **0.10.5** và **0.11-dev** đều qua smoke riêng và smoke toàn pipeline:
boot, title, tạo game, intro, menu, font, Diary save và cold-boot load SRAM.
Ảnh framebuffer thật trong [evidence](evidence/new-game-setup.png);
hash/báo cáo trong `evidence/validation.json` và `patches/manifest.json`.

```bash
.venv/bin/python tools/new_game_smoke.py build/fomt-vi-demo.gba \
  --base-rom "$FOMT_ROM" --library build/mgba_bridge-0.10.5.so \
  --output-dir build/new-game-emulator-0.10.5
```

Bàn phím vẫn dùng bộ ký tự gốc; chưa bổ sung nhập tên tiếng Việt có dấu.
Chưa thử GBA thật hoặc mọi save người chơi. Phần lớn hội thoại/menu ngoài phạm vi
này còn tiếng Anh; đây vẫn là bản thử Việt hóa.
