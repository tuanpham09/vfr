"""Test chuỗi URL tải. Thuần, không mạng. Synthetic [VERIFY]."""
import unittest

from core.infra.downloader import referer_for, resolve_chain
from core.pipeline.media_urls import (
    codec_from_url,
    douyin_url_chain,
    rednote_url_chain,
    resolution_from_gear,
)
from core.types import VideoItem


def vi(**k):
    base = dict(platform="douyin", video_id="1")
    base.update(k)
    return VideoItem(**base)


class TestCodec(unittest.TestCase):
    def test_cs_param(self):
        self.assertEqual(codec_from_url("https://v.example/x?cs=0"), "h264")
        self.assertEqual(codec_from_url("https://v.example/x?cs=2"), "h265")
        self.assertEqual(codec_from_url("https://v.example/x?a=1&cs=4"), "h265")

    def test_hints(self):
        self.assertEqual(codec_from_url("https://v.example/hvc1/x.mp4"), "h265")
        self.assertEqual(codec_from_url("https://v.example/x.mp4"), "h264")
        self.assertEqual(codec_from_url(None), "h264")  # type: ignore[arg-type]

    def test_gear(self):
        self.assertEqual(resolution_from_gear("720p"), 720)
        self.assertEqual(resolution_from_gear("1080p"), 1080)
        self.assertEqual(resolution_from_gear(""), 0)
        self.assertEqual(resolution_from_gear(None), 0)  # type: ignore[arg-type]


class TestDouyinChain(unittest.TestCase):
    def test_priority_order(self):
        video = {
            "play_addr": {"url_list": ["https://v.example/play.mp4"]},
            "bit_rate": [
                {"gear_name": "540p", "bit_rate": 100,
                 "play_addr": {"url_list": ["https://v.example/b540.mp4?cs=0"]}},
                {"gear_name": "720p", "bit_rate": 200,
                 "play_addr": {"url_list": ["https://v.example/b720.mp4?cs=0"]}},
            ],
            "play_addr_265": {"url_list": ["https://v.example/p265.mp4"]},
            "download_addr": {"url_list": ["https://v.example/dl.mp4"]},
        }
        chain = douyin_url_chain(video)
        self.assertEqual(chain[0], "https://v.example/play.mp4")
        self.assertLess(chain.index("https://v.example/b720.mp4?cs=0"),
                        chain.index("https://v.example/b540.mp4?cs=0"))
        self.assertEqual(chain[-1], "https://v.example/dl.mp4")
        self.assertLess(chain.index("https://v.example/p265.mp4"), chain.index("https://v.example/dl.mp4"))

    def test_dedupe_and_garbage(self):
        video = {"play_addr": {"url_list": ["https://v.example/a.mp4", "https://v.example/a.mp4", ""]},
                 "download_addr": {"url_list": ["not-a-url"]}}
        self.assertEqual(douyin_url_chain(video), ["https://v.example/a.mp4"])
        self.assertEqual(douyin_url_chain(None), [])  # type: ignore[arg-type]
        self.assertEqual(douyin_url_chain({}), [])


class TestRednoteChain(unittest.TestCase):
    def test_h264_first(self):
        card = {"video": {"media": {"stream": {
            "h265": {"url_list": ["https://x.example/265.mp4"]},
            "h264": {"url_list": ["https://x.example/264.mp4"]},
        }}}}
        self.assertEqual(rednote_url_chain(card),
                         ["https://x.example/264.mp4", "https://x.example/265.mp4"])
        self.assertEqual(rednote_url_chain({}), [])
        self.assertEqual(rednote_url_chain(None), [])  # type: ignore[arg-type]


class TestResolve(unittest.TestCase):
    def test_douyin(self):
        it = vi(raw={"video": {"play_addr": {"url_list": ["https://v.example/p.mp4"]}}},
                play_url="")
        self.assertEqual(resolve_chain(it), ["https://v.example/p.mp4"])

    def test_fallback_play_url(self):
        it = vi(platform="tiktok", raw={}, play_url="https://c.example/v.mp4")
        self.assertEqual(resolve_chain(it), ["https://c.example/v.mp4"])

    def test_referer(self):
        self.assertEqual(referer_for("douyin"), "https://www.douyin.com/")
        self.assertEqual(referer_for("?"), "")


if __name__ == "__main__":
    unittest.main()
