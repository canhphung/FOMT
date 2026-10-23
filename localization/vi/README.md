# Bản dịch nháp

| File | ID có bản dịch nháp |
| --- | ---: |
| `pilot.json` | 149 |
| `items.json` | 648 |
| `new_game.json` | 24 |
| `intro.json` | 145 |
| `start_menu.json` | 162 |
| `item_descriptions_tools.json` | 16 |
| **Tổng, không trùng ID** | **1144** |

Các file title/lịch/HUD là cấu hình đồ họa, theo dõi riêng với catalog text.
Trạng thái `translated` không đồng nghĩa đã duyệt ngôn ngữ hoặc chơi thử
mọi màn hình. Hiện chưa có ID nào đánh dấu `reviewed`.
[Roadmap](../../docs/ROADMAP_VI.md) ghi thứ tự mở rộng nội dung và QA.

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

Hàng đợi/ngữ cảnh/QA và quy trình lô: [LOCALIZATION_WORKFLOW.md](../../docs/LOCALIZATION_WORKFLOW.md).
