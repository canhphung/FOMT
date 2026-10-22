# Tiến độ Việt hóa

**Hiện tại:** font v2 sửa lệch baseline/bearing, 47 test đạt; bản dịch vẫn 385 ID.
Mục đầu lưu lịch sử bản thử v1; mục cuối ghi phiên sửa font và bằng chứng mới.

## Phiên 2026-10-22 — nền tảng và bản thử đầu tiên

Đã chuyển repo từ README trống thành pipeline localization có kiểm tra ROM,
trích xuất lossless, bảng mã/font Việt, chèn con trỏ/container và tạo IPS.
**Chưa hoàn thành mục tiêu Việt hóa 100%.** Không có chuỗi nào được đánh dấu
`reviewed`; toàn bộ bản dịch hiện là nháp.

### Dữ liệu có nguồn gốc xác minh

| Nhóm | Trích xuất | Có bản dịch nháp | Chưa dịch |
| --- | ---: | ---: | ---: |
| Tên vật phẩm | 347 | 346 | 1 |
| Mô tả vật phẩm | 347 | 21 | 326 |
| Nhãn menu tạm dừng | 7 | 7 | 0 |
| Chuỗi SCR | 8.368 | 11 | 8.357 |
| **Tổng catalog đã hỗ trợ** | **9.069** | **385** | **8.684** |

Khoảng 4,25% số bản ghi trong catalog hiện có bản dịch nháp; đây không phải
phần trăm Việt hóa toàn bộ nội dung game. Một số tên riêng được giữ nguyên.
349 payload khác nội dung nguồn; 36 bản ghi giữ nguyên chữ hiển thị, chủ yếu tên
riêng/tên định danh như Album. Không tính các tên giữ nguyên là câu đã đổi tiếng.
Không đếm câu giả lập trong test là văn bản game.

`localization/en/catalog.json` đã được sinh đầy đủ trong workspace và có thể
tái tạo từ ROM đúng hash, nhưng không track Git. Các subset EN/VI và glossary
có trong repo. `pilot.json` có 48 ID; `items.json` thêm 337 ID, không trùng.

### Kiểm chứng v1 (lịch sử)

- ROM nguồn khớp SHA-1 decomp tham khảo; 190 file source được lập inventory.
- 9.069 bản ghi round trip đúng byte; không sửa script CODE/JUMP khi rebuild.
- 42 kiểm thử pytest qua, không skip trong phiên này vì đã cung cấp `FOMT_ROM`.
- Build lặp lại cùng input tạo cùng hash; áp dụng IPS dựng lại đúng ROM đích.
- ROM 16 MiB boot trong mGBA, tạo game mới, qua các cảnh mở đầu đến nhà ngày 2.
- Đã xem hội thoại Thomas tiếng Việt qua luồng game bình thường và ảnh cả
  7 nhãn menu: Nhật ký, Ba lô, Bản đồ vùng, Bản đồ trại, Thu nhập, Ghi chú, Hướng dẫn.
- 134 glyph Việt khác nhau, đều qua CPU/render mGBA, đúng pixel, advance 1,
  không đụng canary. Cả 134 code qua đường gom byte/vẽ chuỗi, gồm EB7F.
- 95 glyph ASCII cho kết quả byte giống ROM gốc. 7 nhãn menu và 15 tên nông sản
  lấy từ pointer ROM mới qua renderer chuỗi và kiểm tra buffer đích.
- Ghi save thật bằng menu Diary, xuất SRAM 32 KiB, nạp vào core mới, boot lại,
  game nhận save và load về nhà ngày 2. Payload SRAM sau boot/load giữ nguyên.
- Không có log mức error/fatal trong lượt mGBA cuối.

Chứng cứ hiện tại trong `docs/evidence/` đã cập nhật sang v2; hash/kích thước ở
`patches/manifest.json`. Báo cáo ghi chính xác hash target đã chạy test.
`make compare` của decomp gốc chưa chạy: không cần matching build/agbcc cho
pipeline patch trực tiếp này. Không thay đổi code gameplay để làm test qua.

### Vấn đề phát hiện và xử lý trong phiên

- Tài liệu phụ dùng địa chỉ MFOMT: đã đối chiếu lại địa chỉ bản FOMT USA.
- RIFF của game dùng total length và không padding giữa chunk: parser theo
  loader thật, không theo thư viện RIFF phổ thông.
- FF là expansion prefix, không phải ký tự CP932 PUA: codec giữ cặp byte.
- Routine giải glyph IWRAM chạy ARM, không phải Thumb: hook dùng đúng state.
- Glyph advance 8 px vẫn dùng staging 128 byte: canary dựa trên đo thực tế.
- Bộ font thử đầu có O/o trùng bitmap: sửa mẫu O hoa, thêm kiểm thử đủ 134
  bitmap khác nhau để không lặp lại lỗi này.
- Một câu có tên người chơi vượt ngân sách khi dự phòng biến: đã viết lại
  câu tiếng Việt, không bỏ token hoặc nới validator để che lỗi.
- Savestate của emulator không chứa SRAM như bài test cần: kiểm thử save/load
  cuối dùng boot khởi tạo đầy đủ và SRAM riêng, không dựa vào EWRAM savestate.

### Phần chưa giải quyết

1. Phân loại speaker/call-site cho 8.357 chuỗi SCR chưa dịch: hội thoại NPC,
   sự kiện, TV, sách, hướng dẫn và lựa chọn đang lẫn trong cùng loại container.
   Không dịch những chuỗi chưa rõ chức năng.
2. 326 mô tả vật phẩm; một nhãn food `Flower` cần xác minh trước khi dịch.
3. UI static ngoài menu tạm dừng: Diary/options, shop, tên NPC, hướng dẫn,
   name-entry, đồ họa chữ title/lịch/đồng hồ chưa có adapter đầy đủ.
4. Duyệt xưng hô/thuật ngữ: hiện Popuri dùng mình/bạn, Thomas dùng bác/cháu ở
   đoạn đã xác minh. Chưa áp một bộ xưng hô suy đoán cho mọi nhân vật.
5. Lời chào Popuri đã rebuild/kiểm tra token, chưa gặp Popuri bằng luồng chơi
   tự nhiên trong lượt replay này. Không xem đó là bằng chứng encounter đã qua.
6. Chưa kiểm tra mọi cửa sổ vật phẩm, mọi byte-buffer copy, số dòng, cảnh/sự kiện,
   mùa/lễ hội/hôn nhân, hàng trăm giờ gameplay hoặc save cũ của người chơi.
7. Chưa kiểm tra flashcart/GBA thật, thẩm mỹ font trên LCD, nhập tên có dấu.

### Bước tiếp theo cho phiên sau

- Tiếp tục từ catalog đúng SHA-1, không quét/patch ASCII hàng loạt.
- Truy vết caller của GetString/VM text functions để gắn context và speaker,
  ưu tiên NPC thường gặp, cửa hàng và hướng dẫn đầu game.
- Hoàn thiện mô tả vật phẩm và adapter Diary; dùng các ID đã có, giữ nguyên
  control stream hoặc nghiên cứu validator mới trước khi đổi cách chia trang.
- Thêm save/replay theo từng milestone để kiểm tra Popuri, hộp thoại dài,
  cửa hàng, thùng xuất hàng, chuyển cảnh và save/load dài hạn.
- Chỉ nâng trạng thái sang `reviewed` sau khi duyệt ngôn ngữ và ảnh đúng context;
  cập nhật bảng đếm, test và manifest sau mỗi phiên.


## Phiên 2026-10-22 — sửa baseline/bearing font v2

Người dùng phản hồi chữ có dấu không đều và gửi ZIP font OTF tham khảo. Đã đo
bitmap thực tế và xác nhận lỗi v1: chữ thường lệch xuống 1px, chữ hoa bị co từ
10px còn 7px, O hoa rộng/lệch ngang, d/y bị sửa outline và ị mất chấm trên.
Độ rộng advance của engine vẫn luôn là 8px; kiểm thử v1 chưa kiểm tra hình học
thân chữ nên không phát hiện được lỗi này.

Đã thay bằng mask 8×16 dùng nguyên thân/bearing ROM gốc. ASCII và Việt dùng cùng
baseline hàng 13, không trim/scale/căn giữa riêng từng glyph, giữ advance 8px.
Dấu được thêm ở hàng trống; d giữ ascender, y giữ descender, ị giữ chấm trên.
Cache 4bpp sinh trước ở ROM gồm 229 glyph × 128 byte; dispatcher copy vào đúng
staging buffer cũ, không tăng VRAM hoặc sửa kích thước cửa sổ/bytecode gameplay.
Font OTF có 197 ký tự, chỉ 32/134 chữ Việt, được dùng làm tham chiếu; không đóng
gói OTF và không dùng metric 6px của OTF để đổi advance GBA 8px.

Kiểm thử hiện tại: **47 pytest đạt, không skip**, gồm hồi quy baseline/bearing,
outline hoa/thường, dấu trên/dưới i, ascender Đ/đ và cache 4bpp. mGBA xác minh
95 ASCII theo phép dịch đồng nhất 2px từ raster ROM gốc, 134 glyph/chuỗi Việt,
10 glyph fallback legacy/SJIS, 7 menu, 15 tên nông sản và 9 chuỗi ASCII/trộn dấu.
Lượt replay qua mở đầu, chọn menu, ghi Diary, boot core mới và load lại SRAM
vẫn đạt, không log error/fatal. 385 ID dịch không đổi; codec EB40–EBC5 không đổi.
Đã chạy lại cùng bộ probe trên mGBA **0.10.5** như người dùng đang dùng và 0.11-dev.
Adapter được sửa để đọc define CMake thực tế của từng version, tránh lệch ABI
ở hàm xuất SRAM khi tên macro debugger khác nhau; không thay code save của game.

`docs/evidence/font-spacing-comparison.png` là so sánh output renderer v1/v2
trên chuỗi chẩn đoán; ảnh Thomas/menu/save cũng được chụp lại từ ROM v2.
`font-metrics.json` lưu phép đo và metadata OTF, manifest trỏ đúng hash ROM/bản vá
mới. Bản vá mới phải áp lên ROM USA gốc, không chồng lên ROM đã Việt hóa v1.

Giới hạn còn lại: ô chữ vẫn cố định 8px (chưa có kerning/VWF); chưa chơi thử
mọi UI và phần cứng GBA thật. Native glyph ngoài ASCII/Việt, lịch, đồng hồ và
đồ họa title vẫn theo hệ gốc. Các hạng mục dịch chưa giải quyết ở trên vẫn giữ
nguyên, không tăng số chuỗi dịch để tính việc sửa font.
