# Popuri — bản dịch có ngữ cảnh, 2026-10-24

Thêm 87 chuỗi, tổng **139/144** câu trong script chuẩn 993; cả dự án 1.566
bản dịch nháp. Đây không phải toàn bộ lời Popuri trong các sự kiện nhiều NPC.
Bản Việt ở pilot.json; contract nguồn ở localization/popuri_context.json.

## Cơ sở ngữ cảnh

Đối chiếu tài liệu riêng trong knowledge (Fogu và Fandom), không đưa bản gốc
lên Git. URL tham khảo: https://fogu.com/hm4/girls/popuri.htm và
https://harvestmoon.fandom.com/wiki/Popuri_(FoMT).

Popuri vui vẻ, thích động vật, muốn được đối xử như người lớn; Rick là anh
trai hay bao bọc cô. Lillia là mẹ, Rod là bố đang đi tìm cách chữa bệnh cho
mẹ. Popuri có thể kết hôn với người chơi hoặc Kai. Tài liệu Fogu ghi Lila,
nguồn game/Fandom dùng Lillia; không tự đổi tên riêng trong ROM theo bài web.

Wiki chỉ bổ sung ý nghĩa/quan hệ, không cung cấp thoại thay ROM. Nguồn thoại
là ROM USA hợp pháp; literal constructor 0x08035BFC xác định script 993,
hash CODE và từng push-index → OnCall33 được kiểm lại. Không đoán địa chỉ.

## Giọng nói và xưng hô

- Nói chuyện thông thường/quà dùng chung: mình–bạn, vui vẻ, tự nhiên.
- Câu rõ là vợ chồng, mang thai, nuôi con và gọi biệt danh hôn nhân:
  em–anh. Giữ nguyên VAR:29, VAR:2A và các biến khác, không thay bằng tên cố định.
- Với Rick: anh/anh trai; bố mẹ: bố/mẹ; Carter: cha Carter.
- Không áp em–anh cho toàn bộ 1..92: nhóm này còn có phản ứng quà,
  lời từ chối tình cảm và lời mời Lễ hội Đêm sao.
- Không tự suy ngưỡng tim, lịch hoặc điều kiện cưới từ thứ tự các chuỗi.
  Ngữ cảnh ngôn ngữ rõ trong lời thoại khác với chứng minh toàn bộ đường kích hoạt.

125 đổi ý “quấn lấy” thành “lo cho mình quá mức” để thể hiện sự bảo bọc của
Rick. 133 dùng “đẹp trai” thay “đẹp mã”, giữ sắc thái tình cảm nhẹ nhàng;
English `quite men` được hiểu là lỗi gõ của quiet trong câu đối chiếu vẻ ngoài
và tính trầm lặng, không sửa nguồn gốc. 136 gọi cha Carter phù hợp nhà thờ.

## Phần chưa dịch

5, 21, 92: chứa RAW:8166 trong dấu nháy của English; chưa đổi/bỏ RAW để
ép câu Việt qua validator. 38, 39: nhãn lựa chọn lời mời, cần bằng chứng
caller/choice widget riêng. Cả năm chuỗi giữ nguyên byte. Các heart event,
rival event, cưới/lễ hội ở script khác chưa được coi là hoàn thành.

## Kiểm chứng

146 test ROM đạt. Hai mGBA: **139 fixture, 192 WAIT, 404 dòng renderer**,
so bitmap toàn bộ cache tại từng điểm dừng. CODE/JUMP script 993 nguyên vẹn,
5 chuỗi chưa chọn không đổi byte, SRAM không đổi. Biến dùng 12 chữ số thay
thế trong fixture để kiểm khoảng trống; không phải chứng minh giá trị biến
thật hoặc mọi nhánh quan hệ. Fixture ẩn portrait/name, không gán ảnh một NPC
khác làm Popuri; nền nhà chỉ là host. Chưa có playtest encounter tự nhiên
cho cả 139 câu hoặc duyệt ngôn ngữ/bố cục thủ công.

[Kiểm chứng](evidence/popuri-validation.json). Bộ chuẩn font và ảnh cũ được
giữ nguyên. Full-platform/golden/Chromium trước đây thuộc hash lịch sử,
không khẳng định đã chạy lại toàn bộ cho bản mới.

Ảnh fixture nằm trong docs/evidence/popuri/, không phải ảnh gặp Popuri tự nhiên.
