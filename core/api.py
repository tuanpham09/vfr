"""Facade duy nhất mà UI được phép dùng. Core chạy asyncio trong thread riêng."""
from __future__ import annotations

import asyncio
import threading
from typing import Callable

from core.config import Config
from core.events import EventBus
from core.infra.db import Repo
from core.services.task_runner import TaskRunner
from core.services.ws_server import WsServer
from core.types import ScrapeJob, VideoItem


class CoreApi:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.bus = EventBus()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, name="vfr-core", daemon=True)
        self._ready = threading.Event()
        self.repo: Repo | None = None
        self._ws: WsServer | None = None
        self._runner: TaskRunner | None = None

    def subscribe(self, cb: Callable[[object], None]) -> None:
        self.bus.subscribe(cb)

    def start(self) -> None:
        from pathlib import Path
        Path(self.cfg.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.repo = Repo(self.cfg.db_path)
        self._thread.start()
        self._ready.wait(10)
        fut = asyncio.run_coroutine_threadsafe(self._boot(), self._loop)
        fut.result(15)

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    async def _boot(self) -> None:
        assert self.repo is not None
        self._ws = WsServer(self.bus, self.cfg.port, self.cfg.token)
        self._runner = TaskRunner(self._ws, self.repo, self.bus, self.cfg)
        try:
            await self._ws.start()
        except OSError as e:
            self.bus.log(f"Không mở được cổng {self.cfg.port}: {e}", "error")

    def list_videos(self) -> list[VideoItem]:
        return self.repo.list_videos() if self.repo else []

    def start_scrape(self, job: ScrapeJob) -> None:
        assert self._runner is not None
        asyncio.run_coroutine_threadsafe(self._runner.run(job), self._loop)

    def stop(self) -> None:
        if self._runner:
            self._loop.call_soon_threadsafe(self._runner.request_stop)

    def decide(self, decision: str) -> None:
        """decision: resume | skip | stop"""
        if self._runner:
            self._loop.call_soon_threadsafe(self._runner.decide, decision)

    def shutdown(self) -> None:
        if self._ws:
            try:
                asyncio.run_coroutine_threadsafe(self._ws.stop(), self._loop).result(5)
            except Exception:  # noqa: BLE001
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)
        if self.repo:
            self.repo.close()
