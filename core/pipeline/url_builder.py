"""Dựng URL mở trong extension. Thuần: không IO."""
from __future__ import annotations

import re
from urllib.parse import quote, urlparse

_HOSTS = {
    "tiktok": ("tiktok.com",),
    "douyin": ("douyin.com", "iesdouyin.com"),
    "xhs": ("xiaohongshu.com", "xhslink.com"),
}


def _is_url(s: str) -> bool:
    return s.lower().startswith(("http://", "https://"))


def _check_host(platform: str, url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if not any(host == h or host.endswith("." + h) for h in _HOSTS[platform]):
        raise ValueError(f"Link không thuộc nền tảng {platform}: {url}")
    return url


def build_url(platform: str, mode: str, text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("Mục nhập trống")
    if platform not in _HOSTS:
        raise ValueError(f"Nền tảng không hỗ trợ: {platform}")
    if mode == "link" or _is_url(text):
        if not _is_url(text):
            raise ValueError("Cần dán link đầy đủ (bắt đầu bằng https://)")
        return _check_host(platform, text)
    if mode == "user":
        if platform == "tiktok":
            return f"https://www.tiktok.com/@{quote(text.lstrip('@'))}"
        raise ValueError("Douyin/XHS cần dán link trang cá nhân của user")
    if mode == "hashtag":
        tag = text.lstrip("#")
        if platform == "tiktok":
            return f"https://www.tiktok.com/tag/{quote(tag)}"
        text = "#" + tag
    q = quote(text)
    if platform == "tiktok":
        return f"https://www.tiktok.com/search/video?q={q}"
    if platform == "douyin":
        return f"https://www.douyin.com/search/{q}?type=video"
    return f"https://www.xiaohongshu.com/search_result?keyword={q}&source=web_search_result_notes&type=51"


def tiktok_handle(text: str) -> str:
    """Lấy @handle (chữ thường, không @) từ '@name', 'name' hoặc link trang cá nhân; '' nếu không xác định."""
    text = text.strip()
    if _is_url(text):
        m = re.search(r"/@([^/?#]+)", text)
        return m.group(1).lower() if m else ""
    return text.lstrip("@").lower()


def tiktok_video_url(unique: str, video_id: str) -> str:
    """Permalink video TikTok. Tập trung tại đây để VFR005 sạch."""
    unique = (unique or "").strip()
    if unique:
        return f"https://www.tiktok.com/@{unique}/video/{video_id}"
    return f"https://www.tiktok.com/video/{video_id}"


def douyin_video_url(video_id: str) -> str:
    """Permalink video Douyin. Tập trung tại đây để VFR005 sạch."""
    return f"https://www.douyin.com/video/{video_id}"


def xhs_note_url(note_id: str, token: str = "") -> str:
    """Permalink note XHS (kèm xsec_token khi có). Tập trung tại đây để VFR005 sạch."""
    url = f"https://www.xiaohongshu.com/explore/{note_id}"
    if token:
        url += f"?xsec_token={token}&xsec_source=pc_search"
    return url
