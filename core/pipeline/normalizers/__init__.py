from __future__ import annotations

import re

from core.pipeline.normalizers import douyin, tiktok, xhs
from core.pipeline.stream import split_json_values
from core.types import VideoItem

# API không phải kết quả chính (gợi ý, liên quan, feed...) -> bỏ để không lẫn video lạc đề.
# P1: /feed/ (vd. /aweme/v1/feed/) không phải kết quả search keyword — chặn để khỏi tính
# nhầm vào target (trước đây lọt qua vì chỉ chặn tab/feed).
EXCLUDE_API = re.compile(r"(recommend|related|preload|notice|/live|tab/feed|/feed/|aweme/favorite)", re.I)
_BY_PLATFORM = {"tiktok": tiktok.normalize, "douyin": douyin.normalize, "xhs": xhs.normalize}


def _has_any_stat(it: VideoItem) -> bool:
    """True nếu item có ít nhất một số liệu (phân biệt 0 với None)."""
    return it.like is not None or it.comment is not None or it.collect is not None or it.share is not None


def normalize(platform: str, api: str, payload: object) -> list[VideoItem]:
    if EXCLUDE_API.search(api or ""):
        return []
    fn = _BY_PLATFORM.get(platform)
    if not fn:
        return []
    if isinstance(payload, str):          # response dạng stream
        out: dict[str, VideoItem] = {}
        for p in split_json_values(payload):
            for it in fn(api, p):
                prev = out.get(it.video_id)
                if prev is None:
                    out[it.video_id] = it
                elif _has_any_stat(it) and not _has_any_stat(prev):
                    # Chunk partial tới trước (stats null) không được thắng
                    # bản full tới sau (stats thật) — thay bằng bản giàu hơn.
                    out[it.video_id] = it
        return list(out.values())
    return fn(api, payload)
