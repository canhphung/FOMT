# Việt hóa intro mở đầu

Subset `localization/{en,vi}/intro.json` gồm **145 ID**, xác minh từ ROM USA
revision 0 và StanHash/fomt commit `b8471ae065744869f64283473ed68372f82321c9`.
10 câu Thomas có sẵn được chuyển khỏi pilot để tránh trùng ID. Intro thêm
135 bản dịch, nâng tổng lên **544/9.121** mục catalog; chưa Việt hóa toàn game.

## Nội dung và nguồn

| Nhóm | Số ID | Nguồn |
| --- | ---: | --- |
| Nhãn Mẹ/Bố/Ông lão/???/Cô bé | 5 | C-string `0xFB234`, `0xFB27C`, `0xFB300`, `0xFB51C`, `0xFB53C` |
| Hồi tưởng thời thơ ấu, lời hẹn viết thư | 23 | C-string `0xFB23C`–`0xFB7F0`, từng literal slot trong `func_0805F5F4` |
| Thomas đón người chơi, nhận trại, chuyển ngày | 10 | SCR 867 |
| Buổi sáng đầu tiên: Thomas, Zack, lựa chọn hướng dẫn | 22 | SCR 737 |
| Chọn gà/bò/cừu | 5 | SCR 1059 |
| Demo nuôi bò | 21 | SCR 1060 |
| Demo nuôi gà | 19 | SCR 1061 |
| Demo nuôi cừu | 21 | SCR 1062 |
| Demo trồng trọt | 19 | SCR 1063 |

Địa chỉ là **file offset**, cộng `0x08000000` để ra địa chỉ CPU. Mỗi C-string
ghi địa chỉ và toàn bộ literal slot đã kiểm tra trong `tools/intro_text.py`;
source đối chiếu là `asm/code_0803EE94.s`, scene `0x0805EE44`, dispatcher
`0x0805F5F4`. SCR dùng bảng `0xF89D4` và parser đã có. Không đổi CODE/JUMP,
thứ tự string, placeholder, control code, logic hướng dẫn hoặc dữ liệu gameplay.

Xưng hô: bố/mẹ–con, ông–cháu, cô bé tớ–cậu, Thomas bác–cháu, Zack tôi–cậu.
Giữ tên Thomas, Zack, Mineral Town và phần tên riêng Yodel. Glossary ghi rõ
thuật ngữ thùng xuất hàng, rương dụng cụ, máng ăn, ổ ấp và tên hai trại.
`???` và dấu chấm than RAW:8149 được giữ nguyên có chủ đích.

## Nhãn người nói và menu

`func_08050B50` gốc kiểm tra 1–12 byte rồi chia tên thành ba nhóm 4 byte.
Chuỗi Việt EBxx có thể bị cắt giữa hai byte hoặc bị chèn khoảng trống trong từ.
Cache mới raster hóa từng tên thành 12 ô 8×16, xếp lại ba block 4×2 tile,
**768 byte/tên**, dùng mask font v2 và palette hiện có.

Hook tại `0x50B50` nhận đúng các pointer nhãn intro đã chuyển sang ROM mở rộng.
Khi khớp, copy ba block vào `widget+0x1F8+i*0x104`, bật cờ upload tại `+0x1F0`.
Nếu không khớp, thực thi nguyên prologue bị thay rồi quay lại `0x08050B59`.
Không thay renderer toàn bộ tên game, không tăng OBJ/VRAM hoặc hỗ trợ UTF-8.

Menu bốn lựa chọn trong `func_08050478` có giới hạn `strlen` **12 byte/mục**.
“Mẹo hữu ích” vừa số ô nhưng vượt byte nên bị game ẩn; dùng “Mẹo hay” và thêm
metadata/validator theo nguồn để ngăn lặp lại. Menu Có/Không dùng tối đa 26 byte,
câu hỏi tối đa 28 byte. Budget được lấy lại từ extractor khi build, không tin
metadata đã sửa trong bản dịch. Control stream của cả 145 ID giữ nguyên.

## Kiểm chứng

72 pytest đạt, không skip. Kiểm tra literal/prologue identity, giới hạn byte,
chèn lại đủ 145 ID và bảo toàn CODE/JUMP của cả bảy SCR. Build có thể tái tạo
và IPS apply phải khớp hash trong `patches/manifest.json`.

`tools/intro_smoke.py` chạy trên mGBA **0.10.5** và **0.11-dev**:

- Replay từ cold boot, tạo người chơi tên dài 12 ký tự bằng bàn phím gốc.
- Đi hết hồi tưởng, nhận trại, chuyển ngày, ra khỏi nhà gặp Thomas và Zack.
- Thử cả Có/Không, Mẹo hay, Trồng trọt và demo gà/bò/cừu qua các nhánh menu.
- Theo dõi reader thật tại `widget+0xEC`, cursor `+0xF4`, marker vtable
  `0x080E78C0` ở `+0xD0`. Chứng kiến **129/129 ID hội thoại**, lưu 199 ảnh chờ
  nhấn nút; offset/ID/phase/ảnh có trong báo cáo. Không inject câu thoại vào RAM.
- So đúng raster của cả **5 nhãn người nói** trong buffer game đang hiển thị.
  11 ID lựa chọn nằm trong ảnh menu; reader không giữ pointer của chúng.
- Probe cô lập **460 dòng** qua renderer chuỗi thật, có guard trước/sau buffer,
  dự phòng tên dài; so native fallback với control ROM chỉ phục hồi prologue
  của renderer tên cho Thomas/Zack/tên dài/tên vượt giới hạn. Phân biệt các
  probe này với bằng chứng replay tự nhiên.

Smoke toàn pipeline vẫn kiểm tra title/font/menu/Diary save và cold-boot load
trên cả hai mGBA. Sau khi dịch, số lần nhấn A để qua intro thay đổi; smoke nay
dừng ở WAIT thật của câu chuyển ngày, tránh vô tình mở TV rồi chặn nút Start.
Không sửa code game để bài test qua.

```bash
.venv/bin/python tools/text_inserter.py "$FOMT_ROM"
.venv/bin/python tools/intro_smoke.py build/fomt-vi-demo.gba \
  --base-rom "$FOMT_ROM" --library build/mgba_bridge-0.10.5.so \
  --output-dir build/intro-final-0.10.5
```

Ảnh tổng hợp [intro-opening.png](evidence/intro-opening.png) ghép framebuffer
thật, phóng nearest-neighbor 2 lần; nhãn báo cáo nằm ngoài vùng game. Đã xem các
ảnh chính và menu; chưa duyệt thủ công từng frame trong 199 ảnh, chưa thử GBA
thật hoặc mọi event ngoài intro. Các bản dịch vẫn ở trạng thái nháp.
