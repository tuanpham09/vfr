"""Đối chiếu normalizer với cấu trúc/giá trị công khai của các dự án mã nguồn mở (xem FIELD_VERIFICATION.md)."""
import json
import unittest
from pathlib import Path

from core.pipeline.normalizers import normalize

FX = Path(__file__).resolve().parents[1] / "fixtures" / "reference"
load = lambda n: json.loads((FX / n).read_text(encoding="utf-8"))["payload"]


class TestReferenceShapes(unittest.TestCase):
    def test_tiktok(self):
        (i,) = normalize("tiktok", "/api/post/item_list/", load("tiktok_stats_shape.json"))
        self.assertEqual((i.play, i.like, i.comment, i.share, i.collect), (37825357, 3773532, 20166, 33456, 1234))
        self.assertEqual(i.author_id, "someuser")
        self.assertEqual(i.url, "https://www.tiktok.com/@someuser/video/6818316025491246342")
        self.assertEqual(i.hashtags, ["quarantinelife", "throwback"])

    def test_douyin_play_ignored(self):
        (i,) = normalize("douyin", "/aweme/v1/web/aweme/post/", load("douyin_stats_shape.json"))
        self.assertEqual((i.like, i.comment, i.collect, i.share), (70996, 4719, 2021, 300))
        self.assertIsNone(i.play)
        self.assertIn("playwm", i.play_url)

    def test_xhs(self):
        (i,) = normalize("xhs", "/api/sns/web/v1/search/notes", load("xhs_stats_shape.json"))
        self.assertEqual((i.like, i.comment, i.collect, i.share), (15000, 88, 2300, 7))
        self.assertTrue(i.stats_approx)
        self.assertIsNone(i.play)


if __name__ == "__main__":
    unittest.main()
