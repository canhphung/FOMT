# Tiến độ Việt hóa hiện tại

Cập nhật 2026-10-23. Baseline mã/build: `f8e1af2`; roadmap: `7420c5c`.
Bản vá thử nghiệm, chưa phải Việt hóa 100%.

## Nội dung

| Hạng mục | Có bản dịch nháp / đã trích xuất |
| --- | ---: |
| Tổng catalog | 722 / 9.283 |
| Tên vật phẩm | 346 / 347 |
| Mô tả vật phẩm | 37 / 347 |
| Nhãn menu tạm dừng | 7 / 7 |
| Tạo game mới | 24 / 24 |
| Intro/hướng dẫn đầu game | 145 bản ghi |
| Menu con START | 162 bản ghi |
| Lời chào Popuri | 1 bản ghi |

722 ID không trùng nhau; chưa có ID đánh dấu `reviewed`. Còn 8.561 bản ghi
chưa dịch trong catalog; 8.250 chuỗi mang ngữ cảnh chưa phân loại. Hai số
này là hai chỉ số riêng, không cộng với nhau. Tỷ lệ khoảng 7,8% ID không phải
phần trăm toàn bộ game hoặc lượng từ đã hoàn thành.

Đồ họa theo dõi riêng: Bắt đầu/Tiếp tục, tạo game, lịch và HUD. Font Việt,
con trỏ title, bố cục ngày/giờ và tiêu đề lịch đã được triển khai. Nguồn
trong localization/, chi tiết từng adapter trong các tài liệu hệ thống.

## Kiểm chứng gần nhất

- 113 pytest đạt với ROM USA rev 0 được người dùng cung cấp.
- mGBA 0.10.5/0.11-dev: boot/title/font, tạo game, START và Diary save/load
  qua cold boot; báo cáo gắn đúng hash target hiện tại.
- 2.580 tổ hợp packed date/time, 300 setter, chín fixture HUD có kiểm VRAM.
- 56 fixture lịch: kiểm OAM/texture/tile cache của tiêu đề; phần body từ
  y=40 khớp bản gốc. Tám chu kỳ mở/đóng trả lại tài nguyên; SRAM không đổi.
- Kiểm round trip IPS và hash bản build. Số ngày trong lịch và HUD giữ nguyên.

[Báo cáo hiện tại](evidence/date-ui-validation.json),
[tổng hợp](evidence/validation.json), [manifest bản vá](../patches/manifest.json).
Báo cáo intro/tạo game/START chuyên biệt mang hash của các mốc trước; giữ
làm bằng chứng phạm vi từng mốc, không coi là chạy lại toàn bộ trên target mới.

## Còn thiếu

- Phân loại ngữ cảnh/người nói, phần lớn hội thoại NPC và sự kiện.
- 310 mô tả vật phẩm và một tên vật phẩm cần xác minh.
- Kiểm kê UI còn thiếu, TV/sách/hướng dẫn và đồ họa chữ ngoài catalog.
- Duyệt nghĩa/xưng hô/thuật ngữ; chưa encounter Popuri tự nhiên trong bằng chứng hiện có.
- Chưa chơi xuyên mùa/toàn bộ nhánh, chưa kiểm mọi save cũ hoặc GBA thật.
- Mốc năm 200 đã xác minh là giới hạn hiển thị lịch; chưa xác minh hành vi
  gameplay khi vượt mốc đó.

Đã có glossary/hồ sơ theo cảnh, hàng đợi và lô 16 mô tả dụng cụ.
Ưu tiên tiếp theo: duyệt nghĩa/bố cục lô đầu, rồi mở rộng mô tả và trace Thomas. Xem [ROADMAP_VI.md](ROADMAP_VI.md).

## Phiên dọn project — 2026-10-23

- Dọn khoảng 627 MiB ROM thử, savestate, ảnh debug và log cũ khỏi build;
  giữ build/smoke mới nhất (khoảng 20 MB).
- Bảo toàn sáu nội dung save khác nhau, ghi nguồn/hash vào local-data/fixtures;
  chuyển font tham khảo do người dùng gửi sang local-data/reference-font.
- Xóa 16 ảnh thử HUD lỗi thời và hai bản sao ảnh tổng hợp. Bằng chứng hiện tại
  vẫn giữ; đường dẫn báo cáo trỏ về ảnh tổng hợp duy nhất, hash ảnh không đổi.
- Rút gọn lịch sử sửa font trong tài liệu, bổ sung cấu trúc project và make clean.
  Không thay đổi mã ROM, bản dịch hoặc IPS; số ID nháp/duyệt không đổi.
- Kiểm lại make build: cùng hash ROM/IPS; 113 pytest đạt. Cold boot trên cả
  hai adapter mGBA đạt. 67 liên kết tài liệu, 72 hash bằng chứng và sáu save
  được bảo toàn đã đối chiếu. make clean được kiểm bằng dry-run.

## Lịch sử chi tiết

Nhật ký các phiên và ảnh thử trước khi dọn vẫn có trong
[lịch sử Git tại 7420c5c](https://github.com/canhphung/FOMT/blob/7420c5cbb294eb84b0ea0c0bcc1393c4ab21206b/docs/TRANSLATION_PROGRESS.md).
Các địa chỉ nguồn, giới hạn và cách build hiện tại nằm trong tài liệu hệ thống;
không cần mang toàn bộ nhật ký từng pixel vào bản checkout mới.

## Phiên glossary, hàng đợi và lô tools-01 — 2026-10-23

Glossary 389 thuật ngữ, bảy hồ sơ người nói theo phạm vi đã xác minh; chọn
Thomas script 867 (chín câu đón người chơi) làm lô NPC đầu tiên để duyệt.
Wiki Fandom do người dùng gửi bị proxy chặn 403 CONNECT, không nhập dữ kiện
chưa đọc. Thống nhất Hè/hè trong menu sinh nhật và ba chuỗi START; tên
The Summer Sun vốn đã dùng hè.

Thêm localization_queue.py xuất JSON/CSV, lọc batch/context/speaker/trạng thái.
QA gắn hash nguồn/bản dịch; tự phát hiện stale, token/độ dài sai; tách
duyệt ngôn ngữ, bố cục, renderer và playtest. Flower vẫn blocked.
Hàng đợi đầy đủ: 310 cần dịch, 722 chờ QA, 8.251 blocked, 0 done.

Thêm 16 mô tả liềm/cuốc nguồn ROM đã xác minh, giữ token/pointer relocation.
Hai mGBA kiểm 16 pointer và 48 dòng render có guard; ảnh chẩn đoán không
phải cửa sổ vật phẩm thật. Chưa playtest đủ dụng cụ hoặc duyệt bố cục/ngôn
ngữ; vẫn 0 reviewed. 113 pytest đạt; regression font/title/START, tạo game,
lịch/HUD, save/load cold boot được chạy trên cùng target hash mới.
[Quy trình](LOCALIZATION_WORKFLOW.md), [báo cáo lô](evidence/items-batch-validation.json).

## Thử lại wiki sau khi mở quyền — 2026-10-23

Lúc 08:52 UTC, cả trang Fandom được cung cấp và API `action=parse` trên
cùng host trả HTTP 402: “Please contact the site owner for access.”
Đã vượt qua lỗi proxy CONNECT 403 của lần trước nhưng chưa lấy được nội
dung bài. Chưa thể đối chiếu glossary, nhân vật hoặc xưng hô với wiki.
Cập nhật trạng thái nguồn tham khảo; không sửa bản dịch hoặc đánh dấu QA
đã duyệt dựa trên nội dung chưa đọc.
