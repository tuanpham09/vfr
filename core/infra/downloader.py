"""Tải media từ URL đã có (extension duyệt web, app không gọi API nền tảng — ADR-001).

Khung tối thiểu đợt này: `resolve_chain()` dựng chuỗi URL theo `media_urls`,
`download()` tải tuần tự bằng stdlib. Chưa làm resume/proxy/batch.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from core.log import get_logger
from core.pipeline.media_urls import dedupe_urls, douyin_url_chain, rednote_url_chain
from core.types import VideoItem

_LOG = get_logger(__name__)

# VFR005: literal URL nền tảng chỉ được nằm ở url_builder.py và file này.
REFERER = {
    "tiktok": "https://www.tiktok.com/",
    "douyin": "https://www.douyin.com/",
    "xhs": "https://www.xiaohongshu.com/",
}
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def referer_for(platform: str) -> str:
    """Referer theo nền tảng; '' nếu không rõ."""
    return REFERER.get(platform or "", "")


def _tiktok_candidates(raw: dict) -> list[str]:
    video = raw.get("video")
    if not isinstance(video, dict):
        return []
    out: list[str] = []
    for k in ("playAddr", "downloadAddr", "play_addr", "download_addr"):
        v = video.get(k)
        if isinstance(v, str) and v.strip().startswith(("http://", "https://")):
            out.append(v.strip())
        elif isinstance(v, dict):
            lst = v.get("url_list")
            if isinstance(lst, list):
                for u in lst:
                    if isinstance(u, str) and u.strip().startswith(("http://", "https://")):
                        out.append(u.strip())
        elif isinstance(v, list):
            for u in v:
                if isinstance(u, str) and u.strip().startswith(("http://", "https://")):
                    out.append(u.strip())
    return out


def resolve_chain(item: VideoItem) -> list[str]:
    """Dựng chuỗi URL tải cho 1 VideoItem. Không raise, không IO."""
    try:
        raw = item.raw if isinstance(item.raw, dict) else {}
        chain: list[str] = []
        if item.platform == "douyin":
            video = raw.get("video")
            chain = douyin_url_chain(video) if isinstance(video, dict) else []
        elif item.platform == "xhs":
            card = raw.get("note_card")
            if not isinstance(card, dict):
                card = raw
            chain = rednote_url_chain(card)
        elif item.platform == "tiktok":
            chain = _tiktok_candidates(raw)
        if item.play_url and item.play_url.startswith(("http://", "https://")):
            chain.append(item.play_url)
        # P1: dùng dedupe_urls dùng chung từ media_urls (xóa bản trùng trước đây).
        return dedupe_urls(chain)
    except Exception:  # noqa: BLE001 — resolve không được làm hỏng pipeline
        _LOG.exception("resolve_chain thất bại cho %s/%s", item.platform, item.video_id)
        if item.play_url:
            return [item.play_url]
        return []


def download(url: str, dest: str, platform: str = "", timeout: int = 30) -> str:
    """Tải 1 URL về `dest` (tạo thư mục cha). Trả đường dẫn đích. Chỉ tải URL có sẵn."""
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL không hợp lệ: {url[:60]}")
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    ref = referer_for(platform)
    if ref:
        req.add_header("Referer", ref)
    out = Path(dest)
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, timeout=timeout) as resp, out.open("wb") as fh:
        while True:
            chunk = resp.read(256 * 1024)
            if not chunk:
                break
            fh.write(chunk)
    return str(out)
