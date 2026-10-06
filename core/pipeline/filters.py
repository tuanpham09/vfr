"""Bộ lọc thuần. TikTok lọc theo view; Douyin/XHS lọc theo tim."""
from __future__ import annotations

from core.types import ScrapeJob, VideoItem


def metric_name(platform: str) -> str:
    return "view" if platform == "tiktok" else "tim"


def passes(item: VideoItem, job: ScrapeJob) -> tuple[bool, str]:
    if job.min_metric > 0:
        val = item.play if item.platform == "tiktok" else item.like
        if val is None:
            return False, f"thiếu số {metric_name(item.platform)}"
        if val < job.min_metric:
            return False, f"{metric_name(item.platform)} {val} < {job.min_metric}"
    if job.only_cart and item.platform != "xhs":
        if item.has_cart is not True:
            return False, "không có giỏ hàng"
    return True, ""


def hashtag_matches(item: VideoItem, tag: str) -> bool:
    t = tag.strip().lstrip("#").lower()
    return bool(t) and (any(t == h.lower() for h in item.hashtags) or f"#{t}" in item.desc.lower())
