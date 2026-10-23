# Cấu trúc project và vòng đời file

| Đường dẫn | Vai trò | Chính sách |
| --- | --- | --- |
| README_VI.md | Hướng dẫn sử dụng/build/kiểm thử | Giữ ngắn, trỏ tới tài liệu chuyên đề |
| tools/ | Extractor, inserter, font/graphics adapter, emulator checks | Giữ source được dùng; không chứa output |
| tests/ | Kiểm source, codec, pointer, buffer và layout | Giữ |
| localization/en/ | Subset nguồn xác minh; catalog/discovery đầy đủ sinh cục bộ | Subset track Git; catalog đầy đủ không track |
| localization/vi/ | Các nhóm dịch và cấu hình đồ họa | Giữ; là dữ liệu làm việc chính |
| localization/qa/, character_profiles.json | Batch, QA theo hash và hồ sơ người nói theo cảnh | Track Git; hàng đợi xuất ra build/ |
| localization/font/, glossary.json | Bảng mã và thuật ngữ | Giữ |
| localization/platform_baseline.json | Khóa nguồn font/bố cục/pipeline và 43 ảnh chuẩn | Track Git; chỉ sửa sau khi duyệt thay đổi |
| patches/ | IPS phát hành hiện tại và manifest | Track Git; không chứa ROM |
| docs/ | Tài liệu hệ thống, roadmap và tiến độ hiện tại | Lịch sử chi tiết xem Git |
| docs/evidence/ | Báo cáo, ảnh kiểm chứng hiện tại và các mốc chức năng | Không giữ mọi ảnh debug/thử font |
| build/ | ROM build, báo cáo chi tiết, output smoke và adapter .so | Có thể tái tạo; không track Git |
| local-data/ | Font tham khảo và save fixture cục bộ được bảo toàn | Không track Git, không xóa bằng make clean |
| .venv/ | Dependency Python của workspace | Không track Git; giữ khi clean |

## Dọn dẹp

`make clean` chỉ xóa build/, .pytest_cache/ và __pycache__ trong tools/tests.
Nó xóa cả ROM build và adapter mGBA đã biên dịch: build lại theo README.
Nguồn, bản dịch, patches/, docs/evidence/, local-data/ và .venv/ được giữ.
Không đặt ROM đầu vào, font người dùng hoặc save quan trọng trong build/.

Sau phiên dọn hiện tại, build/ giữ ROM mới nhất, insertion-report.json,
hai adapter mGBA và năm thư mục kiểm thử gần nhất. Các bản ROM và ảnh thử
cũ không phải đầu vào bắt buộc để build. Đầu vào gốc do người dùng cung cấp
trong attachments/ ngoài repo không bị thay đổi.

Các save thử khác nhau được giữ theo SHA-256 trong local-data/fixtures/;
index.json ghi đường dẫn nguồn trước khi dọn. day2.sram là bản sao tiện dùng
của fixture ngày 2 từ smoke hiện tại. Đây là dữ liệu cục bộ, không phải file
cần phân phối trong bản vá.

## Kiểm chứng

[platform-v1](PLATFORM_BASELINE.md) và [báo cáo](evidence/platform-validation.json)
chốt nền tảng; `make platform-emulator` tái tạo dưới build/platform-check/.
Ảnh chuẩn mới chỉ lưu khi khác ảnh mốc cũ; không lưu bản sao những ảnh đã khớp.

Nguồn hiện tại của bản vá: patches/manifest.json và
[date-ui-validation.json](evidence/date-ui-validation.json). Báo cáo tổng hợp
là [validation.json](evidence/validation.json). Các báo cáo chuyên biệt intro,
tạo game và START giữ hash từng mốc cũ và phải được đọc đúng phạm vi đó.

Ảnh tổng hợp mỗi nhóm chỉ giữ một bản. Ảnh của các fixture riêng vẫn được
giữ khi báo cáo dùng chúng để xác minh kết quả. Các lần thử font đã bị thay
thế có thể lấy lại từ lịch sử Git, không cần lưu mọi bản trong cây hiện tại.
