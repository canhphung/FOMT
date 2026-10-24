# Quy trình dịch theo ngữ cảnh và hàng đợi QA

Cập nhật object-labels-01: [đồ vật](INTERACTIVE_OBJECTS.md) thêm 261 nhãn
đã xác minh, glossary hiện 471 thuật ngữ; chỉ hai bàn có playtest tự nhiên.
Các số trong phần baseline bên dưới là lịch sử.

Cập nhật npc-daily-01: [NPC](NPC_DAILY_LOCALIZATION.md) có 85 nháp mới,
glossary 405 thuật ngữ. [Vật phẩm](ITEM_LOCALIZATION.md) đã đủ 347 mô tả;
Flower đã xác minh là Bột mì. Các số ở phần baseline/lô đầu dưới đây là
lịch sử; trạng thái hiện tại ở [tiến độ](TRANSLATION_PROGRESS.md).

Baseline phiên 2026-10-23: glossary 389 thuật ngữ; bảy hồ sơ người nói có
phạm vi; lô tools-01 gồm 16 mô tả liềm/cuốc. Mọi bản dịch vẫn là nháp.

[Bàn dịch Anh–Việt](TRANSLATION_WORKBENCH.md) bổ sung giao diện local cho
hàng đợi này: tìm/lọc, tra glossary/xưng hô, sửa bản dịch và kiểm token/độ dài.
Chạy `.venv/bin/python tools/translation_workbench.py`; lưu nháp ghi vào sáu
file VI hiện có, có backup và kiểm xung đột, không tự sửa registry QA.

## Thuật ngữ và xưng hô

`localization/glossary.json` giữ tên riêng, cấp S/M/L/G/P/X và thuật ngữ.
Mùa thứ hai thống nhất **Hè**, viết **hè** trong câu; menu sinh nhật và ba
chuỗi START đã sửa cách gọi Hạ cũ. Tên The Summer Sun đã dùng hè từ trước.
Liềm/cuốc cơ bản có mô tả mang tiêu đề Sickle/Hoe; không tự thêm “sắt” chỉ
vì bảng tên vật phẩm riêng ghi Iron Sickle/Iron Hoe.

`localization/character_profiles.json` hiện có Thomas, Zack, Popuri và các
nhãn Mother/Father/Old Man/Girl trong hồi tưởng. Mỗi hồ sơ có source ID và
phạm vi: bác/cháu của Thomas ở cảnh đón/hướng dẫn; tôi/cậu của Zack ở cảnh
giao hàng; mình/bạn của Popuri chỉ ở lời chào đã xác minh. Hồi tưởng dùng
mẹ/con, bố/con, ông/cháu, tớ/cậu. Không suy ra danh tính Girl hoặc áp giọng
trẻ con vào cảnh trưởng thành. Chưa áp xưng hô cho các NPC chưa rõ ngữ cảnh.

Wiki người dùng đề xuất:
https://harvestmoon.fandom.com/wiki/Harvest_Moon:_Friends_of_Mineral_Town

Lượt đọc đầu ngày 2026-10-23 bị proxy chặn HTTP 403 CONNECT. Sau khi
người dùng mở quyền truy cập, thử lại cả trang wiki và MediaWiki API lúc
08:52 UTC nhận HTTP 402 với thông báo “Please contact the site owner for
access.” Lỗi mới không còn là CONNECT 403. Chưa nhận được nội dung bài,
chưa đối chiếu glossary/hồ sơ nhân vật và không nhập dữ kiện từ trang này.
Khi truy cập được, chỉ dùng tham khảo khái niệm/nhân vật của bản GBA;
lời thoại, pointer, token vẫn lấy từ ROM.
Không trộn wiki remake hoặc More Friends of Mineral Town với bản USA này.

## Xuất hàng đợi

Trích catalog từ ROM đúng hash theo README trước, rồi:

```bash
.venv/bin/python tools/localization_queue.py
.venv/bin/python tools/localization_queue.py \
  --batch localization/qa/batches/tools-01.json \
  --output build/queue-tools.json --csv build/queue-tools.csv
.venv/bin/python tools/localization_queue.py \
  --bucket translate --context item_description --limit 24 \
  --output build/queue-next-descriptions.json
.venv/bin/python tools/localization_queue.py \
  --batch localization/qa/batches/thomas-arrival.json \
  --output build/queue-thomas.json
```

`make queue` xuất toàn bộ hàng đợi. JSON/CSV nằm trong build/, không track
catalog đầy đủ vào Git. CSV dùng UTF-8 BOM và bảo vệ ô có tiền tố công thức.
Công cụ chỉ xuất hàng đợi; chỉnh bản dịch trong file localization/vi/ tương
ứng rồi build bằng inserter. Không coi CSV/hàng đợi là bản dịch đã được duyệt.

Bốn nhóm chính:

| Nhóm | Ý nghĩa |
| --- | --- |
| translate | Đã rõ ngữ cảnh, chưa có bản dịch |
| qa | Có nháp, còn bước duyệt/kiểm thử |
| blocked | Chưa rõ ngữ cảnh, thuật ngữ chưa xác định hoặc validator thất bại |
| done | Có đủ duyệt ngôn ngữ/bố cục, renderer và playtest hợp lệ |

Trạng thái tách riêng: context_status, translation_status, language_review,
layout_review, renderer_check, playtest. Đổi translation_status thành reviewed
không tự làm các bước QA thành công. Không có bản ghi done trong phiên này.

`localization/qa/records.json` gắn QA với SHA-256 của nguyên chuỗi English/VI
UTF-8, bao gồm token. Sửa nguồn/bản dịch làm kết quả cũ thành stale. Duyệt
ngôn ngữ/bố cục cần người duyệt; renderer/playtest passed cần đường dẫn bằng
chứng và hash ROM. Render probe không tự nâng playtest hoặc layout_review.
Không chỉnh trực tiếp metadata để bỏ qua một lỗi thực tế.

Mục item.food.066.name (Flower) đã được xác minh là Bột mì bằng sách và
bảng hàng trong ROM; xem ITEM_LOCALIZATION.md. Chuỗi SCR chưa rõ người nói/chức năng
không tự vào hàng đợi dịch chỉ vì có thể đọc tiếng Anh.

## Lô vật phẩm đầu tiên

`localization/vi/item_descriptions_tools.json`: item.tool.000–015.description,
16 mô tả ở bảng pointer tool đã xác minh; giữ đủ hai cặp CR/LF mỗi mô tả.
Chèn mặc định cùng năm file VI trước đây. Không có source English tự tạo.

```bash
make build ROM="$FOMT_ROM" PYTHON=.venv/bin/python
.venv/bin/python tools/item_batch_smoke.py build/fomt-vi-demo.gba \
  --base-rom "$FOMT_ROM" --library build/mgba_bridge-0.10.5.so \
  --output build/items-0.10.5.json
```

Hai mGBA kiểm 16 pointer được relocate và 48 dòng qua bộ vẽ native có guard.
[Ảnh renderer](evidence/items-tools-renderer.png) là chẩn đoán có nhãn, **không
phải cửa sổ vật phẩm chơi thật**. Chưa lấy đủ dụng cụ nâng cấp/nguyền rủa bằng
luồng chơi bình thường; layout_review và playtest còn pending/not_run.
[Báo cáo lô](evidence/items-batch-validation.json) ghi rõ phạm vi này.

Có 37/347 mô tả có nháp, còn 310. Nhóm tiếp theo nên là rìu/búa/bình tưới
sau khi duyệt nghĩa và bố cục lô đầu; dùng hàng đợi để chọn ID thay vì chép
hàng loạt nội dung chưa rõ ngữ cảnh. Không đánh dấu toàn bộ 347 đã kiểm UI.

## Lô NPC khởi đầu: Thomas (lịch sử)

Chọn script 867, ID script.0867.000–008: cảnh đón người chơi trước/sau hồi
tưởng. Người nói và thứ tự đã được xác minh qua replay intro trước đây;
đây là lô chín bản dịch đã có để bắt đầu duyệt giọng bác/cháu và QA.
Bằng chứng playtest cũ ghi historical, không coi là chứng nhận target mới.
Chưa khẳng định đã định danh toàn bộ hội thoại thường ngày của Thomas.

Sau khi duyệt lô này, trace call-site/điều kiện của nhóm Thomas tiếp theo,
rồi mới chọn và dịch câu mới. Popuri chỉ có lời chào đầu đã xác minh, chưa
encounter tự nhiên trong bằng chứng hiện tại; không dùng nó để nhận toàn
bộ chuỗi chưa phân loại là thoại Popuri.
