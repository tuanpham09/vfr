# Roadmap MVP

Quy ước ID: `S{sprint}-{số}`. Mỗi task có file riêng trong `plans/active/` khi bắt đầu.

## S0 — Harness (làm trước mọi thứ)
| ID | Task | Xong khi |
|---|---|---|
| S0-1 | Khởi tạo repo, `pyproject`, `Makefile`, pre-commit, CI chạy `make check` | `make check` xanh trên repo rỗng |
| S0-2 | import-linter contracts + `tools/custom_lints.py` (VFR001–006) | Cố ý vi phạm → lint fail với thông báo đúng |
| S0-3 | `types.py` (VideoItem, WsMessage), `config.py`, `log.py`, `events.py` | mypy strict xanh, unit test |
| S0-4 | Quy trình fixture: `scrub_fixture.py`, `check_fixtures.py`, INDEX.md | Chạy được trên fixture mẫu |
| S0-6 | `core/pipeline/counts.py::parse_count` + test bảng ≥ 25 case + hypothesis (xem `design/FILTERS_AND_FACE.md`) | Test xanh; không raise với mọi đầu vào; trả `(int\|None, is_approx)` |
| S0-5 | **Thu fixtures thật** cho 3 nền tảng (danh sách trong FIXTURES.md) | Có đủ bộ fixture, gỡ [VERIFY] đầu tiên |

## S1 — Khung + TikTok
| ID | Task |
|---|---|
| S1-1 | Extension: manifest, background (WS, ping, reconnect, token), content, inject (hook), adapter TikTok |
| S1-2 | `ws_server` + `FakeExtension` + contract test |
| S1-3 | `normalizers/tiktok.py` + snapshot test |
| S1-4 | `db.py`, migration, repo (dedupe, batch write) |
| S1-5 | `task_runner` (tuần tự, state machine, stop) |
| S1-6 | PySide6: khung cửa sổ, tab Cào dữ liệu, table model, phân trang, log, trạng thái Chrome Ext |
| S1-7 | `keyword_service` + `llm_gemini` (gemini-3.6-flash) + cache + fallback |
**Nghiệm thu:** AC1 trên TikTok.

## S2 — Douyin, XHS, lọc, tải
| ID | Task |
|---|---|
| S2-1 | Adapter + normalizer Douyin (SSR + API) |
| S2-2 | Adapter + normalizer XHS (xsec_token, chỉ note video) |
| S2-3 | Phát hiện đăng nhập/captcha, `paused_*`, hộp thoại, `resume` (AC3) |
| S2-4 | Lọc: lượt xem (fallback like), giỏ hàng, relevance luật |
| S2-5 | `face_detect` YuNet + badge + lọc hiển thị (AC4) |
| S2-6 | Downloader (httpx, resume, retry, 3 luồng, yt-dlp fallback), Tải trực tiếp, Mở video đã cào (AC2) |
| S2-8 | XHS: bổ sung `comment`/`collect` từ trang chi tiết khi search thiếu (giới hạn 1 lần/video, sau lọc) |
| S2-9 | Cột Views/Tim/Comment/Lưu theo nền tảng, sắp xếp, `—` cho None, `~` cho xấp xỉ |
| S2-7 | Mode @User, Hashtag, Link video cho 3 nền tảng |

## S3 — Ổn định, đóng gói
| ID | Task |
|---|---|
| S3-1 | Hành vi chống bot (jitter, rate limit, giảm tốc khi captcha) |
| S3-2 | Cài đặt (thư mục, delay, luồng, proxy, cổng, API key) |
| S3-3 | Soak test 100 video/nền tảng (AC5), sửa lỗi |
| S3-4 | PyInstaller (Windows), hướng dẫn cài extension (load unpacked), checklist release |

## Phụ thuộc
S0-5 và S0-6 chặn S1-3, S2-1, S2-2. Không viết normalizer khi chưa có fixture thật.

## Đợt 1 — trạng thái (đã code, chưa chạy thật)
S0-1..S0-4, S0-6, S1-1..S1-6 (TikTok), S2-1/S2-2 (khung normalizer Douyin/XHS), S2-3 (login/captcha pause-resume), S2-4 (lọc view/tim/giỏ hàng/**sát từ khóa**), S2-7 (user/hashtag/link), S2-9 (cột số liệu). Còn chờ **S0-5 (fixture thật)** để gỡ `[VERIFY]`.

## Đợt 2 — Hoàn thiện tính năng cào chính (ưu tiên) rồi mới đến tính năng phụ

**Nguyên tắc:** A1 chặn mọi việc còn lại. Không có dữ liệu thật thì chỉ viết được code, không kiểm chứng được độ đúng. Thứ tự dưới đây là mặc định, đổi theo mục "Quyết định mở".

### Nhóm A — Cào chính đúng với dữ liệu thật
| ID | Việc | Phụ thuộc | Xong khi |
|---|---|---|---|
| **A1** | Chạy với Chrome thật + "Lưu JSON thô"; thu fixture thật (S0-5) cho 3 nền tảng × (từ khóa, hashtag, user, link, chưa đăng nhập); sửa normalizer, selector login/captcha, tên cookie; gỡ `[VERIFY]` trong `platforms/*.md` và `FIELD_VERIFICATION.md` | Người dùng chạy app và gửi capture | Mỗi nền tảng có ≥ 3 fixture thật; test normalizer snapshot qua; cột view/tim/comment/lưu đúng với số trên web |
| A2 | Chạy thật UI + WebSocket; sửa lỗi; chỉnh UI khớp ảnh gốc (thanh cuộn cột trái, nút Copy token, nút Duyệt thư mục); pytest-qt smoke test | A1 (một phần) | AC1 (30 video không trùng, Dừng được) và AC3 (đăng nhập → tạm dừng → tiếp tục) đạt trên 3 nền tảng |
| A3 | Gemini sinh từ khóa (`gemini-3.6-flash`, ≤ 2 truy vấn; Douyin/XHS tiếng Trung, TikTok Việt/Anh); cache; fallback; ô API key + "Thử kết nối" trong Cài đặt | A2 | Từ khóa Việt trên Douyin/XHS ra kết quả; thiếu key vẫn cào được (xem `design/KEYWORD_LLM.md`) |
| A4 | Tải video: httpx (tiếp tục tải dở, retry, 3 luồng), yt-dlp dự phòng TikTok; bật "Tải trực tiếp", cột trạng thái tải, "Mở video đã cào" | A1 (để biết URL media thật) | AC2: file phát được, đúng `downloads/{platform}/{author_id}/{video_id}.mp4` + `.json` |
| A5 | XHS: bổ sung comment/lưu từ trang chi tiết khi tìm kiếm thiếu (S2-8); **tắt mặc định**, bật bằng Cài đặt | A1 | Cột Comment/Lưu của XHS có số khi bật; giới hạn 1 lần mở/video |
| A6 | Face detect YuNet trên ảnh bìa + badge 👤; mở khóa nút "Phân biệt video có mặt người" và lọc hiển thị | A4 (cache ảnh bìa) | AC4: mọi video đạt lọc có badge; lọc có người/không người hoạt động |

### Nhóm B — Ổn định, tránh bị chặn
| ID | Việc | Xong khi |
|---|---|---|
| B1 | Giới hạn tốc độ: số tác vụ/giờ, số video/ngày theo nền tảng; tự giảm tốc khi gặp captcha liên tiếp (`design/ANTI_DETECTION.md`) | Test với đồng hồ giả; log hiển thị khi giảm tốc |
| B2 | Cài đặt đầy đủ: proxy, số luồng tải, API key lưu bằng keyring | Đổi cài đặt có hiệu lực không cần khởi động lại (trừ cổng) |
| B3 | Soak test 100 video/nền tảng liên tục (AC5) | Không treo, UI không đứng, không rò bộ nhớ rõ rệt |
| B4 | Đóng gói PyInstaller (Windows), hướng dẫn cài extension, checklist release; import-linter + custom lints theo `harness/LINTS.md` | Bản cài chạy trên máy sạch |

### Nhóm C — Tính năng phụ (sau A và B)
Tìm bằng ảnh (`design/IMAGE_SEARCH.md`, ADR-006). Tab "2. Xử lý video", "3. Review & xuất", Auto: chỉ có chỗ giữ chỗ, chưa làm.

| ID | Task | Xong khi |
|---|---|---|
| S4-1 | Ô "Tìm bằng ảnh" (kéo thả/chọn tệp, thumbnail, nút xóa), khóa khi thiếu API key | UI hiển thị, ảnh được thu nhỏ ≤ 1024px |
| S4-2 | `llm_gemini.image_to_queries` (structured output, cache SHA-256, ≤ 2 truy vấn, fallback) + `FakeVision` | Unit test parser/cache/fallback |
| S4-3 | Tải ảnh bìa, `image_match` theo lô 8, trần `max_vision_calls_per_job`, cache `(ảnh, cover_url)` | Test runner với FakeVision (yes/no/unsure, hết trần) |
| S4-4 | Cột "Khớp ảnh" + tùy chọn "Chỉ gắn nhãn / Loại bỏ" | `unsure` luôn giữ; "Loại bỏ" chỉ tính Số video sau khi có nhãn |
| S4-5 | Cảnh báo quyền riêng tư lần đầu; bỏ `relevance` khi mode ảnh | Test thứ tự pipeline |
| S4-6 | Đo chất lượng: gắn nhãn tay 100 video/nền tảng, báo cáo precision/recall | Quyết định có bật "Loại bỏ" mặc định không |

### Quyết định mở (mặc định đang áp dụng)
1. **Thứ tự A3 và A4**: mặc định A3 (từ khóa chính xác) trước A4 (tải). Nếu cần tải video dùng ngay thì đổi A4 lên trước A3.
2. **A5 (XHS mở trang chi tiết)**: mặc định tắt vì tăng số lần mở trang, tăng nguy cơ bị chặn. Bật khi cần số comment/lưu đầy đủ cho XHS.
3. **Bằng chứng A1**: cần bạn gửi capture đã xóa cookie/token (hoặc chạy giúp tôi theo README → "Lần chạy đầu").

### Sơ đồ phụ thuộc
`A1 → A2 → A3`; `A1 → A4 → A6`; `A1 → A5`; `A2 → B1/B2/B3 → B4`; `A + B → C`.
