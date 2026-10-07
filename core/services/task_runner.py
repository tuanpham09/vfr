"""Điều phối cào: gửi task cho extension, nhận payload, normalize → dedupe → lọc → lưu → phát event."""
from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable, Protocol

from core.config import Config
from core.events import EventBus, JobState, Paused, Progress, VideoUpsert
from core.infra.db import Repo
from core.pipeline.filters import hashtag_matches, passes
from core.pipeline.normalizers import normalize
from core.pipeline.relevance import has_signal, measurable, relevance_score
from core.pipeline.url_builder import build_url, tiktok_handle
from core.types import PLATFORM_LABEL, ScrapeJob, VideoItem


def _is_dom_api(api: str) -> bool:
    return (api or "").startswith("dom://")


def _has_any_stat(it: VideoItem) -> bool:
    """True nếu có ít nhất một số liệu (phân biệt 0 với None)."""
    return it.like is not None or it.comment is not None or it.collect is not None or it.share is not None


class ExtLink(Protocol):
    connected: bool
    on_message: Callable[[dict], None] | None

    async def send(self, msg: dict) -> None: ...


@dataclass
class _Cur:
    id: str
    platform: str
    mode: str
    input: str
    url: str
    target: int
    got: int = 0
    seen: dict[str, str] = field(default_factory=dict)  # video_id -> "dom" | "api"
    counted: set[str] = field(default_factory=set)
    rejected: int = 0
    rej: dict = field(default_factory=lambda: {"bộ lọc": 0, "sai hashtag": 0, "sai kênh": 0, "không sát từ khóa": 0})
    handle: str = ""
    reason: str = ""
    shown: int = 0
    skip_rel_logged: bool = False
    done: asyncio.Event = field(default_factory=asyncio.Event)


class TaskRunner:
    def __init__(self, link: ExtLink, repo: Repo, bus: EventBus, cfg: Config,
                 sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
                 rand: Callable[[float, float], float] = random.uniform) -> None:
        self.link, self.repo, self.bus, self.cfg = link, repo, bus, cfg
        self._sleep, self._rand = sleep, rand
        self._cur: _Cur | None = None
        self._job: ScrapeJob | None = None
        self._stop = False
        self._decision: asyncio.Future[str] | None = None
        self._capture_n = 0
        self.busy = False
        link.on_message = self.on_message

    # ---------- điều khiển từ UI ----------
    def request_stop(self) -> None:
        self._stop = True
        if self._decision and not self._decision.done():
            self._decision.set_result("stop")
        if self._cur and not self._cur.done.is_set():
            self._cur.reason = "stopped"
            self._cur.done.set()
            asyncio.ensure_future(self._safe_send({"type": "stop", "task_id": self._cur.id}))

    def decide(self, decision: str) -> None:
        if self._decision and not self._decision.done():
            self._decision.set_result(decision)

    # ---------- chạy job ----------
    async def run(self, job: ScrapeJob) -> None:
        if self.busy:
            self.bus.log("Đang có job chạy", "warn")
            return
        self.busy, self._stop, self._job = True, False, job
        self.bus.publish(JobState("running"))
        try:
            if not self.link.connected:
                self.bus.log("Chưa kết nối Chrome extension. Hãy mở Chrome có cài extension.", "error")
                self.bus.publish(JobState("error", "no_extension"))
                return
            total = len(job.inputs)
            for idx, text in enumerate(job.inputs):
                if self._stop:
                    break
                await self._run_one(job, idx, total, text)
                if idx < total - 1 and not self._stop:
                    d = self._rand(self.cfg.task_delay_min, self.cfg.task_delay_max)
                    self.bus.log(f"Nghỉ {d:.0f}s trước mục tiếp theo (giữ nhịp tự nhiên)")
                    await self._sleep(d)
            self.bus.publish(JobState("stopped" if self._stop else "done"))
        finally:
            self.busy, self._cur = False, None

    async def _run_one(self, job: ScrapeJob, idx: int, total: int, text: str) -> None:
        label = PLATFORM_LABEL.get(job.platform, job.platform)
        try:
            url = build_url(job.platform, job.mode, text)
        except ValueError as e:
            self.bus.log(f"Bỏ qua '{text}': {e}", "error")
            return
        cur = _Cur(id=uuid.uuid4().hex[:8], platform=job.platform, mode=job.mode, input=text,
                   url=url, target=1 if job.mode == "link" else job.target)
        if job.mode == "user" and job.platform == "tiktok":
            cur.handle = tiktok_handle(text)
        self._cur = cur
        self.bus.log(f"[{label}] Bắt đầu mục {idx + 1}/{total}: {text}")
        resume = False
        while True:
            reason = await self._execute(cur, resume)
            if reason in ("login_required", "captcha"):
                self.bus.publish(Paused(reason, job.platform, text, url))
                self._decision = asyncio.get_running_loop().create_future()
                decision = await self._decision
                self._decision = None
                if decision == "resume":
                    resume = True
                    continue
                self.bus.log(f"Bỏ qua mục '{text}' ({reason})", "warn")
            break
        detail = ", ".join(f"{k} {v}" for k, v in cur.rej.items() if v)
        self.bus.log(f"[{label}] Xong '{text}': {cur.got}/{cur.target} video "
                     f"(loại {cur.rejected}{': ' + detail if detail else ''}) — dừng: {cur.reason or 'n/a'}")
        if cur.got == 0 and cur.rej["không sát từ khóa"] and cur.rej["không sát từ khóa"] == cur.rejected:
            self.bus.log("Mọi video bị loại vì không sát từ khóa. Thử hạ 'Độ sát từ khóa' hoặc dùng từ khóa "
                         "đúng ngôn ngữ của nền tảng (Douyin/XHS: tiếng Trung).", "warn")

    async def _execute(self, cur: _Cur, resume: bool) -> str:
        cur.done.clear()
        cur.reason = ""
        if resume:
            await self._safe_send({"type": "resume", "task_id": cur.id, "url": cur.url,
                                   "max_scrolls": self.cfg.max_scrolls})
        else:
            await self._safe_send({
                "type": "task", "task_id": cur.id, "platform": cur.platform, "mode": cur.mode,
                "query": cur.input, "url": cur.url, "max_scrolls": self.cfg.max_scrolls,
                "idle_limit": self.cfg.idle_limit,
            })
        timeout = self.cfg.max_scrolls * 8 + 90
        try:
            await asyncio.wait_for(cur.done.wait(), timeout)
        except asyncio.TimeoutError:
            cur.reason = "timeout"
            await self._safe_send({"type": "stop", "task_id": cur.id})
            self.bus.log("Hết thời gian chờ extension", "warn")
        if cur.reason == "target":
            await self._safe_send({"type": "stop", "task_id": cur.id})
        return cur.reason

    async def _safe_send(self, msg: dict) -> None:
        try:
            await self.link.send(msg)
        except Exception as e:  # noqa: BLE001
            self.bus.log(f"Không gửi được tới extension: {e}", "error")
            if self._cur and not self._cur.done.is_set():
                self._cur.reason = "ext_error"
                self._cur.done.set()

    # ---------- nhận từ extension ----------
    def on_message(self, msg: dict) -> None:
        cur = self._cur
        if not cur or msg.get("task_id") != cur.id or self._job is None:
            return
        t = msg.get("type")
        if t in ("captured", "state"):
            self._on_payload(cur, self._job, msg)
        elif t == "task_done":
            if not cur.done.is_set():
                cur.reason = str(msg.get("reason", "done"))
                cur.done.set()
        elif t == "progress":
            self.bus.publish(Progress(cur.got, cur.target, cur.input, 0, 0))

    def _on_payload(self, cur: _Cur, job: ScrapeJob, msg: dict) -> None:
        if cur.done.is_set():
            return
        api = str(msg.get("api") or msg.get("type"))
        if cur.platform == "douyin" and cur.mode == "keyword":
            if any(k in api.lower() for k in ("aweme/favorite", "solution/resource", "suggest_words",
                                              "/feed/", "recommend", "related")):
                return
        payload = msg.get("payload")
        if self.cfg.save_raw_captures:
            self._dump(cur.platform, api, payload)
        items = normalize(cur.platform, api, payload)
        self.bus.log(f"  nhận {msg.get('type')} {api[:90]} -> {len(items)} video")  # tạm: chẩn đoán hook Douyin
        if not items:
            return
        new_n = 0
        src = "dom" if _is_dom_api(api) else "api"
        for it in items:
            if cur.got >= cur.target:
                break
            if it.video_id in cur.seen:
                old_src = cur.seen[it.video_id]
                if src == "dom" and old_src == "api":
                    continue  # DOM không được đè số thật của API
                if src == "dom" and old_src == "dom" and not _has_any_stat(it):
                    continue  # DOM rác lặp lại, tránh write vô ích
                if it.video_id in cur.counted:
                    # Đã tính vào target: chạy lại bộ lọc trước khi cập nhật số
                    # liệu — nếu không video từng bị loại vẫn hiện UI.
                    if self._fails_filters(it, cur, job):
                        continue
                    if src == "api":
                        cur.seen[it.video_id] = "api"
                    merged, _ = self.repo.upsert(it)
                    self.bus.publish(VideoUpsert(merged, False))
                    continue
                # Chưa tính (discovery DOM hoặc từng bị loại): cho đi qua
                # bộ lọc bình thường để nâng cấp lên bản API.
                if src == "api":
                    cur.seen[it.video_id] = "api"
            else:
                cur.seen[it.video_id] = src
            if cur.mode == "hashtag" and cur.platform != "tiktok" and not hashtag_matches(it, cur.input):
                self._reject(cur, "sai hashtag")
                continue
            if cur.handle and it.author_id and it.author_id.lower() != cur.handle:
                self._reject(cur, "sai kênh")
                continue
            if cur.mode == "keyword" and has_signal(it):
                if not measurable(cur.input, cur.platform):
                    if job.min_relevance > 0 and not cur.skip_rel_logged:
                        cur.skip_rel_logged = True
                        self.bus.log(
                            "Từ khóa không có chữ Hán nên không so được với mô tả tiếng Trung: "
                            "bỏ qua lọc 'sát từ khóa' (bật dịch máy để dịch sang tiếng Trung).",
                            "warn",
                        )
                else:
                    it.relevance = relevance_score(cur.input, it)
                    if job.min_relevance > 0 and it.relevance < job.min_relevance:
                        if cur.shown < 3:
                            cur.shown += 1
                            self.bus.log(
                                f"Loại (sát {it.relevance:.0%} < {job.min_relevance:.0%}): "
                                f"{(it.desc or '(không mô tả)')[:50]}",
                                "warn",
                            )
                        self._reject(cur, "không sát từ khóa")
                        continue
            ok, why = passes(it, job)
            if not ok:
                self._reject(cur, "bộ lọc")
                continue
            if src == "dom" and not _has_any_stat(it):
                # DOM discovery thiếu số liệu: bỏ hẳn (không lưu DB, không hiện UI,
                # không tính target) — chờ bản API thật tới qua đường nâng cấp.
                # Nếu không, bảng sẽ hiện video mà log vẫn báo 0/N.
                continue
            it.query, it.task_id = cur.input, cur.id
            merged, is_new = self.repo.upsert(it)
            if it.video_id not in cur.counted:
                cur.counted.add(it.video_id)
                cur.got += 1
                new_n += 1 if is_new else 0
            self.bus.publish(VideoUpsert(merged, is_new))
        if new_n or items:
            self.bus.publish(Progress(cur.got, cur.target, cur.input, 0, 0))
        if cur.got >= cur.target and not cur.done.is_set():
            cur.reason = "target"
            cur.done.set()  # _execute sẽ gửi `stop` cho extension sau khi thức dậy

    def _fails_filters(self, it: VideoItem, cur: _Cur, job: ScrapeJob) -> bool:
        """Chạy lại bộ lọc cho bản cập nhật số liệu (không chạm đếm rejected).

        Video đã tính vào target nhưng bản API mới về vẫn phải đạt hashtag /
        kênh / relevance / passes như lần đầu — nếu không video từng bị loại
        vẫn hiện UI với attribution cũ.
        """
        if cur.mode == "hashtag" and cur.platform != "tiktok" and not hashtag_matches(it, cur.input):
            return True
        if cur.handle and it.author_id and it.author_id.lower() != cur.handle:
            return True
        if cur.mode == "keyword" and has_signal(it) and measurable(cur.input, cur.platform):
            it.relevance = relevance_score(cur.input, it)
            if job.min_relevance > 0 and it.relevance < job.min_relevance:
                return True
        ok, _ = passes(it, job)
        return not ok

    @staticmethod
    def _reject(cur: _Cur, why: str) -> None:
        cur.rejected += 1
        cur.rej[why] += 1

    def _dump(self, platform: str, api: str, payload: object) -> None:
        try:
            d = Path(self.cfg.captures_dir)
            d.mkdir(parents=True, exist_ok=True)
            self._capture_n += 1
            p = d / f"{platform}_{int(time.time())}_{self._capture_n:04d}.json"
            p.write_text(json.dumps({"api": api, "payload": payload}, ensure_ascii=False),
                         encoding="utf-8")
        except OSError as e:
            self.bus.log(f"Không lưu được capture: {e}", "warn")
