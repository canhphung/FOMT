# Roadmap Việt hóa Harvest Moon: Friends of Mineral Town

Cập nhật 2026-10-23. Baseline triển khai: `f8e1af2`, ROM USA A4NE revision 0.
Mục tiêu: Việt hóa toàn bộ văn bản có thể tiếp cận, giữ gameplay/save gốc,
phát hành bản vá; không decompile toàn bộ game hoặc phân phối ROM.

## Điểm xuất phát đã kiểm đếm

| Hạng mục | Hiện tại |
| --- | --- |
| Catalog trích xuất | 9.283 ID |
| Bản dịch nháp | 706 ID, không trùng nhau |
| Bản ghi được đánh dấu reviewed | 0 |
| Chưa có bản dịch trong catalog | 8.577 ID |
| Chuỗi còn context script_string_unclassified | 8.250 ID |
| Tên vật phẩm | 346/347 có nháp |
| Mô tả vật phẩm | 21/347 có nháp |
| Kiểm thử tự động | 106 pytest đạt; có smoke mGBA 0.10.5/0.11-dev |

706/9.283 tương đương khoảng 7,6% **ID trong catalog**, không phải 7,6%
lượng từ hoặc toàn bộ game. Đồ họa chữ được theo dõi riêng; catalog có thể
còn thiếu nguồn văn bản chưa phát hiện. Các con số ngữ cảnh và dịch là hai
chiều khác nhau, không cộng vào nhau.

Đã có pipeline extract → JSON → font/bảng mã Việt → insert → IPS, title,
tạo nhân vật, intro/hướng dẫn đầu game, START và lịch/HUD. Đây là phạm vi
đã triển khai, chưa đồng nghĩa mọi câu đều được duyệt hoặc mọi nhánh đều chơi thử.

## Thứ tự thực hiện và điều kiện hoàn thành

| Mốc đề xuất | Phạm vi | Điều kiện qua mốc |
| --- | --- | --- |
| A — ổn định nền tảng | Chốt font, layout, baseline và bộ kiểm tra hiện có | Build lặp lại đúng hash; IPS áp lại đúng ROM; boot/save/load qua; lỗi chặn có ảnh tái hiện |
| B — quản lý bản dịch/ngữ cảnh | Hàng đợi dịch, glossary, speaker, source reference, bằng chứng ngữ cảnh | Mỗi lô có ID nguồn, ngữ cảnh xác minh và trạng thái dịch/duyệt/chơi thử riêng |
| C — vật phẩm và UI thường dùng | 326 mô tả còn thiếu, 1 tên cần xác minh, cửa hàng và các UI còn thiếu được tìm thấy | Vật phẩm/nhãn đã rõ nghĩa, thuật ngữ thống nhất; kiểm cửa sổ tên/mô tả, mua/bán và nhánh xác nhận |
| D — đời sống hằng ngày | Hội thoại NPC thường ngày, mùa/thời tiết, công việc nông trại | Dịch theo từng NPC/bối cảnh; duyệt xưng hô; có encounter thật hoặc ghi rõ chưa tái hiện |
| E — sự kiện và nội dung dài | Lễ hội, sinh nhật, tình cảm/gia đình; TV, sách, hướng dẫn, nội dung tùy chọn có nguồn xác minh | Mỗi nhóm có bản đồ nhánh/điều kiện kích hoạt; lựa chọn và biến được bảo toàn; hội thoại dài không cắt/tràn |
| F — alpha đầy đủ | Hoàn tất nháp cho mọi nguồn văn bản tiếp cận đã kiểm kê | Không còn ID tiếp cận thiếu bản dịch/ngữ cảnh; kiểm kê đồ họa chữ đầy đủ; danh sách nội dung chưa kiểm được công khai |
| G — beta và v1.0 | Duyệt ngôn ngữ, kiểm thử nhiều save/nhánh, đóng gói bản vá | Tất cả nội dung phát hành đã duyệt; không còn lỗi chặn; có báo cáo tương thích, changelog và hướng dẫn áp bản vá |

Tên phiên bản trên là mốc kế hoạch, chưa phải bản phát hành hoặc cam kết thời gian.
Mốc B tiếp tục phục vụ C–E; không chờ phân loại hết 8.250 chuỗi rồi mới dịch.
Dịch và kiểm tra theo từng lô đã xác minh để luôn có bản build chơi được.

## A. Chốt nền tảng trước khi tăng tốc

- Giữ font HUD/lịch/title đã duyệt; chỉ chỉnh khi có lỗi đọc, thiếu dấu,
  chồng chữ, clipping hoặc phản hồi cụ thể. Tránh để tinh chỉnh thẩm mỹ nhỏ
  liên tục chặn tiến độ nội dung.
- Giữ bộ ảnh chuẩn và hash ROM/IPS. Mỗi thay đổi renderer có kiểm vùng nhớ,
  VRAM/OAM và ảnh trong game; thay đổi văn bản kiểm control code/độ dài phù hợp.
- Chốt glossary hiện có, tên riêng và nguyên tắc xưng hô. Mỗi NPC cần hồ sơ
  giọng nói có bằng chứng; không suy đoán một cách xưng hô chung cho cả làng.

## B. Công cụ dịch và phân loại ngữ cảnh

Tận dụng Python hiện có. Bổ sung công cụ quản lý, không viết lại engine.
Ưu tiên bảng làm việc cục bộ đơn giản với các cột ID, nguồn, English, Vietnamese,
người nói, ngữ cảnh, token, trạng thái và liên kết ảnh/bằng chứng. Tìm kiếm,
lọc, xem các câu liền kề và báo lỗi trước khi build quan trọng hơn giao diện cầu kỳ.

Điều tra chuỗi SCR theo script/call-site, nhóm hội thoại liền kề, speaker và
điều kiện nhánh khi xác minh được. Chỉ đưa nhóm rõ chức năng vào hàng đợi dịch.
Chuỗi chưa rõ nghĩa/chức năng giữ nguyên và ghi lý do bị chặn; không coi là đã dịch.

Có thể dùng AI để đề xuất bản nháp sau khi có ngữ cảnh và glossary. Validator
phải từ chối mất/đổi token, placeholder, control stream hoặc glyph không hỗ trợ.
Không tự đánh dấu reviewed, không tự nới validator để câu dịch dài được chèn.

Trạng thái QA nên theo dõi riêng với translation_status hiện có: đã xác minh
ngữ cảnh, đã duyệt ngôn ngữ, đã kiểm bố cục, đã gặp trong game. Đây là phần
cần bổ sung, không phải tính năng giao diện đã tồn tại.

## C. Hoàn thiện nội dung thấy thường xuyên

Ưu tiên 326 mô tả vật phẩm còn thiếu vì đã có nguồn xác minh và tái sử dụng
được 346 tên hiện tại. Xác minh nhãn còn lại (tài liệu trước ghi Flower)
trước khi quyết định dịch. Duyệt cả tên đã có nháp, không chỉ điền ô trống.

Rà cửa hàng, mua/bán, nâng cấp, bệnh viện/dịch vụ, cửa sổ vật phẩm và popup
lịch để xác định phần nào có text/graphics adapter còn thiếu. Danh sách này
là phạm vi cần kiểm kê, không phải khẳng định đã tìm được mọi chuỗi tương ứng.
Dùng cùng thuật ngữ cho tên hàng, menu, mô tả và lời thoại nhắc đến hàng đó.

## D–E. Hội thoại theo nhân vật và sự kiện

Mỗi lô theo một NPC hoặc một luồng sự kiện có ngữ cảnh đầy đủ. Với NPC,
đi từ lời chào/gặp lần đầu đến câu thường ngày, rồi các biến thể mùa,
thời tiết, quan hệ và phản hồi vật phẩm đã xác minh. Với sự kiện, giữ cả
câu dẫn, mọi lựa chọn và nhánh trả lời, thay vì dịch từng câu rời.

Ưu tiên lời thoại hay gặp trong sinh hoạt trước, rồi lễ hội/sinh nhật,
sự kiện tình cảm/gia đình và nội dung tùy chọn/hiếm. TV, sách và hướng dẫn
là luồng nội dung dài riêng để kiểm chia trang, tốc độ đọc và giới hạn hộp thoại.
Không hứa bao phủ những nhóm chưa có bằng chứng nguồn hoặc đường kích hoạt.

## F–G. Định nghĩa hoàn thành và phát hành

Alpha đầy đủ nghĩa là mọi mục **tiếp cận được trong inventory đã kiểm kê**
có nháp, kể cả đồ họa chữ ngoài catalog. Cần ghi riêng nội dung chưa rõ,
không dùng, trùng lặp hoặc không tái hiện; không loại chúng âm thầm để đạt 100%.
Khi phát hiện nguồn mới, tăng mẫu số và ghi thay đổi inventory.

V1.0 cần duyệt cả 706 nháp hiện tại lẫn phần dịch mới: nghĩa, giọng nhân vật,
thuật ngữ, token và bố cục. Tên riêng giữ nguyên theo glossary không được
đếm thành câu đã đổi ngôn ngữ. Review ngôn ngữ và playtest phải báo riêng.

Ma trận QA gồm tạo/nạp game; save ở nhiều giai đoạn; bốn mùa, đầu/cuối tháng,
lễ hội và các nhánh sự kiện đã tìm được; menu/vật phẩm/cửa hàng; text dài,
biến tên người chơi và lựa chọn. Dùng save fixture có nguồn ghi rõ, kết hợp
replay tự nhiên. Fixture giao diện không thay thế chơi xuyên mùa.

Mỗi bản vá gồm ROM nguồn đúng hash, IPS/BPS, hash đích, phạm vi đã dịch,
lỗi còn biết và hướng dẫn save. Kiểm mGBA hai phiên bản; bổ sung GBA/flashcart
khi có thiết bị, không công bố đã kiểm phần cứng nếu chưa làm.

## Việc làm ngay ở phiên kế tiếp

1. Chốt thuật ngữ vật phẩm/xưng hô và rà những lỗi chặn trong bản hiện tại.
2. Bổ sung hàng đợi ngữ cảnh/QA tối thiểu trên dữ liệu JSON đang có.
3. Dịch thử một lô mô tả vật phẩm đã xác minh; nhập lại, kiểm UI thực tế,
   duyệt lô đó rồi mở rộng đến đủ 347 mô tả.
4. Song song kiểm kê UI cửa hàng và chọn NPC đầu tiên có chuỗi/ngữ cảnh
   xác minh đầy đủ cho lô hội thoại kế tiếp.

Đo năng suất bằng số từ có ngữ cảnh đã dịch/duyệt và thời gian QA trong các
lô đầu rồi mới ước lượng lịch phát hành. Không thể suy thời gian hoàn thành
chính xác từ số ID: một tên vật phẩm và một đoạn hội thoại dài đều là một ID.

## Báo cáo sau mỗi phiên

Ghi inventory/ID mới, số nháp mới, số đã duyệt, số đã kiểm trong game,
nhóm bị chặn và lý do, test/ảnh/hash bản vá, cùng lô ưu tiên tiếp theo.
Cập nhật [TRANSLATION_PROGRESS.md](TRANSLATION_PROGRESS.md); không cộng nháp,
review và playtest thành một phần trăm duy nhất.
