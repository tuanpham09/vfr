# Architecture

```
PySide6 UI ──► core.api (facade) ──► services ──► normalizers/filters/face ──► types
                                         │                                      ▲
                                  ws_server ◄──► Chrome Extension               │
                                         └──► db (SQLite), downloader, llm ─────┘
```

## Lớp (trên → dưới, chỉ được import xuống dưới)
| # | Package | Trách nhiệm |
|---|---|---|
| 5 | `app/` | PySide6: cửa sổ, tab, table model. Chỉ import `core.api`, `core.types` |
| 4 | `core/api.py` | Facade: `start_scrape`, `stop`, `resume`, `list_videos`, `subscribe(events)` |
| 3 | `core/services/` | `task_runner`, `ws_server`, `download_service`, `keyword_service` |
| 2 | `core/pipeline/` | `normalizers/`, `filters.py`, `face_detect.py`, `relevance.py` (thuần) |
| 2 | `core/infra/` | `db.py`, `downloader.py`, `llm_gemini.py`, `ffmpeg.py` |
| 1 | `core/types.py`, `core/config.py`, `core/log.py` | Pydantic models, enum, settings |

Ràng buộc bổ sung (import-linter, xem `harness/LINTS.md`):
- `core.pipeline` **không** import `core.infra`, `core.services`, `httpx`, `sqlite3`, `socket`, `datetime.now`.
- `app` không import `core.infra`, `core.pipeline`, `core.services`.
- Không có import vòng.

## Luồng sự kiện
Services phát event (`VideoAdded`, `VideoUpdated`, `TaskStateChanged`, `Log`, `ExtStatus`) qua `EventBus` (asyncio). UI nhận qua Qt signal bridge trong `app/bridge.py`. UI không polling.

## Concurrency
- Một event loop asyncio trong `QThread` riêng chạy: WS server, task runner, downloader, LLM call.
- Face detect (CPU) chạy `run_in_executor` (ThreadPool, size 2).
- DB: một writer, ghi batch 50 dòng hoặc 1 giây.
- UI thread không làm IO, không decode ảnh nặng (thumbnail load qua worker + cache LRU).

## Thư mục
```
vfr/
├─ app/{main.py,main_window.py,bridge.py,tabs/,models/}
├─ core/{api.py,types.py,config.py,log.py,events.py}
│  ├─ services/{task_runner.py,ws_server.py,download_service.py,keyword_service.py}
│  ├─ pipeline/{normalizers/{tiktok,douyin,xhs}.py,filters.py,face_detect.py,relevance.py}
│  └─ infra/{db.py,downloader.py,llm_gemini.py,ffmpeg.py}
├─ extension/{manifest.json,background.js,content.js,inject.js,adapters/{tiktok,douyin,xhs}.js,lib/}
├─ tests/{unit/,integration/,ext/,fixtures/{tiktok,douyin,xhs}/}
├─ tools/{capture_fixture.md,scrub_fixture.py,check_fixtures.py}
├─ docs/  AGENTS.md  Makefile  pyproject.toml
```

## Tech stack
PySide6 · websockets · SQLModel/SQLite · httpx (+ yt-dlp fallback TikTok) · imageio-ffmpeg · opencv-python-headless (YuNet ONNX) · jieba + rapidfuzz + OpenCC (relevance dạng luật) · google-genai (Gemini) · loguru · pytest + pytest-asyncio · ruff · mypy · import-linter · vitest (extension) · PyInstaller.
