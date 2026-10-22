# Font và bảng mã tiếng Việt

## Kết quả reverse engineering trên đúng bản USA

| Thành phần | GBA bus address | Nguồn chính |
| --- | --- | --- |
| Hàm chọn/vẽ glyph | `0x080D0D28` | `asm/code_809E804.s` |
| Sheet glyph hẹp | `0x084F90CC` | `asm/data/data_0813B288.s` |
| Lookup một byte, 256 số s16 | `0x084FA7A0` | cùng file |
| Sheet glyph rộng | `0x084FA9A0` | cùng file |
| Lookup JIS | `0x08523290` | cùng file |
| Giải glyph hẹp tại IWRAM | `0x0300085C`, **ARM** | copy từ ROM lúc boot |
| Giải glyph rộng tại IWRAM | `0x03000714`, **ARM** | copy từ ROM lúc boot |
| Vẽ chuỗi vào tile buffer | `0x0804E8F0`, Thumb | `asm/code_0803EE94.s` |

Glyph nguồn là 1bpp, MSB ở trái, 12 hàng; glyph hẹp 12 byte (8 pixel), glyph
rộng 24 byte (16 pixel). Routine gốc thêm bóng và chuyển sang 4bpp cho GBA.
**Buffer tạm thực tế là 128 byte / bốn tile 16×16 ngay cả khi advance=8 px**;
điều này đã đo bằng mGBA và canary trước/sau buffer. Foreground palette index 1,
shadow index 2, foreground có offset x=1 và y=2 trong staging buffer.
Không lấy kích thước staging buffer từ suy đoán “một glyph rộng 8 tức 64 byte”.

## FOMT-VI-EB-v1

File JSON vẫn là UTF-8 NFC; khi build, 134 chữ Việt có dấu/Đđ được ánh xạ
hai byte từ `EB 40` đến `EB C5`. Danh sách sắp xếp theo Unicode trong
`localization/font/encoding.json`. ASCII giữ nguyên byte/glyph.

Byte EB riêng lẻ có lookup -1, do đó renderer gốc trả 0 và wrapper gom byte
kế tiếp thành code `0xEBxx`. Bộ đổi SJIS cũ chỉ chấp nhận lead đến EA; hook
chặn dải EB40–EBC5 trước bước đó và trả advance=1. Đây là **mã tùy chỉnh**, không
phải SJIS tiêu chuẩn; có cả trail 7F. Toàn bộ 134 code đã qua đường gom hai byte
của hàm vẽ chuỗi thật, bao gồm trường hợp 7F. Không dùng FF vì dành cho biến.

Hook thay đúng 8 byte đầu `0x080D0D28`, kiểm tra prologue gốc trước khi patch:
`70 B5 04 1C 0A 1C 00 26`. Với ký tự ngoài dải Việt, hook phát lại 4 lệnh đã
thay rồi nhảy đến `0x080D0D30` ở Thumb state. Với ký tự Việt, đọc bitmap mới
và gọi `0x0300085C` ở **ARM state** bằng BX; không dùng BLX/Thumb-2 trên ARM7TDMI.
Đã so sánh nguyên byte kết quả render 95 ký tự ASCII với ROM gốc.

## Pixel art và bộ nhớ

`tools/vietnamese_font.py` tạo glyph 8×12. Thân chữ thường giữ nét font gốc;
chữ hoa có mẫu pixel gọn riêng, hoa O rộng hơn để phân biệt với o. Bốn hàng
trên dành cho dấu thanh và mũ/móc; hàng cuối dành cho dấu nặng. y có đuôi thu
gọn. Đã kiểm tra 134 bitmap khác nhau; không gộp Ô/ô hoặc Ớ/ớ.

Bitmap xuất trong `encoding.json` là tài liệu tham chiếu được sinh lại từ code,
không phải đầu vào chỉnh sửa của importer hiện tại. Chỉnh mẫu trong Python nếu
muốn sửa nét, rồi build/test/xuất lại bảng. Atlas trong `docs/evidence` minh họa
bitmap; ảnh trong game là chứng cứ cho renderer thật.

Thêm 134×12 = **1,608 byte ROM**, tối đa 128 byte reservation cho hook. Không
cấp thêm VRAM/font cache; dùng staging buffer và đường upload gốc. Vẫn rộng
1 tile, không thêm framebuffer riêng trong game. Điều này không thay thế việc
chơi thử mọi UI hoặc đo thời gian của toàn bộ event: đoạn mở đầu/menu đã qua,
còn nhiều biến thể cửa sổ chưa kiểm tra.

Không thay font nhập tên người chơi: bàn phím name-entry, giới hạn byte trong
save và tên tự nhập có dấu là một hạng mục riêng. Bản thử cho phép tên ASCII
như game gốc; không khẳng định nhập tên tiếng Việt đã hoạt động.

## Kiểm thử đã triển khai

- Mỗi chữ Việt được gọi qua hàm ROM bằng CPU mGBA thực, so foreground pixel với
  bitmap và kiểm tra canary 16 byte hai phía buffer 128 byte.
- Kiểm tra width-only với buffer null cho cả 134 chữ và lead EB riêng lẻ.
- Vẽ cả bộ 134 code qua hàm gom byte/vẽ chuỗi thật; không mất ký tự.
- 7 nhãn menu và 15 tên nông sản lấy từ pointer trong ROM đã patch, so pixel với
  từng glyph, có canary cho buffer đích.
- Chạy mới, xem hội thoại Thomas và cả 7 menu bằng nút game bình thường.
- Duyệt ảnh sau mỗi thay đổi font; chưa kiểm tra phần cứng GBA thật.

Font hiện là bản pixel thử nghiệm; vẫn cần duyệt thẩm mỹ, nhất là chữ hoa/dấu kép
trên LCD thật. Không có fallback bỏ dấu hoặc encode UTF-8 trực tiếp vào ROM.
