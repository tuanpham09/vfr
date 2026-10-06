import json
import unittest
from pathlib import Path

from core.pipeline.normalizers import normalize

FX = Path(__file__).resolve().parents[1] / "fixtures"


def load(p):
    d = json.loads((FX / p).read_text(encoding="utf-8"))
    return d["api"], d["payload"]


class TestTikTok(unittest.TestCase):
    def setUp(self):
        api, pl = load("tiktok/search_synthetic.json")
        self.items = {i.video_id: i for i in normalize("tiktok", api, pl)}

    def test_count_and_ids(self):
        self.assertEqual(set(self.items), {"7300000000000000001", "7300000000000000002"})

    def test_stats_with_views(self):
        i = self.items["7300000000000000001"]
        self.assertEqual((i.play, i.like, i.comment, i.collect, i.share), (1234567, 45600, 789, 3400, 120))
        self.assertFalse(i.stats_approx)

    def test_zero_is_not_none(self):
        i = self.items["7300000000000000002"]
        self.assertEqual((i.play, i.comment, i.collect), (0, 0, 0))

    def test_meta(self):
        i = self.items["7300000000000000001"]
        self.assertEqual(i.url, "https://www.tiktok.com/@linh.review/video/7300000000000000001")
        self.assertEqual(i.hashtags, ["reviewlamdep", "sunscreen"])
        self.assertTrue(i.has_cart)
        self.assertFalse(self.items["7300000000000000002"].has_cart)
        self.assertEqual(i.cover_url, "https://cdn.example/c1.jpg")
        self.assertEqual(i.created_at, 1700000000)

    def test_excluded_api(self):
        api, pl = load("tiktok/search_synthetic.json")
        self.assertEqual(normalize("tiktok", "/api/recommend/item_list/", pl), [])

    def test_garbage_payload(self):
        for p in (None, [], {}, "x", 5, {"a": [1, {"b": None}]}):
            self.assertEqual(normalize("tiktok", "/api/x", p), [])


class TestDouyin(unittest.TestCase):
    def setUp(self):
        api, pl = load("douyin/search_synthetic.json")
        self.items = normalize("douyin", api, pl)

    def test_skips_images_and_ads(self):
        self.assertEqual([i.video_id for i in self.items], ["7400000000000000001"])

    def test_stats_no_play(self):
        i = self.items[0]
        self.assertIsNone(i.play)
        self.assertEqual((i.like, i.comment, i.collect, i.share), (23000, 456, 7800, 90))
        self.assertTrue(i.has_cart)
        self.assertEqual(i.duration_s, 42.0)
        self.assertEqual(i.hashtags, ["防晒", "测评"])
        self.assertEqual(i.author_id, "MS4wLjABAAAA_x")


class TestXhs(unittest.TestCase):
    def setUp(self):
        api, pl = load("xhs/search_synthetic.json")
        self.items = normalize("xhs", api, pl)

    def test_only_video_notes(self):
        self.assertEqual([i.video_id for i in self.items], ["65a000000000000000000001"])

    def test_abbreviated_counts(self):
        i = self.items[0]
        self.assertIsNone(i.play)
        self.assertEqual((i.like, i.comment, i.collect, i.share), (12000, 356, 2300, 45))
        self.assertTrue(i.stats_approx)
        self.assertIsNone(i.has_cart)
        self.assertIn("xsec_token=TOKEN_PLACEHOLDER", i.url)
        self.assertEqual(i.author_name, "薯薯")


if __name__ == "__main__":
    unittest.main()
