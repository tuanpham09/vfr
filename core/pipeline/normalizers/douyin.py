"""Douyin: dict có aweme_id + statistics. play luôn None (play_count thường ẩn/0)."""
from __future__ import annotations

import json

from core.pipeline.normalizers.common import (as_str, dedupe_tags, dig, first_url,
                                              hashtags_from_text, read_counts, to_epoch, walk)
from core.types import VideoItem

CART_HINTS = ("product", "goods", "shop", "commerce")  # [VERIFY]
CART_KEYS = ("anchor_info", "shop_product_info", "commerce_info")
_MAP = {
    "like": ("digg_count",),
    "comment": ("comment_count",),
    "collect": ("collect_count",),
    "share": ("share_count",),
}


def _is_item(d: dict) -> bool:
    return as_str(d.get("aweme_id")) != "" and isinstance(d.get("statistics"), dict)


def _has_cart(d: dict) -> bool:
    for k in CART_KEYS:
        v = d.get(k)
        if v:
            blob = json.dumps(v, ensure_ascii=False).lower()
            if any(h in blob for h in CART_HINTS):
                return True
    return False


def normalize(api: str, payload: object) -> list[VideoItem]:
    out: dict[str, VideoItem] = {}
    for d in walk(payload):
        if not _is_item(d):
            continue
        vid = as_str(d["aweme_id"])
        if vid in out or d.get("is_ads") is True or d.get("images"):
            continue
        nums, approx = read_counts(d["statistics"], _MAP)
        author = d.get("author") if isinstance(d.get("author"), dict) else {}
        desc = as_str(d.get("desc"))
        tags = [as_str(t.get("hashtag_name")) for t in (d.get("text_extra") or []) if isinstance(t, dict)]
        tags += [as_str(c.get("cha_name")) for c in (d.get("cha_list") or []) if isinstance(c, dict)]
        video = d.get("video") if isinstance(d.get("video"), dict) else {}
        dur = video.get("duration")  # mili giây
        out[vid] = VideoItem(
            platform="douyin", video_id=vid, url=f"https://www.douyin.com/video/{vid}",
            desc=desc, author_id=as_str(author.get("sec_uid") or author.get("uid")),
            author_name=as_str(author.get("nickname")),
            hashtags=dedupe_tags(tags + hashtags_from_text(desc)),
            cover_url=first_url(video.get("cover") or video.get("origin_cover")),
            play_url=first_url(video.get("play_addr")),
            duration_s=dur / 1000 if isinstance(dur, (int, float)) and dur > 0 else None,
            play=None, like=nums["like"], comment=nums["comment"], collect=nums["collect"],
            share=nums["share"], stats_approx=approx, has_cart=_has_cart(d),
            created_at=to_epoch(d.get("create_time")), raw=d,
        )
    return list(out.values())
