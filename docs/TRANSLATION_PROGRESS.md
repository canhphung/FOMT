# Tiến độ Việt hóa hiện tại

Cập nhật 2026-10-23. Baseline mã/build: `f8e1af2`; roadmap: `7420c5c`.
Bản vá thử nghiệm, chưa phải Việt hóa 100%.

## Nội dung

| Hạng mục | Có bản dịch nháp / đã trích xuất |
| --- | ---: |
| Tổng catalog | 706 / 9.283 |
| Tên vật phẩm | 346 / 347 |
| Mô tả vật phẩm | 21 / 347 |
| Nhãn menu tạm dừng | 7 / 7 |
| Tạo game mới | 24 / 24 |
| Intro/hướng dẫn đầu game | 145 bản ghi |
| Menu con START | 162 bản ghi |
| Lời chào Popuri | 1 bản ghi |

706 ID không trùng nhau; chưa có ID đánh dấu `reviewed`. Còn 8.577 bản ghi
chưa dịch trong catalog; 8.250 chuỗi mang ngữ cảnh chưa phân loại. Hai số
này là hai chỉ số riêng, không cộng với nhau. Tỷ lệ 7,6% ID không phải
phần trăm toàn bộ game hoặc lượng từ đã hoàn thành.

Đồ họa theo dõi riêng: Bắt đầu/Tiếp tục, tạo game, lịch và HUD. Font Việt,
con trỏ title, bố cục ngày/giờ và tiêu đề lịch đã được triển khai. Nguồn
trong localization/, chi tiết từng adapter trong các tài liệu hệ thống.

## Kiểm chứng gần nhất

- 106 pytest đạt với ROM USA rev 0 được người dùng cung cấp.
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
- 326 mô tả vật phẩm và một tên vật phẩm cần xác minh.
- Kiểm kê UI còn thiếu, TV/sách/hướng dẫn và đồ họa chữ ngoài catalog.
- Duyệt nghĩa/xưng hô/thuật ngữ; chưa encounter Popuri tự nhiên trong bằng chứng hiện có.
- Chưa chơi xuyên mùa/toàn bộ nhánh, chưa kiểm mọi save cũ hoặc GBA thật.
- Mốc năm 200 đã xác minh là giới hạn hiển thị lịch; chưa xác minh hành vi
  gameplay khi vượt mốc đó.

Ưu tiên tiếp theo: glossary, hàng đợi ngữ cảnh/QA và lô mô tả vật phẩm đã
xác minh. Xem [ROADMAP_VI.md](ROADMAP_VI.md).

## Phiên dọn project — 2026-10-23

- Dọn khoảng 627 MiB ROM thử, savestate, ảnh debug và log cũ khỏi build;
  giữ build/smoke mới nhất (khoảng 20 MB).
- Bảo toàn sáu nội dung save khác nhau, ghi nguồn/hash vào local-data/fixtures;
  chuyển font tham khảo do người dùng gửi sang local-data/reference-font.
- Xóa 16 ảnh thử HUD lỗi thời và hai bản sao ảnh tổng hợp. Bằng chứng hiện tại
  vẫn giữ; đường dẫn báo cáo trỏ về ảnh tổng hợp duy nhất, hash ảnh không đổi.
- Rút gọn lịch sử sửa font trong tài liệu, bổ sung cấu trúc project và make clean.
  Không thay đổi mã ROM, bản dịch hoặc IPS; số ID nháp/duyệt không đổi.
- Kiểm lại make build: cùng hash ROM/IPS; 106 pytest đạt. Cold boot trên cả
  hai adapter mGBA đạt. 67 liên kết tài liệu, 72 hash bằng chứng và sáu save
  được bảo toàn đã đối chiếu. make clean được kiểm bằng dry-run.

## Lịch sử chi tiết

Nhật ký các phiên và ảnh thử trước khi dọn vẫn có trong
[lịch sử Git tại 7420c5c](https://github.com/canhphung/FOMT/blob/7420c5cbb294eb84b0ea0c0bcc1393c4ab21206b/docs/TRANSLATION_PROGRESS.md).
Các địa chỉ nguồn, giới hạn và cách build hiện tại nằm trong tài liệu hệ thống;
không cần mang toàn bộ nhật ký từng pixel vào bản checkout mới.
