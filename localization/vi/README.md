# Bản dịch nháp

- `pilot.json`: 48 chuỗi — 7 nhãn menu, 15 tên + 15 mô tả nông sản,
  lời chào Popuri và 10 chuỗi mở đầu của Thomas/người dẫn chuyện.
- `items.json`: thêm 337 chuỗi — 331 tên vật phẩm và 6 mô tả len.
- Tổng: 385 ID không trùng nhau. Trạng thái `translated` là bản dịch nháp,
  **không đồng nghĩa đã duyệt ngôn ngữ hoặc chơi thử mọi màn hình**.

Chỉnh `vietnamese_translation`, giữ nguyên `id` và `original_english`.
Không thay đổi các token `{WAIT}`, `{CR}`, `{LF}`, `{PAGE}`, `{VAR:XX}`,
`{RAW:...}` hoặc thứ tự của chúng. JSON dùng UTF-8; ROM dùng bảng mã riêng.
Không thêm xuống dòng bằng ký tự newline thật. Công cụ hiện yêu cầu giữ nguyên
control stream; khi cần chia trang khác phải nghiên cứu và mở rộng validator trước.

`context_evidence` ghi lý do xác định được chức năng/người nói của chuỗi script.
Các chuỗi chưa rõ chức năng trong catalog tổng không tự động được dịch.
Không dùng thay thế từ hàng loạt cho hội thoại thiếu ngữ cảnh.

Tên riêng và thuật ngữ: xem `../glossary.json`. Chỉ dùng `reviewed` sau khi đã
duyệt cả nghĩa, xưng hô, token và bố cục. Chưa có ID nào ở trạng thái này.
