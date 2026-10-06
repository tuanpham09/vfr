# AGENTS.md — Video Flow Render (VFR)

Bản đồ ngắn. Chi tiết nằm trong `docs/` (đọc theo nhu cầu, đừng đọc hết).

## Dự án là gì
App desktop (PySide6) + Chrome extension (MV3) cào video review sản phẩm từ **TikTok, Douyin, Xiaohongshu** để nghiên cứu nội dung. Không có Facebook, không có tab Auto/Xử lý/Review trong MVP.

## Đọc gì trước khi làm việc
| Việc | Đọc |
|---|---|
| Hiểu sản phẩm, UI, tiêu chí | `docs/product/SPEC.md` |
| Kiến trúc, quy tắc phụ thuộc lớp | `docs/ARCHITECTURE.md` |
| Giao thức App ↔ Extension | `docs/protocol/WS_PROTOCOL.md` |
| Schema `VideoItem`, DB | `docs/design/DATA_MODEL.md` |
| Sinh từ khóa bằng Gemini | `docs/design/KEYWORD_LLM.md` |
| Lọc, face detect, badge | `docs/design/FILTERS_AND_FACE.md` |
| Chống bot, tốc độ | `docs/design/ANTI_DETECTION.md` |
| Từng nền tảng | `docs/platforms/{tiktok,douyin,xhs}.md` |
| Cách test, fixtures, lint | `docs/harness/*.md` |
| Việc đang làm | `docs/plans/ROADMAP.md`, `docs/plans/active/` |
| Vì sao chọn như vậy | `docs/decisions/` |

## Lệnh chuẩn (phải chạy được trước khi báo xong)
```
make setup      # venv + deps + pre-commit
make check      # ruff + mypy --strict + import-linter + pytest (nhanh, offline)
make test-ext   # test JS của extension (vitest)
make run        # chạy app
make fixtures-check   # kiểm tra fixtures hợp lệ, không chứa token/cookie
```
**Một việc chỉ xong khi `make check` xanh.** Đọc thông báo lỗi lint: nó chứa hướng dẫn sửa.

## Quy tắc vàng (vi phạm = lint/test fail)
1. **Extension không có logic nghiệp vụ.** Chỉ hook, scroll, phát hiện login/captcha, chuyển tiếp. Parse/lọc/dedupe chỉ ở Python.
2. **Normalizer là hàm thuần**: `dict -> list[VideoItem]`, không IO, không network, không thời gian hiện tại.
3. **Mọi JSON từ nền tảng được parse ở biên** bằng Pydantic. Không truyền `dict` thô qua các lớp.
4. **App không tự gọi API của TikTok/Douyin/XHS.** Chỉ extension duyệt web. (Trừ tải file media đã có URL.)
5. **Không dùng `print`**; dùng `loguru` qua `core.log`.
6. **Không hardcode** selector, URL pattern, tên cookie, tên model: nằm trong `adapters/` hoặc `config`.
7. **Test không chạm mạng.** Dùng fixtures trong `tests/fixtures/`. Không commit cookie/token thật.
8. **UI không import trực tiếp lớp thấp**; chỉ qua `core.api` (facade).
9. Mỗi quyết định kiến trúc mới → thêm ADR ngắn trong `docs/decisions/`.

## Khi không chắc
Tên trường JSON, selector, tên cookie trong docs được đánh dấu **`[VERIFY]`**. Đừng đoán: thu thập response thật vào fixtures (xem `docs/harness/FIXTURES.md`), rồi sửa docs + code cùng một commit.

## Định nghĩa "xong"
Code + test + docs cập nhật + `make check` xanh + mục tương ứng trong `docs/QUALITY.md` cập nhật.
