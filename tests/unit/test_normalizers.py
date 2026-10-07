import json
import unittest
from pathlib import Path

from core.pipeline.normalizers import normalize
from core.pipeline.normalizers.common import has_cart_signals

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


class TestStream(unittest.TestCase):
    def test_split_and_normalize_stream(self):
        from core.pipeline.stream import split_json_values
        api, pl = load("douyin/search_synthetic.json")
        text = "data: " + json.dumps(pl) + "\n\ndata: " + json.dumps({"x": 1}) + "\n"
        self.assertEqual(len(split_json_values(text)), 2)
        self.assertEqual([i.video_id for i in normalize("douyin", api, text)], ["7400000000000000001"])
        self.assertEqual(split_json_values("không có json"), [])

    def test_favorite_excluded(self):
        api, pl = load("douyin/search_synthetic.json")
        self.assertEqual(normalize("douyin", "/aweme/v1/web/aweme/favorite/?a=1", pl), [])

    def test_stream_richer_wins_over_partial(self):
        # Chunk partial (stats null) tới trước không được thắng bản full tới sau.
        api = "/aweme/v1/web/general/search/single/"
        partial = {"aweme_id": "99", "desc": "x", "statistics": {},
                   "author": {"nickname": "a"}}
        full = {"aweme_id": "99", "desc": "x", "statistics": {"digg_count": 500},
                "author": {"nickname": "a"}}
        text = json.dumps(partial) + "\n" + json.dumps(full)
        items = normalize("douyin", api, text)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].like, 500)

    def test_rejects_dict_without_statistics(self):
        # Author blob / suggestion chỉ có id / dict thiếu stats -> không thành item.
        items = normalize("douyin", "/aweme/v1/web/search/item/", {
            "data": [
                {"aweme_id": "10", "desc": "không stats"},
                {"aweme_id": "11", "author": {"nickname": "blob"}},
                {"aweme_id": "12", "statistics": {}},
            ],
        })
        self.assertEqual([i.video_id for i in items], ["12"])


    def test_dom_fallback_items(self):
        dom_payload = {
            "data": [
                {
                    "aweme_id": "7450000000000000001",
                    "desc": "迷你制冰机 家用小型",
                    "author": {"nickname": "家电测评", "sec_uid": "MS4wLj_test"},
                    "cover_url": "https://p3.example/c.jpg",
                    "statistics": {"digg_count": "1.2万"},
                }
            ]
        }
        items = normalize("douyin", "dom://douyin/search", dom_payload)
        self.assertEqual(len(items), 1)
        it = items[0]
        self.assertEqual(it.video_id, "7450000000000000001")
        self.assertEqual(it.author_name, "家电测评")
        self.assertEqual(it.author_id, "MS4wLj_test")
        self.assertEqual(it.desc, "迷你制冰机 家用小型")
        self.assertEqual(it.like, 12000)
        self.assertTrue(it.stats_approx)


class TestCartSignals(unittest.TestCase):
    """Synthetic: chống regression. [VERIFY] — cần fixture thật để chốt."""

    def test_is_ec_video(self):
        self.assertTrue(has_cart_signals({"isECVideo": 1}))
        self.assertTrue(has_cart_signals({"isECVideo": "1"}))

    def test_anchor_types(self):
        self.assertTrue(has_cart_signals({"anchors": [{"type": 33}]}))
        self.assertTrue(has_cart_signals({"anchors": [{"type": "5"}]}))
        self.assertTrue(has_cart_signals({"anchors": [{"component_key": "anchor_shop"}]}))
        self.assertFalse(has_cart_signals({"anchors": []}))
        self.assertFalse(has_cart_signals({"anchors": [{"type": 1, "keyword": "x"}]}))

    def test_commerce_keys(self):
        self.assertTrue(has_cart_signals({"commerceInfo": {"product_id": "1"}}))
        self.assertTrue(has_cart_signals({"commerce_info": {"shop": "x"}}))
        self.assertTrue(has_cart_signals({"extra": "{\"product_id\":\"9\"}"}))

    def test_no_signal(self):
        self.assertFalse(has_cart_signals({}))
        self.assertFalse(has_cart_signals({"anchors": None}))
        self.assertFalse(has_cart_signals(None))  # type: ignore[arg-type]
        self.assertFalse(has_cart_signals("x"))  # type: ignore[arg-type]

    def test_tiktok_normalize_uses_helper(self):
        items = normalize("tiktok", "/api/search/general/full/", {
            "data": [{"type": 1, "item": {
                "id": "1", "desc": "x",
                "stats": {"playCount": 1},
                "video": {"playAddr": "u"},
                "isECVideo": 1,
            }}],
        })
        self.assertTrue(items[0].has_cart)

    def test_douyin_missing_stats_is_none(self):
        items = normalize("douyin", "/aweme/v1/web/search/item/", {
            "data": [{"aweme_id": "9", "desc": "x", "statistics": {}}],
        })
        it = items[0]
        self.assertIsNone(it.like)
        self.assertFalse(it.has_cart)


class TestOmitUnavailable(unittest.TestCase):
    """None = nền tảng không cung cấp; 0 = số thật. Không ép 0."""

    def test_tiktok_missing_keys_are_none(self):
        items = normalize("tiktok", "/api/search/general/full/", {
            "data": [{"type": 1, "item": {
                "id": "7", "desc": "x",
                "stats": {"playCount": 5},
                "video": {"playAddr": "u"},
            }}],
        })
        it = items[0]
        self.assertEqual(it.play, 5)
        self.assertIsNone(it.like)
        self.assertIsNone(it.share)

    def test_xhs_missing_share_is_none(self):
        items = normalize("xhs", "/api/sns/web/v1/search/notes", {
            "data": {"items": [{"id": "n1", "note_card": {
                "type": "video",
                "interact_info": {"liked_count": 3},
                "video": {"media": {"stream": {"h264": "https://x.example/v.mp4"}}},
            }}]},
        })
        it = items[0]
        self.assertEqual(it.like, 3)
        self.assertIsNone(it.share)


if __name__ == "__main__":
    unittest.main()
