# Lints và công cụ ép quy tắc

## pyproject.toml (trích)
```toml
[tool.ruff]
line-length = 100
select = ["E","F","I","B","UP","T20","S","PL","RUF","DTZ","ASYNC"]  # T20 cấm print, DTZ cấm datetime.now() không tz
[tool.mypy]
strict = true
[tool.importlinter]
root_packages = ["app", "core"]

[[tool.importlinter.contracts]]
name = "Layers"
type = "layers"
layers = ["app", "core.api", "core.services", "core.pipeline | core.infra", "core.types | core.config | core.log"]

[[tool.importlinter.contracts]]
name = "Pipeline is pure"
type = "forbidden"
source_modules = ["core.pipeline"]
forbidden_modules = ["core.infra", "core.services", "httpx", "sqlite3", "socket", "requests"]

[[tool.importlinter.contracts]]
name = "UI only via facade"
type = "forbidden"
source_modules = ["app"]
forbidden_modules = ["core.infra", "core.pipeline", "core.services"]
```

## Lint tùy biến (`tools/custom_lints.py`, chạy trong `make check`)
| Rule | Kiểm tra | Thông báo lỗi (mẫu) |
|---|---|---|
| VFR001 | Không có file > 400 dòng | "File quá dài. Tách theo trách nhiệm (xem ARCHITECTURE.md)." |
| VFR002 | Tên model Gemini chỉ xuất hiện trong `core/config.py` | "Dùng `config.LLM_MODEL`." |
| VFR003 | `extension/` không chứa từ khóa nghiệp vụ (`play_count`, `diggCount`, `aweme_id`...) ngoài `adapters/` pattern | "Parse nghiệp vụ phải ở Python normalizer." |
| VFR004 | Mọi chuỗi `[VERIFY]` trong docs có thể liệt kê bằng `make verify-list` | (báo cáo, không fail) |
| VFR005 | Không có `http(s)://` tới tiktok/douyin/xiaohongshu trong `core/` ngoài `core/pipeline/url_builder.py` và downloader | "App không gọi API nền tảng (AGENTS.md #4)." |
| VFR006 | Fixture không chứa pattern bí mật (cookie, `msToken`, `web_session`, API key) | "Chạy tools/scrub_fixture.py." |

## Makefile (đích chính)
`setup`, `check` (ruff → mypy → import-linter → custom_lints → pytest -m "not live"), `test-ext`, `fixtures-check`, `verify-list`, `run`, `package`.

## pre-commit
ruff, ruff-format, gitleaks (bí mật), `make fixtures-check`.
