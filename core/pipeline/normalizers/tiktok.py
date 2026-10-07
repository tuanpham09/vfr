"""TikTok: tìm các dict dạng item (id + stats + video) ở bất kỳ độ sâu nào.

Tên trường là [VERIFY] cho tới khi có fixture thật (docs/platforms/tiktok.md).
"""
from __future__ import annotations

from core.pipeline.normalizers.common import (as_str, dedupe_tags, dig, first_url,
                                              has_cart_signals, hashtags_from_text,
                                              read_counts, to_epoch, walk)
from core.pipeline.url_builder import tiktok_video_url
from core.types import VideoItem

_MAP = {
    "play": ("playCount", "play_count"),
    "like": ("diggCount", "digg_count"),
    "comment": ("commentCount", "comment_count"),
    "collect": ("collectCount", "collect_count"),
    "share": ("shareCount", "share_count"),
}


def _is_item(d: dict) -> bool:
    return (as_str(d.get("id")) != "" and isinstance(d.get("stats"), dict)
            and isinstance(d.get("video"), dict))


def _has_cart(item: dict) -> bool:
    return has_cart_signals(item)


def normalize(api: str, payload: object) -> list[VideoItem]:
    out: dict[str, VideoItem] = {}
    for d in walk(payload):
        if not _is_item(d):
            continue
        vid = as_str(d["id"])
        if vid in out:
            continue
        stats: dict = dict(d.get("statsV2") or {})
        stats.update({k: v for k, v in d["stats"].items() if v is not None})
        nums, approx = read_counts(stats, _MAP)

        author = d.get("author")
        if isinstance(author, dict):
            uid = as_str(author.get("uniqueId") or author.get("id"))
            name = as_str(author.get("nickname") or author.get("uniqueId"))
            unique = as_str(author.get("uniqueId")) or uid
        else:
            uid = unique = as_str(author)
            name = uid
        desc = as_str(d.get("desc"))
        video = d["video"]
        tags = [as_str(t.get("hashtagName")) for t in (d.get("textExtra") or []) if isinstance(t, dict)]
        tags = dedupe_tags(tags + hashtags_from_text(desc))
        dur = video.get("duration")
        out[vid] = VideoItem(
            platform="tiktok", video_id=vid,
            url=tiktok_video_url(unique, vid),
            desc=desc, author_id=uid, author_name=name, hashtags=tags,
            cover_url=first_url(video.get("cover") or video.get("originCover") or video.get("dynamicCover")),
            play_url=first_url(video.get("playAddr") or video.get("downloadAddr")),
            duration_s=float(dur) if isinstance(dur, (int, float)) and dur > 0 else None,
            play=nums["play"], like=nums["like"], comment=nums["comment"],
            collect=nums["collect"], share=nums["share"], stats_approx=approx,
            has_cart=_has_cart(d), created_at=to_epoch(d.get("createTime")),
            raw=d,
        )
    return list(out.values())
