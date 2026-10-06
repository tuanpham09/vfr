from __future__ import annotations

import re

from core.pipeline.normalizers import douyin, tiktok, xhs
from core.types import VideoItem

# API không phải kết quả chính (gợi ý, liên quan...) -> bỏ để không lẫn video lạc đề.
EXCLUDE_API = re.compile(r"(recommend|related|preload|notice|/live|tab/feed)", re.I)
_BY_PLATFORM = {"tiktok": tiktok.normalize, "douyin": douyin.normalize, "xhs": xhs.normalize}


def normalize(platform: str, api: str, payload: object) -> list[VideoItem]:
    if EXCLUDE_API.search(api or ""):
        return []
    fn = _BY_PLATFORM.get(platform)
    return fn(api, payload) if fn else []
