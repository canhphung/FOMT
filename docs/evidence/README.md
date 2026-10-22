# Chứng cứ kiểm thử

Target ROM và bản vá được định danh trong `validation.json` và
`../../patches/manifest.json`. Không có ROM hoặc save người dùng trong thư mục này.

- `thomas-dialogue.png`, `thomas-three-lines.png`: ảnh framebuffer mGBA khi chơi
  mới bằng nút bình thường, không thay câu thoại bằng RAM injection.
- `pause-menu.png`: ghép 7 ảnh framebuffer khi chọn từng nhãn bằng nút Right.
  Các dòng `pause menu N` nằm ngoài framebuffer, chỉ là nhãn báo cáo.
- `diary-saved.png`: game đã ghi save qua Diary, hiển thị thông tin ngày/người chơi.
- `diary-load-menu.png`: core mới đã nhận SRAM sau boot và hiện cùng save.
- `game-loaded.png`: xác nhận Load trong game, trở lại nhà ngày 2.
- `v1-save-loaded-in-v2.png`: boot ROM v2 bằng mGBA 0.10.5, import SRAM của bản
  v1 rồi Load trong game. Đây là một mẫu save, không phải kiểm thử mọi save cũ.
- `vietnamese-font.png`: atlas từ mask v2 8×16, phóng 3 lần; **không phải
  ảnh game**. Nhãn EBxx đối chiếu với `localization/font/encoding.json`.
- `font-spacing-comparison.png`: output renderer chuỗi mGBA trước (v1) và sau
  (v2), phóng 3 lần. Dòng alphabet là chuỗi chẩn đoán, không phải lời thoại gốc.
- `font-metrics.json`: baseline/bearing/advance đo từ ROM và cmap/metrics OTF
  người dùng gửi. Không đóng gói file OTF; build dùng outline ROM.
- `title-start.png`: framebuffer mGBA 0.10.5, cold boot và nhấn Start để tới
  title; prompt đồ họa đã đổi thành **Bắt đầu**. Không ghép chữ lên ảnh.
- `title-font-comparison.png`: hai framebuffer title trước/sau đổi màu nét,
  phóng nguyên pixel 3 lần; nhãn Before/After nằm ngoài ảnh game. Bản mới dùng
  nét xanh ngọc mảnh 1px và halo trắng; hình dáng giữ nguyên bản v3 đã được duyệt.
- `title-font-sample.png`: artwork tile hiện tại trên nền tối, phóng nguyên
  pixel 3 lần để xem xanh ngọc/trắng; đây không phải framebuffer game.

Ảnh đã được xem thủ công. Các phép so pixel/canary và kết quả pytest nằm trong
`validation.json`. Probe hàm dùng trạng thái emulator cô lập và không được xem
là bằng chứng đã gặp NPC tự nhiên. Lời chào Popuri chưa được kiểm tra bằng encounter.
