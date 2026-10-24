# Harvest Moon: Friends of Mineral Town — Việt hóa thử nghiệm

Repo chứa công cụ trích xuất/chèn lại văn bản, font Việt và bản dịch nháp có nguồn
xác minh cho **FOMT GBA USA revision 0**. Đây là bản thử, **chưa Việt hóa 100%**.
Không chứa hoặc tự tải ROM thương mại. Bản vá IPS nằm trong `patches/`.

## Trạng thái hiện tại

[Đồ vật tương tác](docs/INTERACTIVE_OBJECTS.md): 261 nhãn/68 tên đã có nháp, gồm Bàn, Giường, Kệ sách, Tủ lạnh; hai bàn trong nhà được kiểm bằng input tự nhiên.

[Hội thoại NPC lô đầu](docs/NPC_DAILY_LOCALIZATION.md): thêm 34 câu Thomas và 51 câu Popuri; xưng hô theo source ID, điều kiện chưa xác minh ghi riêng.

Lô [vật phẩm/UI](docs/ITEM_LOCALIZATION.md) hoàn tất nháp; duyệt nghĩa và giao dịch cửa hàng tự nhiên còn pending.

- Trích xuất 9.309 bản ghi: 8.368 chuỗi SCR, 347 tên + 347 mô tả vật phẩm,
  7 nhãn menu tạm dừng, 24 mục tạo game mới, 28 mục hồi tưởng thời thơ ấu, 162 mục trong các menu con START và 26 chuỗi native cửa hàng/vật phẩm.
- 1.405 bản ghi dịch nháp: 347 tên vật phẩm, 347 mô tả, 26 chuỗi UI native, 7 menu, 1 lời chào Popuri,
  24 mục tạo game mới, 145 mục intro/hướng dẫn đầu game, 162 mục menu START, 85 câu NPC và 261 nhãn đồ vật tương tác.
- Lịch/HUD tiếng Việt: Năm, Xuân/Hè/Thu/Đông, CN/T2…T7 và đồng hồ 24 giờ.
  Tiêu đề lịch đã căn khoảng cách và thu nhỏ riêng số năm; HUD giữ vị trí đồng hồ,
  icon và màu gốc. [Ảnh hiện tại](docs/evidence/date-ui.png),
  [chi tiết](docs/DATE_UI.md), [ảnh tiêu đề trước/sau](docs/evidence/calendar-heading.png).
- Đã dịch menu con START: lưu/tải và tùy chọn Nhật ký, Ba lô, mô tả bản đồ,
  thống kê/Ghi chú và sách Mẹo điều khiển. Sửa hai tiêu đề Ba lô bị cắt chữ có dấu.
  [Ảnh trong game](docs/evidence/start-menu.png), [phạm vi và kiểm thử](docs/START_MENU.md).
- Đã Việt hóa phần Thomas đón người chơi, chuyến đi thời thơ ấu, ông lão/cô bé,
  lời hẹn viết thư, chuyển ngày, lời hướng dẫn của Thomas/Zack và bốn demo
  trồng trọt/chăn nuôi. [Ảnh intro](docs/evidence/intro-opening.png),
  [nguồn và kiểm chứng](docs/INTRO_LOCALIZATION.md).
- Đã Việt hóa luồng đặt tên nhân vật/nông trại/chó, chọn mùa/ngày sinh, xác nhận
  tên và xác nhận tạo game. Bàn phím giữ bộ ký tự gốc và giới hạn tên 12 ký tự.
  [Ảnh trong mGBA](docs/evidence/new-game-setup.png),
  [chi tiết hệ thống](docs/NEW_GAME_UI.md).
- Title đã đổi **Start → Bắt đầu**, **Continue → Tiếp tục**, có dấu, nét xanh
  ngọc mảnh với viền trắng bên trong và viền đen ngoài cùng. Có save thì hiện
  cả hai lựa chọn; giữ luồng tạo game mới/nạp save của game gốc.
- Font 134 chữ Việt; ASCII/chữ có dấu cùng baseline, giữ nét và advance 8px gốc.
  Bản sửa v2 xử lý lỗi lệch thân chữ/spacing; xem ảnh trước–sau trong `docs/evidence`.
- Chèn lại ở vùng ROM mở rộng, giữ nguyên bytecode sự kiện và dữ liệu gameplay.
- Kiểm thử mGBA: boot, tạo game mới, hội thoại Thomas, 7 nhãn menu, render font,
  lịch/HUD và ghi Diary, nạp lại save sau boot; 138 pytest đạt. Chi tiết và giới hạn trong báo cáo tiến độ.

Chưa xác minh toàn bộ gameplay, mọi màn hình vật phẩm, TV/sách/sự kiện, phần cứng
GBA thật hoặc nhập tên người chơi có dấu. Phần lớn hội thoại vẫn là tiếng Anh.

## Dịch và QA

[Bàn dịch Anh–Việt](docs/TRANSLATION_WORKBENCH.md): chạy
`.venv/bin/python tools/translation_workbench.py`, rồi mở đường dẫn terminal
in ra. Có tìm kiếm, lọc lô/ngữ cảnh/người nói, glossary, kiểm token/độ dài và
lưu nháp có backup trực tiếp vào file dịch.

[Quy trình làm việc](docs/LOCALIZATION_WORKFLOW.md): glossary, hồ sơ xưng hô,
hàng đợi JSON/CSV và lô 16 mô tả dụng cụ đầu tiên. `make queue` xuất hàng đợi;
nguồn chưa rõ ngữ cảnh giữ blocked.

## Cấu trúc và dọn workspace

[Xem cấu trúc project](docs/PROJECT_STRUCTURE.md). `build/` chứa đầu ra tái tạo được;
`local-data/` giữ font tham khảo và save thử cục bộ, không đưa lên Git.
Chạy `make clean` để xóa đầu ra build/cache; lệnh này giữ nguồn, bản dịch, bản vá
phát hành, môi trường `.venv/` và dữ liệu trong `local-data/`.

## Lộ trình

[Bộ chuẩn nền tảng](docs/PLATFORM_BASELINE.md) chốt font, bố cục và 43 ảnh
framebuffer. `make platform-check` kiểm hai build/IPS và pytest;
`make platform-emulator` bổ sung replay và so pixel trên hai mGBA.

[Roadmap Việt hóa](docs/ROADMAP_VI.md): mốc nội dung, công cụ, QA và điều kiện phát hành.

## ROM đầu vào

Chỉ dùng bản ROM bạn có quyền sử dụng:

```
Game code: A4NE; revision: 0; size: 8388608
SHA1: a2fc3574f0a65a4fcf7682fb274b9d7eebdef963
```

ROM có patch sẵn hoặc revision khác sẽ bị từ chối. Luôn giữ ROM và save gốc
riêng; công cụ không ghi đè ROM đầu vào. ROM build và save không được track Git.

Khi đổi từ bản font v1 sang v2, hãy khởi động lại ROM mới và load save **trong
game** (`.sav`), không load savestate emulator của ROM cũ. Savestate giữ các
con trỏ vào vùng ROM mở rộng đã được bố trí lại. Đã kiểm tra một save SRAM v1
ngày 2 load trên v2; chưa kiểm tra mọi save/cảnh của người chơi.

## Chạy từ đầu

Python 3.10+; các lệnh bên dưới chạy tại thư mục repo. Không cần decompile game,
agbcc hoặc devkitARM để build bản vá này.

```bash
cd /workspace/FOMT
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt

# Thay đường dẫn bằng ROM của bạn; giữ dấu nháy nếu tên file có khoảng trắng.
export FOMT_ROM='/path/to/Harvest Moon - Friends of Mineral Town (USA).gba'
.venv/bin/python tools/text_extractor.py "$FOMT_ROM"
.venv/bin/python tools/text_inserter.py "$FOMT_ROM"
FOMT_ROM="$FOMT_ROM" .venv/bin/python -m pytest -q
```

Đầu ra mặc định: `localization/en/catalog.json` (catalog tổng, sinh local),
`build/fomt-vi-demo.gba` (chỉ local), `patches/fomt-vi-demo.ips`,
`build/insertion-report.json`. Cùng ROM/bản dịch/font/artwork tạo cùng byte đầu ra.

Có thể dùng `make extract/build/test ROM="$FOMT_ROM" PYTHON=.venv/bin/python`.
`Makefile` mới chỉ phục vụ localization. Makefile decomp gốc ở checkout tham
khảo không được dùng cho quy trình này; mục tiêu matching của nó không cần
thiết để trích xuất và patch văn bản.

Để build riêng bản thử nhỏ gồm 38 chuỗi (10 câu Thomas đã chuyển sang intro.json):

```bash
.venv/bin/python tools/text_inserter.py "$FOMT_ROM" \
  --translations localization/vi/pilot.json \
  --output build/fomt-vi-pilot.gba \
  --patch build/fomt-vi-pilot.ips --report build/pilot-report.json
```

## Áp dụng bản vá đã tạo

```bash
.venv/bin/python tools/apply_ips.py "$FOMT_ROM" \
  --patch patches/fomt-vi-demo.ips --manifest patches/manifest.json \
  --output build/fomt-vi-demo.gba
```

Lệnh này kiểm tra hash ROM nguồn, bản vá và ROM đích. IPS tiêu chuẩn không tự
chứa checksum; `manifest.json` bổ sung kiểm tra đó cho release này. Chỉ phát hành
IPS + manifest + tài liệu, không phát hành file `.gba`. Đây là bản thử, chưa phải
bản phát hành Việt hóa hoàn chỉnh.

## Kiểm thử bằng mGBA không cần giao diện

Tùy chọn; công cụ extract/build/test cơ bản không cần emulator. Adapter dùng API
nội bộ mGBA nên phải compile với cùng checkout/config build. Trong phiên Cloud
này checkout đã có tại `/workspace/mgba`.

```bash
# Nếu chưa có checkout emulator:
git clone https://github.com/mgba-emu/mgba /workspace/mgba
git -C /workspace/mgba checkout fd9dc5c2cbf234365068855851107e762fc6211b
cmake -S /workspace/mgba -B /workspace/mgba/build \
  -DBUILD_QT=OFF -DBUILD_SDL=OFF -DBUILD_GL=OFF \
  -DBUILD_GLES2=OFF -DBUILD_GLES3=OFF -DBUILD_PYTHON=OFF \
  -DUSE_FFMPEG=OFF -DUSE_LIBZIP=OFF -DUSE_LZMA=OFF \
  -DUSE_SQLITE3=OFF -DUSE_DISCORD_RPC=OFF \
  -DBUILD_STATIC=ON -DBUILD_SHARED=ON -DENABLE_DEBUGGERS=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build /workspace/mgba/build -j 4
bash tools/build_mgba_bridge.sh /workspace/mgba
.venv/bin/python tools/emulator_smoke.py build/fomt-vi-demo.gba \
  --base-rom "$FOMT_ROM" --output-dir build/demo-emulator
```

Cần GCC, CMake và make; mGBA dùng BIOS thay thế tích hợp, không tải BIOS thương mại.
Adapter đọc `C_DEFINES` từ build Unix Makefiles để khớp ABI của đúng phiên bản.
Nếu dùng mGBA 0.10.5, build checkout tag `0.10.5` tương tự (CMake 4 cần thêm
`-DCMAKE_POLICY_VERSION_MINIMUM=3.5`), rồi tạo adapter riêng:

```bash
bash tools/build_mgba_bridge.sh /workspace/mgba-0.10.5 build/mgba_bridge-0.10.5.so
.venv/bin/python tools/emulator_smoke.py build/fomt-vi-demo.gba \
  --base-rom "$FOMT_ROM" --library build/mgba_bridge-0.10.5.so
```

Ảnh, JSON kiểm thử và save thử chỉ ghi dưới `build/`. Xem ảnh thủ công sau khi chạy;
thông báo replay hoàn tất không tự chứng minh mọi màn hình đã đúng. Không dùng
emulator savestate để thay cho kiểm thử save trong game.

## Tiếp tục dịch

1. Xác minh context/speaker từ game hoặc call-site, ghi `context_evidence`.
2. Tra [glossary](localization/glossary.json), giữ tên riêng và cách xưng hô.
3. Sao chép bản ghi từ catalog, nhập `vietnamese_translation`, đặt trạng thái
   `translated`. Không tự tạo `original_english` hoặc địa chỉ.
4. Truyền file JSON mới bằng `--translations` cùng các file đã có; ID trùng bị từ chối.
5. Build, kiểm tra token/chiều ngang, test trong emulator và duyệt ảnh. Chỉ đặt
   `reviewed` sau khi duyệt cả ngôn ngữ và bố cục.
6. Cập nhật [TRANSLATION_PROGRESS.md](docs/TRANSLATION_PROGRESS.md) sau mỗi phiên.

`tools/fomt_text.py` là adapter định dạng; `vietnamese_font.py` tạo font/hook;
`text_extractor.py` và `text_inserter.py` là CLI. Không patch byte theo kết quả
quét ASCII chưa xác minh. Không thay ROM gốc, không tải ROM và không push repo
tham khảo. [TEXT_SYSTEM.md](docs/TEXT_SYSTEM.md) và
[VIETNAMESE_FONT.md](docs/VIETNAMESE_FONT.md) ghi địa chỉ, chứng cứ và phần chưa rõ.
