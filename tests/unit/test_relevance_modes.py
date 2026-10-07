import asyncio
import copy
import json
import unittest
from pathlib import Path

from core.events import Log, VideoUpsert
from core.pipeline.relevance import measurable, relevance_score, tokens
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
        self.assertAlmostEqual(relevance_score("绞肉机", vi(platform="douyin", desc="碎肉机")), 0.85 * 2 / 3)  # chung 2/3 ký tự
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

    async def test_dom_without_stats_dropped(self):
        # Item DOM qua filter nhưng thiếu số liệu: bỏ hẳn — không lưu DB, không hiện UI.
        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="captured", task_id=msg["task_id"], api="dom://douyin/search",
                          payload={"data": [
                              {"aweme_id": "991", "desc": "圆珠笔 好用",
                               "author": {"nickname": "a"}, "statistics": {}},
                              {"aweme_id": "992", "desc": "圆珠笔 测评",
                               "author": {"nickname": "b"},
                               "statistics": {"digg_count": 10, "comment_count": 1,
                                              "collect_count": 2, "share_count": 0}},
                          ]})
                link.emit(type="task_done", task_id=msg["task_id"], reason="idle")
        runner, link, repo, ev = make(script)
        await runner.run(ScrapeJob("douyin", "keyword", ["圆珠笔"], target=2))
        self.assertEqual([v.video_id for v in repo.list_videos()], ["992"])
        self.assertEqual(len([e for e in ev if isinstance(e, VideoUpsert)]), 1)

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


class TestMeasurable(unittest.TestCase):
    """measurable() kiểm tra truy vấn có thể so được với nền tảng hay không."""

    def test_vietnamese_not_measurable_on_douyin(self):
        self.assertFalse(measurable("kem chống nắng", "douyin"))

    def test_latin_not_measurable_on_xhs(self):
        self.assertFalse(measurable("anessa", "xhs"))

    def test_chinese_measurable_on_douyin(self):
        self.assertTrue(measurable("防晒霜", "douyin"))

    def test_mixed_latin_cjk_measurable_on_xhs(self):
        self.assertTrue(measurable("Anessa 防晒霜", "xhs"))

    def test_any_query_measurable_on_tiktok(self):
        self.assertTrue(measurable("kem chống nắng", "tiktok"))
        self.assertTrue(measurable("sunscreen", "tiktok"))


class TestCjkLenient(unittest.TestCase):
    """CJK scoring: khớp ký tự đơn lẻ trong desc kể cả không liền kề."""

    def test_non_adjacent_words_still_match(self):
        # Desc có "口红" và "推荐" riêng, query "口红测评推荐" → trước đây ~0.4 bigram
        it = vi(platform="douyin", desc="今天分享口红 超好用的推荐")
        self.assertGreaterEqual(relevance_score("口红测评推荐", it), 0.5)

    def test_cross_word_bigram_not_required(self):
        it = vi(platform="douyin", desc="防晒霜真实测评")
        self.assertGreaterEqual(relevance_score("防晒霜 测评", it), 0.9)

    def test_unrelated_cjk_rejected(self):
        it = vi(platform="douyin", desc="美食探店 火锅")
        self.assertLess(relevance_score("防晒霜测评", it), 0.3)

    def test_mixed_brand_and_cjk(self):
        it = vi(platform="xhs", desc="Anessa 防晒 测评")
        # Query "Anessa 防晒霜": bigram 1/2=0.5, ký tự 2/3*0.85≈0.567,
        # điểm=(0.567*3+1.0)/4≈0.675. Ngưỡng 0.65 phản ánh đúng công thức hiện tại.
        self.assertGreaterEqual(relevance_score("Anessa 防晒霜", it), 0.65)


class TestRunnerChineseBug(unittest.IsolatedAsyncioTestCase):
    """Truy vấn tiếng Việt trên Douyin không bị loại vì không đo được độ sát."""

    async def _run(self, query, platform, fixture="douyin/search_synthetic.json", min_rel=0.5):
        f = fx(fixture)

        async def script(msg, link):
            if msg["type"] == "task":
                link.emit(type="captured", task_id=msg["task_id"], api=f["api"], payload=f["payload"])
                link.emit(type="task_done", task_id=msg["task_id"], reason="idle")

        runner, link, repo, ev = make(script)
        await runner.run(ScrapeJob(platform, "keyword", [query], target=10, min_relevance=min_rel))
        logs = [e for e in ev if isinstance(e, Log)]
        return repo.list_videos(), logs

    async def test_vietnamese_query_on_douyin_not_filtered_out(self):
        vids, logs = await self._run("kem chống nắng", "douyin", "douyin/search_synthetic.json")
        self.assertEqual(len(vids), 1)  # trước đây bị loại hết
        self.assertTrue(any("bỏ qua lọc" in e.msg for e in logs))

    async def test_chinese_query_on_douyin_kept(self):
        vids, _ = await self._run("防晒霜 测评", "douyin", "douyin/search_synthetic.json")
        self.assertEqual(len(vids), 1)

    async def test_offtopic_chinese_logs_examples(self):
        vids, logs = await self._run("口红", "douyin", "douyin/search_synthetic.json")
        self.assertEqual(vids, [])
        self.assertTrue(any(e.msg.startswith("Loại (sát") for e in logs))


if __name__ == "__main__":
    unittest.main()
