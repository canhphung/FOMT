# Tiến độ Việt hóa hiện tại

Cập nhật 2026-10-24. Bộ chuẩn kỹ thuật: `platform-v5-signs`; roadmap ban đầu: `7420c5c`.
Bản vá thử nghiệm, chưa phải Việt hóa 100%.

## Nội dung

| Hạng mục | Có bản dịch nháp / đã trích xuất |
| --- | ---: |
| Tổng catalog | 1.456 / 9.309 |
| Hướng dẫn giường/thùng xuất hàng | 3 / 3 trong lô |
| Biển/thông báo và lựa chọn liên quan | 48 / 48 trong lô |
| Nhãn đồ vật tương tác | 261 / 261 đã xác minh |
| Tên vật phẩm | 347 / 347 |
| Mô tả vật phẩm | 347 / 347 |
| Chuỗi native shop/cửa sổ vật phẩm mới | 26 / 26 |
| Nhãn menu tạm dừng | 7 / 7 |
| Tạo game mới | 24 / 24 |
| Intro/hướng dẫn đầu game | 145 bản ghi |
| Menu con START | 162 bản ghi |
| Lời chào Popuri | 1 bản ghi |
| Thomas — script chuẩn | 34 / 34 |
| Popuri — lô thường ngày mới | 51 / 51 (còn index 1–92) |

1.456 ID không trùng nhau; chưa có ID đánh dấu `reviewed`. 7.853 bản ghi
còn thiếu dịch đều đang chờ phân loại ngữ cảnh. Khoảng 15,6% ID trong catalog
không phải phần trăm lượng từ hay toàn bộ game. Thêm 26 chuỗi UI native,
glossary hiện có 496 thuật ngữ.

Đồ họa theo dõi riêng: Bắt đầu/Tiếp tục, tạo game, lịch và HUD. Font Việt,
con trỏ title, bố cục ngày/giờ và tiêu đề lịch đã được triển khai. Nguồn
trong localization/, chi tiết từng adapter trong các tài liệu hệ thống.

## Kiểm chứng gần nhất

- 144 pytest đạt với ROM USA rev 0 được người dùng cung cấp.
- Bàn dịch local: 12 luồng Chromium đạt ở mốc object-labels-01, sửa/lưu trên bản sao dữ liệu;
  toàn bộ 31 file JSON localization gốc giữ nguyên hash.
- Hai build độc lập giống byte; IPS phát hành áp lại đúng ROM. Khóa 42 file
  nền tảng và 43 ảnh chuẩn, replay trên hai mGBA không lệch pixel.
- mGBA 0.10.5/0.11-dev: boot/title/font, tạo game, START và Diary save/load
  qua cold boot; báo cáo gắn đúng hash target hiện tại.
- 2.580 tổ hợp packed date/time, 300 setter, chín fixture HUD có kiểm VRAM.
- 56 fixture lịch: kiểm OAM/texture/tile cache của tiêu đề; phần body từ
  y=40 khớp bản gốc. Tám chu kỳ mở/đóng trả lại tài nguyên; SRAM không đổi.
- Vật phẩm/UI: 720 bản ghi, 724 pointer fields, 1.351 dòng có guard; 613 cửa sổ Ba lô mỗi backend qua RAM fixture, SRAM không đổi.
- NPC: 85 câu mới, 124 WAIT native, 266 dòng có guard, 864 ca dò nhánh Thomas; fixture UI, chưa encounter tự nhiên.
- Đồ vật: 261 nhãn/68 tên, 261 WAIT và bitmap cache khớp pixel mỗi backend; hai bàn bằng input tự nhiên; 260 CODE/JUMP và 184 chuỗi ngoài nhãn giữ nguyên.
- Kiểm round trip IPS và hash bản build. Số ngày trong lịch và HUD giữ nguyên.

[Bộ chuẩn nền tảng](PLATFORM_BASELINE.md),
[báo cáo nền tảng](evidence/platform-validation.json), [lịch/HUD](evidence/date-ui-validation.json),
[đồ vật](evidence/object-labels-validation.json), [NPC mốc trước](evidence/npc-daily-validation.json), [vật phẩm/UI mốc trước](evidence/items-complete-validation.json), [tổng hợp lịch sử](evidence/validation.json), [manifest bản vá](../patches/manifest.json).
Báo cáo lịch/HUD, intro/tạo game/START chuyên biệt mang hash của các mốc trước; giữ
làm bằng chứng phạm vi từng mốc, không coi là chạy lại toàn bộ trên target mới.

## Còn thiếu

- Phân loại ngữ cảnh/người nói, phần lớn hội thoại NPC và sự kiện.
- Duyệt nghĩa/bố cục 347 mô tả và 347 tên đã có nháp; kiểm giao dịch cửa hàng tự nhiên.
- Kiểm kê UI còn thiếu, TV/sách/hướng dẫn và đồ họa chữ ngoài catalog.
- Duyệt nghĩa/xưng hô/thuật ngữ; chưa encounter Popuri tự nhiên trong bằng chứng hiện có.
- Chưa chơi xuyên mùa/toàn bộ nhánh, chưa kiểm mọi save cũ hoặc GBA thật.
- Mốc năm 200 đã xác minh là giới hạn hiển thị lịch; chưa xác minh hành vi
  gameplay khi vượt mốc đó.

Đã có glossary/hồ sơ theo cảnh, hàng đợi và lô 16 mô tả dụng cụ.
Ưu tiên tiếp theo: trace cổng mùa/quan hệ Popuri, encounter Thomas/Popuri tự nhiên; tiếp tục duyệt lô vật phẩm và giao dịch cửa hàng. Xem [ROADMAP_VI.md](ROADMAP_VI.md).

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

## Ổn định nền tảng platform-v1 — 2026-10-23

Chốt ba hệ font hiện hành, không sửa bitmap/palette/tọa độ hoặc bản dịch.
Manifest mới khóa 28 file nguồn và 43 framebuffer 240×160. Bảy ảnh khác
mốc lịch sử (gồm Hạ → Hè) được cập nhật cho bộ chuẩn, thêm một ảnh hội
thoại Thomas. 35 ảnh đã khớp dùng lại tại chỗ; ảnh mốc cũ giữ làm lịch sử.

Thêm `platform_check.py`, `make platform-check` và `make platform-emulator`:
pytest → hai build độc lập → kiểm manifest/IPS round trip → năm suite trên
mỗi backend → so RGBA với 43 ảnh chuẩn. Lỗi nguồn hoặc pixel làm lệnh thất
bại; không tự cập nhật chuẩn. Có ảnh diff và báo cáo trạng thái lần chạy mới.
Bốn test mới kiểm thay đổi pixel/alpha, kích thước, khóa nguồn/ảnh và việc
lần chạy lỗi không giữ báo cáo xanh cũ. Tổng 117 pytest đạt, không skip.

Hai build giữ nguyên hash ROM/IPS phát hành. Cả 0.10.5 và 0.11-dev chạy đủ
font/title/intro/save-load, tạo game, START, lịch/HUD và renderer dụng cụ;
43/43 ảnh mỗi backend khớp chuẩn, 0 pixel khác. Bằng chứng gắn hash ROM và
manifest bộ chuẩn trong [platform-validation.json](evidence/platform-validation.json).

Duyệt thẩm mỹ toàn gallery vẫn pending; 722 bản dịch giữ trạng thái nháp,
0 reviewed. Chưa kiểm GBA thật, chơi xuyên mùa, mọi cửa sổ vật phẩm hoặc
encounter Popuri. Không suy số năm gameplay từ fixture lịch. Các công việc
này vẫn mở trong QA; xem [quy ước và ảnh chuẩn](PLATFORM_BASELINE.md).

## Bàn dịch Anh–Việt — 2026-10-23

Thêm server Python và giao diện local: bảng Anh–Việt phân trang, tìm không
phân biệt dấu/hoa-thường, lọc hàng đợi/ngữ cảnh/người nói/lô, tra glossary và
bảy hồ sơ theo đúng source ID. Hiển thị địa chỉ, bằng chứng ngữ cảnh và QA.

Bản dịch được kiểm bằng encoder/check_translation hiện có ngay khi nhập:
token đủ và đúng thứ tự, glyph hỗ trợ, độ rộng, giới hạn byte, tên riêng.
Chặn lưu rỗng/lỗi hoặc ngữ cảnh chưa xác minh; Flower vẫn chỉ đọc. Lưu vào
file VI đang sở hữu, bản ghi vật phẩm mới vào items.json; khóa ghi, kiểm
revision, backup và thay file nguyên tử. Không sửa source/pointer/QA; bản
sửa là translated, QA hash cũ chuyển stale. CSV xuất theo bộ lọc, chưa import.

Chín test mới về validator, tìm/lọc, provenance, backup, stale QA, xung đột,
ghi đồng thời hai ID, CSV và HTTP đạt. Tổng 126 pytest đạt, không skip;
platform-check build hai lần và áp IPS đúng target cũ. Không sửa 28 file nền
tảng đã khóa, font hoặc bố cục; không cần chạy lại mGBA cho binary không đổi.

Chromium chạy 11 luồng thật trên bản sao dữ liệu, kiểm cả viewport 390px;
0 exception, 22 JSON nguồn giữ hash. Ảnh công cụ và lỗi token cố ý nằm ở
[workbench-validation.json](evidence/workbench-validation.json), không phải
ảnh game. Dữ liệu thật vẫn 722 nháp, 0 reviewed; hàng đợi 310 cần dịch,
722 QA, 8.251 blocked. Chưa có editor glossary/hồ sơ/registry QA, import CSV
hoặc tự build/playtest trong giao diện. [Hướng dẫn](TRANSLATION_WORKBENCH.md).

## Phiên vật phẩm và UI — 2026-10-23

Thêm 310 mô tả còn thiếu (326 là số trước lô 16 dụng cụ), xác minh Bột mì
bằng nguồn trong ROM, chỉnh tên mì kiều mạch tempura và vé oẳn tù tì.
Thêm 17 thông báo shop và 9 nhãn/đơn vị cửa sổ. Giữ nguyên token và dữ liệu
phi văn bản; sửa scanner NUL của title dụng cụ, thêm giới hạn 95/79 byte.
Chi tiết nguồn, lỗi English và phạm vi QA tại [ITEM_LOCALIZATION.md](ITEM_LOCALIZATION.md).
Không nâng trạng thái ngôn ngữ hoặc chơi thử tự nhiên dựa trên RAM fixture.

## Hội thoại thường ngày — npc-daily-01, 2026-10-23

Thêm 34 câu của Thomas (đủ script chuẩn 1017) và 51 câu Popuri (993.093–143).
Đã nối actor constructor → script → native ShowText, mở rộng source ID trong
hồ sơ bác/cháu và mình/bạn; giữ ngoài phạm vi thoại vợ/con chưa trace.
Dò 864 ca theo CODE gốc của Thomas: mức thân thiết, lượt nói, giờ, weather;
không gán bốn mùa cho NPC chưa có bằng chứng. Wiki FoMT vẫn trả HTTP 402.
Toàn bộ bản dịch là nháp; native UI fixture không thay encounter tự nhiên.
Xem [nguồn và độ phủ](NPC_DAILY_LOCALIZATION.md), [báo cáo](evidence/npc-daily-validation.json).

## Tinh chỉnh Thomas — thomas-refinement-01

Áp dụng bốn đề xuất 1017.007/014/018/023 đã được người dùng chọn: sắc thái
giật mình, thống nhất thị trấn, giữ always và rõ nghĩa quản lý thị trấn.
Giữ nguyên English/control stream, xưng bác/cháu và số nháp 1.144.
Tài liệu tham khảo và bản rà soát riêng nằm trong knowledge/ được Git ignore,
không phát hành cùng bản vá. Không đánh dấu toàn bộ Thomas đã duyệt.

[Báo cáo tinh chỉnh](evidence/thomas-refinement-validation.json) có ảnh và
kiểm năm WAIT/12 dòng riêng cho bốn câu. Gate đầy đủ kiểm lại hai build/IPS,
134 pytest, tám suite mỗi mGBA và 43 ảnh chuẩn không đổi. Bàn dịch không
chạy lại trong lượt chỉ thay văn bản này; bằng chứng browser cũ giữ hash/mốc cũ.

## Nhãn đồ vật tương tác — object-labels-01, 2026-10-24

Thêm 261 nhãn tại 260 script, 68 tên English và 66 mục glossary mới.
Xác minh literal, CODE và OnCall33/34/35 bằng contract nguồn tường minh;
không thay từ hàng loạt hoặc dịch lẫn thoại Cliff, giường/vợ, cuộc thi,
khám bệnh và Ngọc Sự thật nằm trong cùng script. 184 chuỗi ngoài nhãn giữ byte.

Table trong ảnh người dùng là 351.001; đã tái hiện từ save bằng input
thường cùng bàn tròn 355.000. Các nhãn còn lại kiểm fixture UI native,
con trỏ WAIT và pixel glyph của ba hàng cache. Không coi là đã đi mọi map.
[Phạm vi và ảnh](INTERACTIVE_OBJECTS.md), [bằng chứng](evidence/object-labels-validation.json).

Font/bố cục không đổi, 43 ảnh chuẩn giữ nguyên. Còn kiểm tự nhiên các nhà
khác và kiểm kê menu/hướng dẫn dài/biển hiệu ngoài nhãn; toàn bộ vẫn là nháp.
Knowledge giữ cục bộ, không đưa tài liệu hoặc ZIP lên GitHub.

## Phiên interaction-hints-01 — 2026-10-24

Thêm hai bản hướng dẫn giường và một bản hướng dẫn thùng xuất hàng, đúng
chuỗi trong ảnh người dùng. Giữ control code, CODE/JUMP, lựa chọn ngủ và
font. Kiểm native UI fixture cả bốn WAIT, 10 dòng renderer và bitmap chữ
trước/sau cuộn trên hai mGBA. Chưa có playtest tương tác tự nhiên cho ba
chuỗi; duyệt ngôn ngữ/bố cục thủ công còn pending. Không dịch nhãn chứa
RAW:81A8 khi chưa rõ chức năng. Chi tiết: [INTERACTION_HINTS.md](INTERACTION_HINTS.md).

## Phiên signs-01 — 2026-10-24

Thêm 48 mục ở 31 script: 45 nội dung biển và 3 lựa chọn ném đĩa. Giữ đầy đủ
13 thông báo lễ hội, hai biến thể thư viện và lịch mở cửa đúng từng source.
Xác minh 10 RAW glyph, giữ mũi tên; chỉ hai biển được giảm đệm trống theo
contract. Kiểm native fixture 45 nội dung/73 WAIT và 179 dòng renderer;
12 luồng Chromium trên bản sao, không sửa 37 JSON nguồn. Tổng nháp 1.456
ID, glossary 496. Chưa có QA ngôn ngữ/bố cục thủ công hoặc mọi tương tác
tự nhiên/map. Chi tiết: [SIGN_LOCALIZATION.md](SIGN_LOCALIZATION.md).
