from __future__ import annotations

import re

from core.pipeline.normalizers import douyin, tiktok, xhs
from core.pipeline.stream import split_json_values
from core.types import VideoItem

# API không phải kết quả chính (gợi ý, liên quan...) -> bỏ để không lẫn video lạc đề.
EXCLUDE_API = re.compile(r"(recommend|related|preload|notice|/live|tab/feed|aweme/favorite)", re.I)
_BY_PLATFORM = {"tiktok": tiktok.normalize, "douyin": douyin.normalize, "xhs": xhs.normalize}


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
                out.setdefault(it.video_id, it)
        return list(out.values())
    return fn(api, payload)
