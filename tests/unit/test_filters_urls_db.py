import tempfile
import unittest
from pathlib import Path

from core.infra.db import Repo
from core.pipeline.filters import hashtag_matches, passes
from core.pipeline.url_builder import build_url
from core.types import ScrapeJob, VideoItem


def vi(**k):
    base = dict(platform="tiktok", video_id="1")
    base.update(k)
    return VideoItem(**base)


class TestFilters(unittest.TestCase):
    def test_tiktok_views(self):
        job = ScrapeJob("tiktok", "keyword", ["x"], min_metric=1000)
        self.assertTrue(passes(vi(play=1000), job)[0])
        self.assertFalse(passes(vi(play=999), job)[0])
        self.assertFalse(passes(vi(play=None), job)[0])

    def test_douyin_uses_like(self):
        job = ScrapeJob("douyin", "keyword", ["x"], min_metric=100)
        self.assertTrue(passes(vi(platform="douyin", like=100, play=None), job)[0])
        self.assertFalse(passes(vi(platform="douyin", like=5), job)[0])

    def test_min_zero_disables(self):
        self.assertTrue(passes(vi(play=None), ScrapeJob("tiktok", "keyword", ["x"]))[0])

    def test_cart(self):
        job = ScrapeJob("tiktok", "keyword", ["x"], only_cart=True)
        self.assertTrue(passes(vi(has_cart=True), job)[0])
        self.assertFalse(passes(vi(has_cart=False), job)[0])
        self.assertFalse(passes(vi(has_cart=None), job)[0])
        self.assertTrue(passes(vi(platform="xhs", has_cart=None), job)[0])  # XHS bỏ qua

    def test_hashtag(self):
        self.assertTrue(hashtag_matches(vi(hashtags=["防晒"]), "#防晒"))
        self.assertTrue(hashtag_matches(vi(desc="hay #Review quá"), "review"))
        self.assertFalse(hashtag_matches(vi(desc="abc"), "review"))


class TestUrls(unittest.TestCase):
    def test_keyword(self):
        self.assertEqual(build_url("tiktok", "keyword", "kem chống nắng"),
                         "https://www.tiktok.com/search/video?q=kem%20ch%E1%BB%91ng%20n%E1%BA%AFng")
        self.assertTrue(build_url("douyin", "keyword", "防晒").endswith("?type=video"))
        self.assertIn("type=51", build_url("xhs", "keyword", "防晒"))

    def test_hashtag_user(self):
        self.assertEqual(build_url("tiktok", "hashtag", "#abc"), "https://www.tiktok.com/tag/abc")
        self.assertEqual(build_url("tiktok", "user", "@bob"), "https://www.tiktok.com/@bob")
        self.assertIn("%23", build_url("douyin", "hashtag", "防晒"))

    def test_errors(self):
        for args in [("douyin", "user", "abc"), ("xhs", "user", "abc"), ("tiktok", "keyword", " "),
                     ("tiktok", "link", "abc"), ("tiktok", "link", "https://evil.com/x"),
                     ("douyin", "link", "https://www.tiktok.com/x"), ("fb", "keyword", "a")]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    build_url(*args)

    def test_links_ok(self):
        self.assertTrue(build_url("douyin", "user", "https://www.douyin.com/user/abc"))
        self.assertTrue(build_url("douyin", "link", "https://v.douyin.com/abc/"))


class TestRepo(unittest.TestCase):
    def test_upsert_merge(self):
        with tempfile.TemporaryDirectory() as d:
            r = Repo(str(Path(d) / "t.db"))
            a, new = r.upsert(vi(play=100, like=10, desc="a", hashtags=["x"]))
            self.assertTrue(new)
            r.upsert(vi(status="done", local_path="/f.mp4", has_face=True))
            b, new2 = r.upsert(vi(play=200, like=None, comment=3))
            self.assertFalse(new2)
            self.assertEqual((b.play, b.like, b.comment, b.desc, b.hashtags), (200, 10, 3, "a", ["x"]))
            self.assertEqual((b.status, b.local_path, b.has_face), ("done", "/f.mp4", True))
            self.assertEqual(len(r.list_videos()), 1)
            r.close()


if __name__ == "__main__":
    unittest.main()
