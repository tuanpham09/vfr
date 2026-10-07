"""Xiaohongshu: item có note_card (search/feed) hoặc có note_id + interact_info (user_posted).
play = None; has_cart = None (XHS không có giỏ hàng)."""
from __future__ import annotations

import re

from core.pipeline.normalizers.common import (as_str, dedupe_tags, dig, first_url, read_counts,
                                              to_epoch, walk)
from core.pipeline.url_builder import xhs_note_url
from core.types import VideoItem

_MAP = {
    "like": ("liked_count",),
    "comment": ("comment_count",),
    "collect": ("collected_count",),
    "share": ("shared_count", "share_count"),
}
_TOPIC = re.compile(r"#([^#\[\]\s]+)\[话题\]#")


def _card_and_outer(d: dict) -> tuple[dict, dict] | None:
    card = d.get("note_card")
    if isinstance(card, dict) and isinstance(card.get("interact_info"), dict):
        return card, d
    if isinstance(d.get("interact_info"), dict) and (d.get("note_id") or d.get("id")):
        return d, d
    return None


def _cover(card: dict) -> str:
    cover = card.get("cover")
    if isinstance(cover, dict):
        for k in ("url_default", "url_pre", "url"):
            if isinstance(cover.get(k), str) and cover[k]:
                return cover[k]
        return first_url(cover.get("info_list"))
    return first_url(cover)


def _play(card: dict) -> str:
    h264 = dig(card, "video", "media", "stream", "h264")
    return first_url(h264) if h264 else ""


def normalize(api: str, payload: object) -> list[VideoItem]:
    out: dict[str, VideoItem] = {}
    for d in walk(payload):
        pair = _card_and_outer(d)
        if not pair:
            continue
        card, outer = pair
        kind = as_str(card.get("type"))
        if kind and kind != "video":
            continue
        if not kind and not card.get("video"):
            continue
        vid = as_str(outer.get("id") or card.get("note_id") or outer.get("note_id"))
        if not vid or vid in out:
            continue
        nums, approx = read_counts(card["interact_info"], _MAP)
        user = card.get("user") if isinstance(card.get("user"), dict) else {}
        title = as_str(card.get("display_title") or card.get("title"))
        desc = as_str(card.get("desc"))
        tags = [as_str(t.get("name")) for t in (card.get("tag_list") or []) if isinstance(t, dict)]
        tags += _TOPIC.findall(desc)
        token = as_str(outer.get("xsec_token") or card.get("xsec_token"))
        out[vid] = VideoItem(
            platform="xhs", video_id=vid, url=xhs_note_url(vid, token),
            desc=(title + " " + desc).strip() if desc and title and desc != title else (desc or title),
            author_id=as_str(user.get("user_id")),
            author_name=as_str(user.get("nickname") or user.get("nick_name")),
            hashtags=dedupe_tags(tags), cover_url=_cover(card), play_url=_play(card),
            play=None, like=nums["like"], comment=nums["comment"], collect=nums["collect"],
            share=nums["share"], stats_approx=approx, has_cart=None,
            created_at=to_epoch(card.get("time")), raw=d,
        )
    return list(out.values())
