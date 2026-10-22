# Việt hóa menu START

Phạm vi: menu tạm dừng mở bằng START trong khi chơi, gồm các màn con. Hai prompt
Bắt đầu/Tiếp tục ở title đã được xử lý ở phiên trước.

Thêm **162 bản ghi nháp** trong `localization/{en,vi}/start_menu.json`, không
trùng các ID đã dịch. Bao gồm Nhật ký (lưu/tải, tệp, nút bấm, đồng hồ, chân dung,
tên, xác nhận/lỗi), hai tiêu đề Ba lô, mô tả địa điểm và giờ mở cửa trên bản đồ,
các bảng tài sản/chú lùn/thu chi/cấp dụng cụ, Ghi chú/kỷ lục, lựa chọn Hướng dẫn
và toàn bộ 21 chuỗi duy nhất của sách Mẹo điều khiển. Demo trồng trọt/chăn nuôi
dùng các script đã dịch trong `intro.json`.

## Nguồn xác minh

ROM A4NE rev 0 có SHA-1 trong README. Tham khảo StanHash/fomt b8471ae:

| Nhóm | Dữ liệu/nguồn |
| --- | --- |
| Nhật ký | `asm/new_game.s`, 08003BC0..080048A0; bảng 18 con trỏ file 0xE8704 |
| Ba lô | `asm/code_0803EE94.s` 0808C2F0/0808C2F4; constructor 080CAFC4/080CC15C trong `asm/code_809E804.s` |
| Thống kê/Ghi chú | Các literal trong `asm/code_0803EE94.s`, dữ liệu file 0xFB824..0xFC008 |
| Bản đồ | 40 descriptor ở file 0xFD080..0xFD3A0, stride 20; hai trường đầu là con trỏ văn bản |
| Hướng dẫn | `asm/code_linkonce.s` 080D8D8C..080D8D98 và 080D99A4..080D99B0 |
| Sách mẹo | 0x1084AC → 0x1157D0, 27 con trỏ dòng; đã thấy qua START → Hướng dẫn → Mẹo hay |

`tools/start_menu.py` lưu whitelist offset, từng con trỏ và byte nguồn chính xác.
Extractor kiểm tra chúng trước khi tạo bản ghi. Inserter trích xuất lại từ ROM
nguồn và chỉ sửa những trường này, không dùng địa chỉ do người dịch tự nhập.
Chuỗi dùng chung được đổi ở các call-site đã xác minh, gồm cả màn tải từ title.
Giữ nguyên các RAW 81A1 (ô vuông trang trí), WAIT, CR và LF.

## Hai bộ vẽ đặc biệt

Tiêu đề Ba lô có buffer **12 byte** tại object+0x28C, trường kích thước túi kế
ngay sau ở +0x298. Game gốc chỉ sao chép tối đa 8 byte. “Dụng cụ” là 7 ô/9 byte,
“Vật phẩm” là 8 ô/10 byte nên bị cắt dù còn vừa khung 64px. Bản vá nâng trần lên
11 byte, giữ NUL trong buffer cũ, và tính chiều ngang theo ô glyph. Mã EBxx dùng
một ô; mã Nhật cũ vẫn hai ô. Không tăng object, VRAM hoặc sức chứa túi.

Hai cặp lệnh giới hạn ở 0xCB05A/0xCB05E và 0xCC1F8/0xCC1FC; hai điểm tính rộng
ở 0xCB178/0xCC414. Các nhãn bảng thống kê có padding theo số ô của nguồn để
không để sót dữ liệu hình ở cuối vùng tile cố định.

Tiêu đề sách ở 0807A216 vẽ từng byte thành một OBJ, khác bộ vẽ phần thân. Riêng
con trỏ tiêu đề Mẹo điều khiển được chuyển sang cache 8x16px/ô có dấu đầy đủ,
sau đó đi qua lệnh upload gốc 0807A252. Sách/thư khác đi nhánh gốc. Hook ở địa
chỉ lệch 2 byte dùng trampoline **10 byte**, có literal căn 4 byte; không dùng
trampoline 8 byte vốn yêu cầu địa chỉ chia hết cho 4. Không thêm OBJ hay VRAM.

## Kiểm thử

```bash
# Sau khi build theo README và chạy emulator_smoke.py để tạo SRAM trong game:
.venv/bin/python tools/start_menu_smoke.py build/fomt-vi-demo.gba \
  --sram build/start-full-final-0.10.5/save-test.sram \
  --library build/mgba_bridge-0.10.5.so \
  --output-dir build/start-final-0.10.5
```

79 pytest đạt. mGBA 0.10.5 và 0.11-dev kiểm tra 197 trường con trỏ, 239 dòng qua
bộ vẽ thật với vùng canh bộ nhớ, hai buffer tiêu đề và trường sức chứa túi kế
cận, cache tiêu đề sách trong OBJ VRAM. Replay bình thường qua 7 menu, 6 hàng
Nhật ký, xác nhận lưu/tải, các trang thống kê có thể mở, sách mẹo và lựa chọn
trồng trọt/chăn nuôi. Bộ smoke chung kiểm tra thêm font/title, tạo game và lưu
SRAM rồi cold boot tải lại; không phát hiện lỗi emulator.

Xem [ảnh tổng quan](evidence/start-menu.png) và
[báo cáo](evidence/start-menu-validation.json). Duyệt ảnh trực tiếp; smoke không
OCR và không tự chứng minh mọi bố cục đều đúng trong mọi trạng thái save.

Còn lại: chữ đồ họa ngày/giờ SP/Mon/AM và đơn vị D giữ nguyên; save thử chưa có
vật nuôi/cá nên chưa đi qua tự nhiên mọi danh sách hoặc mọi điểm bản đồ. Những
nhãn đó đã qua kiểm tra con trỏ và probe bộ vẽ. Các tên riêng như Staid/Nappy/
Bold giữ nguyên. Chưa kiểm thử trên máy GBA thật hoặc chơi xuyên mùa.
