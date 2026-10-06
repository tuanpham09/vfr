"""Kiểu dữ liệu dùng chung. Lớp thấp nhất: không import gì từ core/app."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Platform(str, Enum):
    TIKTOK = "tiktok"
    DOUYIN = "douyin"
    XHS = "xhs"


class Mode(str, Enum):
    KEYWORD = "keyword"
    USER = "user"
    HASHTAG = "hashtag"
    LINK = "link"


PLATFORM_LABEL = {"tiktok": "TikTok", "douyin": "Douyin", "xhs": "Xiaohongshu"}


@dataclass
class VideoItem:
    platform: str
    video_id: str
    url: str = ""
    desc: str = ""
    author_id: str = ""
    author_name: str = ""
    hashtags: list[str] = field(default_factory=list)
    cover_url: str = ""
    play_url: str = ""
    duration_s: float | None = None
    # Số liệu: None = nền tảng không cung cấp (khác 0).
    play: int | None = None
    like: int | None = None
    comment: int | None = None
    collect: int | None = None
    share: int | None = None
    stats_approx: bool = False
    has_cart: bool | None = None
    has_face: bool | None = None  # chưa làm trong MVP đợt 1
    relevance: float | None = None  # 0..1, chỉ có khi cào theo từ khóa
    status: str = "new"
    local_path: str | None = None
    query: str = ""
    task_id: str = ""
    created_at: int | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def key(self) -> tuple[str, str]:
        return (self.platform, self.video_id)


@dataclass
class ScrapeJob:
    platform: str
    mode: str
    inputs: list[str]
    target: int = 30           # số video MỖI mục nhập
    min_metric: int = 0        # TikTok: lượt xem; Douyin/XHS: lượt tim
    only_cart: bool = False
    min_relevance: float = 0.5  # chỉ áp cho mode từ khóa; 0 = tắt
