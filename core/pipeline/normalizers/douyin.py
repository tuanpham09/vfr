"""Douyin: dict có aweme_id + statistics. play luôn None (play_count thường ẩn/0)."""
from __future__ import annotations

from core.pipeline.counts import parse_count
from core.pipeline.normalizers.common import (as_str, dedupe_tags, dig, first_url,
                                              has_cart_signals, hashtags_from_text,
                                              read_counts, to_epoch, walk)
from core.pipeline.url_builder import douyin_video_url
from core.types import VideoItem

_MAP = {
    "like": ("digg_count",),
    "comment": ("comment_count",),
    "collect": ("collect_count",),
    "share": ("share_count",),
}


def _is_item(d: dict) -> bool:
    # Chặt: bắt buộc có id + statistics là dict (kể cả rỗng).
    # Bản nới lỏng trước đây (chỉ cần author/desc/title/like_text) đã biến
    # author blob, suggestion chỉ có id, dict DOM thiếu stats thành VideoItem
    # với URL /video/<id> 404. Stub DOM của adapter luôn có statistics nên
    # vẫn được chấp nhận.
    has_id = as_str(d.get("aweme_id") or d.get("video_id")) != ""
    return has_id and isinstance(d.get("statistics"), dict)


def _has_cart(d: dict) -> bool:
    return has_cart_signals(d)


def normalize(api: str, payload: object) -> list[VideoItem]:
    src = "dom" if (api or "").startswith("dom://") else "api"
    out: dict[str, VideoItem] = {}
    for d in walk(payload):
        if not _is_item(d):
            continue
        vid = as_str(d.get("aweme_id") or d.get("video_id"))
        if vid in out or d.get("is_ads") is True or d.get("images"):
            continue
        stats = d.get("statistics") if isinstance(d.get("statistics"), dict) else {}
        nums, approx = read_counts(stats, _MAP)
        if nums["like"] is None:
            # Extension chỉ forward text thô (vd. "2.3万"), Python parse ra số.
            like_val, like_approx = parse_count(d.get("like_text"))
            if like_val is not None:
                nums["like"], approx = like_val, approx or like_approx
        author = d.get("author") if isinstance(d.get("author"), dict) else {}
        desc = as_str(d.get("desc") or d.get("title"))
        tags = [as_str(t.get("hashtag_name")) for t in (d.get("text_extra") or []) if isinstance(t, dict)]
        tags += [as_str(c.get("cha_name")) for c in (d.get("cha_list") or []) if isinstance(c, dict)]
        video = d.get("video") if isinstance(d.get("video"), dict) else {}
        dur = video.get("duration")  # mili giây
        author_id = as_str(author.get("sec_uid") or author.get("uid") or d.get("author_id"))
        author_name = as_str(author.get("nickname") or d.get("author_name"))
        cover = first_url(video.get("cover") or video.get("origin_cover") or d.get("cover_url"))
        play = first_url(video.get("play_addr") or d.get("play_url"))
        out[vid] = VideoItem(
            platform="douyin", video_id=vid, url=douyin_video_url(vid),
            desc=desc, author_id=author_id,
            author_name=author_name,
            hashtags=dedupe_tags(tags + hashtags_from_text(desc)),
            cover_url=cover,
            play_url=play,
            duration_s=dur / 1000 if isinstance(dur, (int, float)) and dur > 0 else None,
            play=None, like=nums["like"], comment=nums["comment"], collect=nums["collect"],
            share=nums["share"], stats_approx=approx, has_cart=_has_cart(d),
            created_at=to_epoch(d.get("create_time")), raw={**d, "_src": src},
        )
    return list(out.values())
