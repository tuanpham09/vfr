import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from core.config import Config
from core.events import EventBus, Paused, VideoUpsert
from core.infra.db import Repo
from core.services.task_runner import TaskRunner
from core.types import ScrapeJob

FX = Path(__file__).resolve().parents[1] / "fixtures"


def fx(p):
    return json.loads((FX / p).read_text(encoding="utf-8"))


class FakeLink:
    """Giả lập extension: kịch bản là hàm async nhận (msg, link)."""

    def __init__(self, script):
        self.connected = True
        self.on_message = None
        self.sent = []
        self.script = script

    async def send(self, msg):
        self.sent.append(msg)
        asyncio.get_running_loop().create_task(self.script(msg, self))

    def emit(self, **m):
        self.on_message(m)


def make(script, **cfgkw):
    d = tempfile.mkdtemp()
    cfg = Config(db_path=str(Path(d) / "t.db"), captures_dir=str(Path(d) / "cap"), task_delay_min=0,
                 task_delay_max=0, **cfgkw)
    bus, repo = EventBus(), Repo(cfg.db_path)
    events = []
    bus.subscribe(events.append)
    link = FakeLink(script)

    async def nosleep(_):
        return None

    return TaskRunner(link, repo, bus, cfg, sleep=nosleep, rand=lambda a, b: 0), link, repo, events


class TestRunner(unittest.IsolatedAsyncioTestCase):
    async def test_stops_at_target_and_sends_stop(self):
        f = fx("tiktok/search_synthetic.json")

        async def script(msg, link):
            if msg["type"] == "task":
                await asyncio.sleep(0)
                link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
        runner, link, repo, ev = make(script)
        job = ScrapeJob("tiktok", "keyword", ["kem chống nắng"], target=1)
        await runner.run(job)
        ups = [e for e in ev if isinstance(e, VideoUpsert)]
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0].item.play, 1234567)
        self.assertTrue(any(m["type"] == "stop" for m in link.sent))
        self.assertEqual(len(repo.list_videos()), 1)

    async def test_dedupe_and_min_filter(self):
        f = fx("tiktok/search_synthetic.json")

        async def script(msg, link):
            if msg["type"] == "task":
                for _ in range(2):  # cùng payload gửi 2 lần
                    link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
                link.emit(type="task_done", task_id=msg["task_id"], reason="idle")
        runner, link, repo, ev = make(script)
        await runner.run(ScrapeJob("tiktok", "keyword", ["a"], target=10, min_metric=100))
        self.assertEqual(len(repo.list_videos()), 1)  # video 2 có 0 view bị loại

    async def test_login_pause_then_resume(self):
        f = fx("xhs/search_synthetic.json")
        state = {"n": 0}

        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="task_done", task_id=msg["task_id"], reason="login_required")
            elif msg["type"] == "resume":
                state["n"] += 1
                link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
                link.emit(type="task_done", task_id=msg["task_id"], reason="idle")
        runner, link, repo, ev = make(script)
        t = asyncio.create_task(runner.run(ScrapeJob("xhs", "keyword", ["防晒"], target=5)))
        for _ in range(100):
            await asyncio.sleep(0.01)
            if any(isinstance(e, Paused) for e in ev):
                break
        paused = [e for e in ev if isinstance(e, Paused)]
        self.assertEqual(paused[0].reason, "login_required")
        runner.decide("resume")
        await asyncio.wait_for(t, 5)
        self.assertEqual(state["n"], 1)
        self.assertEqual(len(repo.list_videos()), 1)

    async def test_login_skip(self):
        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="task_done", task_id=msg["task_id"], reason="login_required")
        runner, link, repo, ev = make(script)
        t = asyncio.create_task(runner.run(ScrapeJob("douyin", "keyword", ["a", "b"], target=5)))
        for _ in range(200):
            await asyncio.sleep(0.01)
            if sum(isinstance(e, Paused) for e in ev) >= 1:
                runner.decide("skip")
                break
        for _ in range(200):
            await asyncio.sleep(0.01)
            if sum(isinstance(e, Paused) for e in ev) >= 2:
                runner.decide("skip")
                break
        await asyncio.wait_for(t, 5)
        self.assertEqual(sum(isinstance(e, Paused) for e in ev), 2)

    async def test_hashtag_filter_douyin(self):
        f = fx("douyin/search_synthetic.json")

        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
                link.emit(type="task_done", task_id=msg["task_id"], reason="idle")
        runner, link, repo, ev = make(script)
        await runner.run(ScrapeJob("douyin", "hashtag", ["不存在的标签"], target=5))
        self.assertEqual(len(repo.list_videos()), 0)
        runner2, _, repo2, _ = make(script)
        await runner2.run(ScrapeJob("douyin", "hashtag", ["防晒"], target=5))
        self.assertEqual(len(repo2.list_videos()), 1)

    async def test_user_stop(self):
        async def script(msg, link):
            pass  # extension "treo"
        runner, link, repo, ev = make(script)
        t = asyncio.create_task(runner.run(ScrapeJob("tiktok", "keyword", ["a"], target=5)))
        await asyncio.sleep(0.05)
        runner.request_stop()
        await asyncio.wait_for(t, 5)
        self.assertTrue(any(m["type"] == "stop" for m in link.sent))

    async def test_no_extension(self):
        runner, link, repo, ev = make(lambda m, l: asyncio.sleep(0))
        link.connected = False
        await runner.run(ScrapeJob("tiktok", "keyword", ["a"]))
        self.assertEqual(link.sent, [])

    async def test_saves_raw_captures(self):
        f = fx("tiktok/search_synthetic.json")

        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
        runner, link, repo, ev = make(script, save_raw_captures=True)
        await runner.run(ScrapeJob("tiktok", "keyword", ["a"], target=1))
        self.assertEqual(len(list(Path(runner.cfg.captures_dir).glob("tiktok_*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
