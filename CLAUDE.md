# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make setup          # tạo venv + cài deps + pre-commit
make check          # ruff + ruff format + mypy --strict + import-linter + custom_lints + pytest (không mạng)
make test-ext       # vitest cho extension JS
make fixtures-check # kiểm tra fixture: JSON hợp lệ, không bí mật, có trong INDEX
make verify-list    # liệt kê các mục [VERIFY] trong docs
make run            # chạy app (python -m app.main)
make package        # đóng gói PyInstaller
```

Chạy một test đơn lẻ:
```bash
pytest tests/unit/test_filters_urls_db.py -q
pytest tests/unit/test_task_runner.py::test_foo -q
```

**Một việc chỉ xong khi `make check` xanh.**

## Kiến trúc

```
PySide6 UI ──► core.api (facade) ──► services ──► normalizers/filters ──► types
                                          │
                                   ws_server ◄──► Chrome Extension (MV3)
                                          └──► db (SQLite), downloader, llm
```

### Lớp (chỉ được import xuống):
| Lớp | Package | Ghi chú |
|---|---|---|
| 5 | `app/` | PySide6 UI; chỉ import `core.api`, `core.types` |
| 4 | `core/api.py` | Facade duy nhất của UI: `start_scrape`, `stop`, `decide`, `list_videos`, `subscribe` |
| 3 | `core/services/` | `task_runner`, `ws_server`, `download_service`, `keyword_service` |
| 2 | `core/pipeline/` | `normalizers/`, `filters.py`, `relevance.py` — **thuần, không IO** |
| 2 | `core/infra/` | `db.py`, `downloader.py`, `llm_gemini.py` |
| 1 | `core/types.py`, `core/config.py`, `core/log.py` | Pydantic models, enum, settings |

**Import-linter ép cứng các ràng buộc này — vi phạm sẽ fail `make check`.**

### Concurrency
- Một asyncio event loop chạy trong `QThread` riêng (không phải thread UI).
- UI nhận event qua `EventBus` → `app/bridge.py` (Qt signal bridge). UI không polling.
- DB ghi batch (50 dòng hoặc 1 giây), một writer duy nhất.

### Extension ↔ App
WebSocket `ws://127.0.0.1:{port}`, mọi message là JSON có `type`. Extension chỉ hook/scroll/forward — **không parse nghiệp vụ**. Parse chỉ ở Python normalizers.

## Quy tắc cốt lõi

1. **Extension không có logic nghiệp vụ.** Chỉ hook, scroll, phát hiện login/captcha, chuyển tiếp. Parse/lọc/dedupe chỉ ở Python.
2. **Normalizer là hàm thuần**: `(api: str, payload: object) -> list[VideoItem]` — không IO, không network.
3. **Mọi JSON từ nền tảng được parse ở biên** bằng Pydantic. Không truyền `dict` thô qua các lớp.
4. **App không tự gọi API nền tảng.** Chỉ extension duyệt web (ngoại trừ tải media có URL sẵn).
5. **Không dùng `print`** — dùng `loguru` qua `core.log`.
6. **Không hardcode** selector, URL pattern, tên cookie, tên model: đặt trong `adapters/` hoặc `config`.
7. **Test không chạm mạng.** Dùng fixtures trong `tests/fixtures/`.

## Lint tự động (fail `make check`)

| Rule | Nội dung |
|---|---|
| VFR001 | Không file > 400 dòng |
| VFR002 | Tên model Gemini chỉ xuất hiện trong `core/config.py` |
| VFR003 | `extension/` không chứa từ khóa parse nghiệp vụ ngoài `adapters/` |
| VFR005 | Không có URL `http(s)://tiktok/douyin/xhs` trong `core/` ngoài `url_builder.py` và downloader |
| VFR006 | Fixture không chứa cookie/token thật |
| T20 (ruff) | Cấm `print` |
| DTZ (ruff) | Cấm `datetime.now()` không timezone |

## Trường đánh dấu `[VERIFY]`

Tên trường JSON, selector, cookie trong docs được đánh dấu `[VERIFY]` khi chưa kiểm chứng bằng dữ liệu thật. Khi gặp `[VERIFY]`: thu fixture thật → chạy `tools/scrub_fixture.py` → cập nhật normalizer + docs trong cùng một commit.

## Fixtures

Vị trí: `tests/fixtures/{tiktok,douyin,xhs}/{mode}_{yyyymmdd}_{n}.json`

Quy trình thêm fixture:
1. Thu response thật (extension DevTools hoặc chế độ "Lưu JSON thô").
2. Chạy `python tools/scrub_fixture.py <file>` (xóa bí mật).
3. Thêm dòng vào `tests/fixtures/INDEX.md`.
4. `make fixtures-check` phải xanh trước khi commit.

## Khi thêm normalizer mới hoặc sửa

- Mỗi normalizer test với ≥ 3 fixture thật (có giỏ hàng, không giỏ hàng, thiếu trường).
- Normalizer nằm ở `core/pipeline/normalizers/{platform}.py`, chữ ký: `normalize(api: str, payload: object) -> list[VideoItem]`.
- `VideoItem.relevance` chỉ được gán ở `task_runner`, không phải trong normalizer.

## Quyết định kiến trúc quan trọng

- **ADR-001**: Extension-first (app không gọi trực tiếp API nền tảng).
- **ADR-002**: Không dùng embedding — relevance chỉ dùng luật (bigram CJK + Latin word match).
- **ADR-004**: PySide6 + asyncio trong QThread riêng (không `qasync`).
- **ADR-005**: `VideoItem` là stdlib `dataclass` (không Pydantic) để tránh overhead ở pipeline.

## Định nghĩa "xong"

Code + test + docs cập nhật + `make check` xanh + mục tương ứng trong `docs/QUALITY.md` cập nhật.
