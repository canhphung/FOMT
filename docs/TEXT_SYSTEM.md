# Hệ thống văn bản FOMT USA

## Phạm vi và nguồn

Phân tích trên ROM do người dùng cung cấp, 8,388,608 byte, game code `A4NE`,
revision 0. SHA-1 bắt buộc:
`a2fc3574f0a65a4fcf7682fb274b9d7eebdef963`.
SHA-256: `ca6cebe7211b6f2693af210709f76222204bf9f7621dec08b30ca268117460dd`.

Nguồn chính: [StanHash/fomt](https://github.com/StanHash/fomt), commit
`b8471ae065744869f64283473ed68372f82321c9`. Toàn bộ 190 file tracked được đọc
để lập `reference_inventory.json` với kích thước/hash; phân tích ngữ nghĩa tập
trung vào VM, dữ liệu vật phẩm, font và các hàm gọi render. Đây không phải tuyên
bố đã hiểu mọi hàm của game. Checkout tham khảo nằm ngoài repo sản phẩm.

Tài liệu phụ: [StanHash/FOMT-DOC](https://github.com/StanHash/FOMT-DOC).
Nhiều địa chỉ trong đó ghi **MFOMTU**, thuộc *More Friends of Mineral Town*.
Không được sao chép các địa chỉ đó sang bản FOMT. Địa chỉ trong tài liệu này đã
đối chiếu với source chính và ROM đúng hash. `rea` chưa cần dùng.

## Địa chỉ và byte order

GBA bus address = `0x08000000 + file_offset`. Word/pointer dùng little endian.
Ví dụ bus `0x080F89D4` tương ứng file offset `0x0F89D4`. Công cụ kiểm tra miền
pointer, không cắt bit để biến một pointer sai thành địa chỉ hợp lệ.

## Bảng vật phẩm

Chứng cứ: `tools/scripts/dump_item_tables.py`, `data/item/*.def`,
`src/item.cc` (`Tool/Food/Article::GetName/GetDesc`).

| Nhóm | File offset bảng | Số phần tử | Stride | Name pointer | Description pointer |
| --- | --- | ---: | ---: | ---: | ---: |
| tool | `0x0EAB0C` | 81 | 12 | +0 | +8 |
| food | `0x0EDCD8` | 171 | 16 | +0 | +12 |
| article | `0x0EFED4` | 95 | 12 | +0 | +8 |

Tên và mô tả là C-string kết thúc bằng byte `00`. Các trường icon, giá,
stamina, fatigue và thuộc tính vật phẩm không bị sửa. Bảng product định tuyến
sang food/article, không phải một bản sao độc lập của tất cả tên.

Tổng trích xuất nhóm này: 347 tên + 347 mô tả. Không sửa lỗi gốc ngoài phạm vi:
ví dụ hai nhãn len đều hiện `Wool (P)`; bản dịch giữ nhãn P theo văn bản nguồn.
Nhãn `Flower` của food 66 còn mơ hồ và chưa dịch, không tự sửa thành Flour.

## Menu tạm dừng

7 pointer liên tiếp tại file `0x0F1A34`, theo thứ tự Diary, Rucksack, World Map,
Farm Map, Earnings, Memo, Tutorial. Trước khi xuất, extractor kiểm tra đúng cả
7 nhãn nguồn. Chứng cứ: `asm/code_0803A8A4.s`, literal `0x0803C0C4` trỏ
đến `gUnk_080F1A34`, truy cập `table[index]`.

Ngân sách dịch thử: 12 ô × 8 pixel. Cả 7 nhãn đã được chọn bằng nút Right trong
game và xem ảnh chụp. Các chữ trong màn hình Diary, hướng dẫn, tên NPC và logo
title chưa được tích hợp vào adapter static text; title có thành phần đồ họa.

## Script hội thoại/sự kiện

Chứng cứ chính: `src/script_engine.cc` và `include/script_engine.hh`:
`AScriptEngine::Load`, `GetString`, `ScriptEngine::LoadById`.

Bảng pointer tại file `0x0F89D4`, dài `0x14C4` byte = 1,329 phần tử. Phần tử 0
null; 1,328 phần tử còn lại trỏ đến container `RIFF`/`SCR `. Chúng chứa tổng
8,368 chuỗi. Chuỗi byte `RIFF` tại `0x03EF48` là literal trong code, không phải
container SCR — scanner chỉ tìm magic sẽ đếm sai.

```
container +00  "RIFF"
          +04  u32 total_container_bytes
          +08  "SCR "
          +0C  các chunk: tag[4], u32 payload_bytes, payload

CODE payload: u32 bytecode_bytes, bytecode[...]
JUMP payload: bảng nhảy VM (tùy script)
STR  payload: u32 count, u32 relative_offsets[count], string_pool
```

**Khác RIFF chuẩn**: trường length của game là tổng kích thước container, không
phải tổng trừ 8. Không thêm padding lẻ/chẵn giữa các chunk. Container tiếp theo
thường được căn 4 byte bên ngoài container. Offset của từng string tính từ đầu
`string_pool`, không phải đầu ROM/container/chunk. String kết thúc bằng `00`.
Giữ nguyên số lượng/thứ tự ID; VM gọi string theo index.

Importer giữ nguyên byte `CODE` và `JUMP`, tái tạo `STR ` và trường length,
đặt container mới ngoài ROM gốc rồi sửa đúng pointer trong bảng script. Nó kiểm
tra lại toàn bộ string và so sánh bytecode/bảng nhảy sau rebuild. Không patch
các word có giá trị giống pointer ở nơi chưa rõ chức năng.

## Bảng mã và control stream

Renderer tương thích ASCII/Shift-JIS với một số glyph một byte tùy chỉnh của
bản USA. Không phải Unicode/UTF-8. JSON dùng token để đảm bảo round trip:

| Byte | Token | Ý nghĩa xác minh |
| --- | --- | --- |
| `00` | không xuất như text | kết thúc C-string |
| `05` | `{WAIT}` | chờ nút tiến hội thoại |
| `0A` | `{LF}` | chuyển dòng, không tự đặt x=0 |
| `0C` | `{PAGE}` | xóa/chuyển trang hộp thoại |
| `0D` | `{CR}` | đặt x về đầu dòng |
| `FF xx` | `{VAR:XX}` | yêu cầu bộ mở rộng biến; giữ nguyên cả cặp |
| byte khác ngoài ASCII | `{RAW:...}` | giữ nguyên, chưa gán nghĩa tùy tiện |

`{VAR:21}` hiện tên người chơi trong đoạn Thomas, đã quan sát bằng tên A.
Chưa lập đầy đủ ý nghĩa mọi variable ID. `{RAW:8140}` thường là khoảng trắng
rộng theo CP932 nhưng vẫn giữ nguyên byte thay vì thay thành dấu cách ASCII.
Không diễn giải byte `FF` thành ký tự Private Use của Python CP932.

Đã kiểm tra `encode(decode(bytes)) == bytes` cho toàn bộ 9,069 bản ghi.
Importer yêu cầu token và thứ tự token giống hoàn toàn nguồn. Phần tử `RAW`
không được xóa/đổi để làm validator qua. Văn bản thường được chuẩn hóa NFC.

## Font, giới hạn và import

Xem [VIETNAMESE_FONT.md](VIETNAMESE_FONT.md). Hộp thoại có ba dòng hiển thị và
ngang 28 ô; source `func_0804EFAC` dùng phép kiểm tra x+width với `0x1B`,
cuộn dòng theo display manager. Công cụ đo chiều ngang, tách CR/LF đúng nghĩa,
và dự phòng 12 ô cho mỗi biến chưa biết chiều dài. Ngân sách tên vật phẩm 20 ô
là giới hạn dịch thử bảo thủ, **chưa chứng minh mọi cửa sổ đều có đủ 20 ô**.
Chưa có kiểm tra tự động đầy đủ chiều dọc, mọi expansion, buffer copy theo byte
hoặc mọi biến thể cửa sổ. Dấu/chữ dùng 2 byte nhưng rộng 1 ô.
Font v2 dùng mask 8×16, giữ outline/bearing gốc và căn ASCII/Việt cùng baseline;
cache 4bpp 229 glyph dùng đúng staging 128 byte của engine, không đổi advance 8px.

ROM đầu ra 16 MiB. Mọi allocation mới bắt đầu từ offset `0x800000`, căn 4 byte;
không tận dụng vùng FF bên trong ROM gốc bằng suy đoán. Chỉ sửa 8 byte prologue
renderer và các slot pointer đã xác minh. Header và SRAM routine giữ nguyên.
Mỗi build có audit report liệt kê các write, allocation, layout và hash.

## Phân loại còn thiếu

9,069 là số chuỗi trong **các cấu trúc đã hỗ trợ**, không phải khẳng định đã tìm
hết mọi chữ game có thể hiển thị. Script còn chứa TV, sách, sự kiện, menu chọn,
lời NPC và hướng dẫn; phần lớn chưa nối được đến speaker/call-site, nên giữ
`script_string_unclassified`. Chưa dịch tự động nhóm này. Tên NPC, UI static,
name-entry, đồ họa chữ và lịch/đồng hồ cần adapter và kiểm thử riêng. Không có
địa chỉ hay hội thoại tự đặt nào được đưa vào catalog dưới tên nội dung gốc.
