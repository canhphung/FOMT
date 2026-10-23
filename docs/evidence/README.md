# Bằng chứng kiểm thử

ROM/save đầu vào không được track ở đây. Mỗi báo cáo phải được đọc cùng
hash target và giới hạn ghi trong chính báo cáo, không suy từ tên ảnh.

## Bản vá hiện tại

- [Manifest](../../patches/manifest.json): hash nguồn/đích và IPS hiện tại.
- [Tổng hợp](validation.json): font/title/save/load và liên kết kiểm chứng.
- [Lịch/HUD và regression](date-ui-validation.json): hai mGBA, pytest,
  VRAM/OAM/tài nguyên, lịch và regression START trên target hiện tại.
- [Tổng quan lịch/HUD](date-ui.png), [tiêu đề trước/sau](calendar-heading.png).
  Ảnh từng fixture nằm trong date-ui/; không lưu bản sao overview trong thư mục con.
- [Glyph a/â/è](hud-a-glyph.png), [e/è](hud-e-glyph.png): raster phóng 4x,
  không phải framebuffer game. [Khoảng cách Hè](date-hud-he-spacing-tight.png)
  giải thích bố cục H–è hiện tại.

## Lô mô tả dụng cụ

[items-batch-validation.json](items-batch-validation.json) gắn 16 pointer, 48 dòng
render, regression tạo game và hash ROM hiện tại. [Ảnh renderer](items-tools-renderer.png)
là chẩn đoán, không phải cửa sổ vật phẩm trong gameplay. Chưa duyệt ngôn ngữ,
bố cục UI hoặc lấy đủ dụng cụ qua luồng chơi thật.

## Bằng chứng theo mốc chức năng

Intro, tạo game và START có báo cáo chuyên biệt và ảnh tương ứng. Chúng
mang hash của mốc lúc tính năng được triển khai; regression bản hiện tại
nằm trong date-ui-validation.json. Không coi tất cả ảnh lịch sử là ảnh của
cùng một binary mới nhất.

- [Tạo game](new-game-setup.png), new-game-*.png: các bước và nhánh xác nhận.
- [Intro](intro-opening.png), intro-*.png: replay mở đầu và hướng dẫn.
- [START](start-menu.png), start-menu/: các trang và xác nhận; chỉ một overview.
- title-*.png, diary-*.png, game-loaded.png: title/cursor và save/load theo mốc.
- vietnamese-font.png và font-metrics.json: atlas/metrics, không phải cảnh game.
  font-spacing-comparison.png và v1-save-loaded-in-v2.png là bằng chứng lịch sử
  cho sửa font/tương thích một save, không bảo đảm mọi save cũ.

Ảnh game lấy từ framebuffer mGBA. Ảnh ghép/phóng dùng nearest-neighbor,
nhãn báo cáo nằm ngoài framebuffer. Chuỗi chẩn đoán font không phải thoại game.
Probe hàm cô lập không được xem là encounter NPC tự nhiên; Popuri vẫn chưa
có encounter tự nhiên trong bằng chứng hiện có.

Các ảnh thử HUD lỗi thời đã bỏ khỏi cây hiện tại; có thể truy hồi bằng Git.
Giữ ảnh cần giải thích thiết kế hiện hành và ảnh fixture được báo cáo tham chiếu.
