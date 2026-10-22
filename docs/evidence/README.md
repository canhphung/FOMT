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
- `vietnamese-font.png`: atlas từ bitmap nguồn 8×12, phóng 3 lần; **không phải
  ảnh game**. Nhãn EBxx đối chiếu với `localization/font/encoding.json`.

Ảnh đã được xem thủ công. Các phép so pixel/canary và kết quả pytest nằm trong
`validation.json`. Probe hàm dùng trạng thái emulator cô lập và không được xem
là bằng chứng đã gặp NPC tự nhiên. Lời chào Popuri chưa được kiểm tra bằng encounter.
