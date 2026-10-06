# ADR-004 — PySide6, core asyncio ở QThread riêng
**Quyết định:** UI PySide6; core (WS, runner, downloader, LLM) chạy asyncio trong thread riêng, giao tiếp bằng EventBus + Qt signal.
**Lý do:** UI mượt; core tách khỏi Qt nên sau này chạy headless/FastAPI mà không đổi logic.
