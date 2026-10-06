import asyncio
import copy
import json
import unittest
from pathlib import Path

from core.events import Log
from core.pipeline.relevance import relevance_score, tokens
from core.pipeline.url_builder import tiktok_handle
from core.types import ScrapeJob, VideoItem
from tests.unit.test_task_runner import fx, make


def vi(**k):
    base = dict(platform="tiktok", video_id="1")
    base.update(k)
    return VideoItem(**base)


class TestRelevance(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(tokens("Kem chống nắng Anessa"), ["kem", "chong", "nang", "anessa"])
        self.assertEqual(tokens("防晒霜测评"), ["防晒", "晒霜", "霜测", "测评"])
        self.assertEqual(tokens("口红 测评"), ["口红", "测评"])
        self.assertEqual(tokens("a ! ,"), [])

    def test_scores(self):
        it = vi(desc="Review kem chống nắng Anessa", hashtags=["skincare"])
        self.assertEqual(relevance_score("kem chống nắng anessa", it), 1.0)
        self.assertEqual(relevance_score("kem chong nang anessa", it), 1.0)   # không dấu vẫn khớp
        self.assertAlmostEqual(relevance_score("kem chống nắng laroche", it), 0.75)
        self.assertEqual(relevance_score("son môi", it), 0.0)
        self.assertEqual(relevance_score("", it), 1.0)

    def test_cjk(self):
        it = vi(platform="douyin", desc="防晒霜 真实 测评 #防晒")
        self.assertGreaterEqual(relevance_score("防晒霜测评", it), 0.75)
        self.assertEqual(relevance_score("口红", it), 0.0)

    def test_phrase_and_signal(self):
        from core.pipeline.relevance import has_signal
        self.assertEqual(relevance_score("绞肉机", vi(platform="douyin", desc="多功能绞肉机 测评")), 1.0)
        self.assertEqual(relevance_score("绞肉机", vi(platform="douyin", desc="碎肉机")), 0.5)  # chung bigram 肉机
        self.assertFalse(has_signal(vi(desc="", hashtags=[])))
        self.assertTrue(has_signal(vi(desc="", hashtags=["x"])))

    def test_hashtag_and_author_count(self):
        it = vi(desc="", hashtags=["anessa"], author_name="Linh")
        self.assertEqual(relevance_score("anessa", it), 1.0)


class TestHandle(unittest.TestCase):
    def test_handle(self):
        self.assertEqual(tiktok_handle("@Linh.Review"), "linh.review")
        self.assertEqual(tiktok_handle("linh.review"), "linh.review")
        self.assertEqual(tiktok_handle("https://www.tiktok.com/@Linh.Review?lang=vi"), "linh.review")
        self.assertEqual(tiktok_handle("https://vm.tiktok.com/abc/"), "")


class TestModes(unittest.IsolatedAsyncioTestCase):
    async def _run(self, job, fixture):
        f = fx(fixture)

        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
                link.emit(type="task_done", task_id=msg["task_id"], reason="idle")
        runner, link, repo, ev = make(script)
        await runner.run(job)
        return repo.list_videos(), ev, link

    async def test_keyword_relevance_filters_offtopic(self):
        vids, ev, _ = await self._run(ScrapeJob("tiktok", "keyword", ["kem chống nắng anessa"], target=10),
                                      "tiktok/search_synthetic.json")
        self.assertEqual([v.video_id for v in vids], ["7300000000000000001"])
        self.assertEqual(vids[0].relevance, 1.0)
        logs = " ".join(e.msg for e in ev if isinstance(e, Log))
        self.assertIn("không sát từ khóa 1", logs)

    async def test_relevance_off(self):
        vids, _, _ = await self._run(ScrapeJob("tiktok", "keyword", ["kem chống nắng anessa"], target=10,
                                               min_relevance=0), "tiktok/search_synthetic.json")
        self.assertEqual(len(vids), 2)

    async def test_all_offtopic_warns(self):
        vids, ev, _ = await self._run(ScrapeJob("tiktok", "keyword", ["son môi"], target=10),
                                      "tiktok/search_synthetic.json")
        self.assertEqual(vids, [])
        self.assertTrue(any(isinstance(e, Log) and e.level == "warn" and "sát từ khóa" in e.msg for e in ev))

    async def test_empty_desc_not_rejected(self):
        # fixture douyin có 1 video hợp lệ, desc "防晒霜测评": từ khóa lạc đề phải loại, desc rỗng phải giữ
        vids, ev, _ = await self._run(ScrapeJob("douyin", "keyword", ["绞肉机"], target=5),
                                      "douyin/search_synthetic.json")
        self.assertEqual(vids, [])   # có desc nhưng lạc đề -> vẫn loại khi min_relevance=0.5

    async def test_tiktok_user_only_that_channel(self):
        vids, ev, link = await self._run(ScrapeJob("tiktok", "user", ["@linh.review"], target=10),
                                         "tiktok/search_synthetic.json")
        self.assertEqual([v.author_id for v in vids], ["linh.review"])
        self.assertIsNone(vids[0].relevance)       # mode user không chấm từ khóa
        sent = [m for m in link.sent if m["type"] == "task"][0]
        self.assertEqual(sent["url"], "https://www.tiktok.com/@linh.review")

    async def test_tiktok_hashtag_url_and_no_filter(self):
        vids, _, link = await self._run(ScrapeJob("tiktok", "hashtag", ["#review"], target=10),
                                        "tiktok/search_synthetic.json")
        self.assertEqual(len(vids), 2)
        self.assertEqual([m for m in link.sent if m["type"] == "task"][0]["url"],
                         "https://www.tiktok.com/tag/review")

    async def test_link_mode_takes_one(self):
        vids, _, link = await self._run(ScrapeJob("tiktok", "link", ["https://www.tiktok.com/@a/video/1"],
                                                  target=50), "tiktok/search_synthetic.json")
        self.assertEqual(len(vids), 1)

    async def test_bad_input_logged_not_crash(self):
        vids, ev, link = await self._run(ScrapeJob("douyin", "user", ["abc"], target=5),
                                         "douyin/search_synthetic.json")
        self.assertEqual(vids, [])
        self.assertTrue(any(isinstance(e, Log) and e.level == "error" for e in ev))


if __name__ == "__main__":
    unittest.main()
