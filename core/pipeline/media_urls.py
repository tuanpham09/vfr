"""Chuỗi URL tải media theo thứ tự ưu tiên. Thuần, không IO/network.

Douyin (suy từ VideoContentStudio `_dis/crawlers_douyin_scraper.py.txt:847`):
  play_addr → bit_rate H264 (res cao trước, bitrate cao trước)
  → play_addr_265 → bit_rate H265 → download_addr (cuối, có thể watermark).
XHS (rednote): ưu tiên H264 trước để tương thích preview/OpenCV.
"""
from __future__ import annotations

import re

_CS_RE = re.compile(r"(?:^|[?&])cs=(\d+)")
_GEAR_RE = re.compile(r"(\d{3,4})p?")
_H265_HINTS = ("hvc1", "hev1", "h265", "hevc")


def _to_int(v: object) -> int:
    if v is None or isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return v if v > 0 else 0
    if isinstance(v, float):
        return int(v) if v > 0 else 0
    if isinstance(v, str):
        try:
            n = int(float(v.strip()))
        except (TypeError, ValueError):
            return 0
        return n if n > 0 else 0
    return 0


def codec_from_url(url: object) -> str:
    """h264 mặc định; cs=2/4 hoặc hint hvc1/hev1/h265/hevc → h265."""
    s = url if isinstance(url, str) else ""
    m = _CS_RE.search(s)
    if m:
        return "h265" if m.group(1) in ("2", "4") else "h264"
    low = s.lower()
    if any(h in low for h in _H265_HINTS):
        return "h265"
    return "h264"


def resolution_from_gear(gear: object) -> int:
    """Trích số phân giải từ gear_name (vd. '720p' → 720); 0 nếu không khớp."""
    if not isinstance(gear, str):
        return 0
    m = _GEAR_RE.search(gear)
    return int(m.group(1)) if m else 0


def _addr_urls(addr: object) -> list[str]:
    if not isinstance(addr, dict):
        return []
    lst = addr.get("url_list")
    if not isinstance(lst, list):
        return []
    out: list[str] = []
    for u in lst:
        if isinstance(u, str) and u.strip():
            out.append(u.strip())
    return out


def dedupe_urls(urls: list[str]) -> list[str]:
    """Loại URL trùng, giữ thứ tự xuất hiện đầu. Dùng chung cho downloader."""
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def douyin_url_chain(video: object) -> list[str]:
    """Trả chuỗi URL tải từ dict `video` của aweme_info. Không raise."""
    if not isinstance(video, dict):
        return []
    out: list[str] = []
    play_addr = video.get("play_addr")
    if isinstance(play_addr, dict):
        out += _addr_urls(play_addr)

    bit_rate = video.get("bit_rate")
    entries: list[dict] = []
    if isinstance(bit_rate, list):
        entries = [b for b in bit_rate if isinstance(b, dict)]
    h264: list[tuple[int, int, list[str]]] = []
    h265: list[tuple[int, int, list[str]]] = []
    for e in entries:
        addr = e.get("play_addr")
        urls = _addr_urls(addr) if isinstance(addr, dict) else []
        if not urls:
            continue
        gear = e.get("gear_name") if isinstance(e.get("gear_name"), str) else ""
        bitrate = _to_int(e.get("bit_rate") or e.get("bit_rate_265"))
        width = _to_int((addr.get("width") if isinstance(addr, dict) else 0)
                        or e.get("width") or video.get("width"))
        height = _to_int((addr.get("height") if isinstance(addr, dict) else 0)
                         or e.get("height") or video.get("height"))
        res = height or resolution_from_gear(gear)
        # P1: phân loại theo cả entry (gear/bit_rate_265 hint h265), không chỉ URL đầu —
        # entry h265 không đánh dấu sẽ xếp nhầm trước play_addr_265.
        codec = codec_from_url(urls[0])
        if codec == "h264":
            blob = f"{gear} {e.get('bit_rate_265') or ''}".lower()
            if "265" in blob or "h265" in blob or "hevc" in blob or "hvc" in blob:
                codec = "h265"
        bucket = h264 if codec == "h264" else h265
        bucket.append((res, bitrate, urls))
    for _res, _br, urls in sorted(h264, key=lambda t: (t[0], t[1]), reverse=True):
        out += urls
    addr265 = video.get("play_addr_265")
    if isinstance(addr265, dict):
        out += _addr_urls(addr265)
    for _res, _br, urls in sorted(h265, key=lambda t: (t[0], t[1]), reverse=True):
        out += urls
    dl = video.get("download_addr")
    if isinstance(dl, dict):
        out += _addr_urls(dl)
    return dedupe_urls([u for u in out if u.startswith(("http://", "https://"))])


def _collect_urls(v: object) -> list[str]:
    if isinstance(v, str):
        s = v.strip()
        return [s] if s.startswith(("http://", "https://")) else []
    if isinstance(v, list):
        out: list[str] = []
        for item in v:
            out += _collect_urls(item)
        return out
    if isinstance(v, dict):
        out2: list[str] = []
        for k in ("url_list", "UrlList", "urlList"):
            lst = v.get(k)
            if isinstance(lst, list):
                for u in lst:
                    out2 += _collect_urls(u)
        for k in ("url", "Uri", "uri", "master_url", "url_default", "masterUrl"):
            out2 += _collect_urls(v.get(k))
        return out2
    return []


def rednote_url_chain(card: object) -> list[str]:
    """Trả chuỗi URL từ note_card XHS. H264 trước, H265 sau. Không raise."""
    if not isinstance(card, dict):
        return []
    video = card.get("video")
    if not isinstance(video, dict):
        return []
    media = video.get("media")
    stream = media.get("stream") if isinstance(media, dict) else None
    if not isinstance(stream, dict):
        return []

    def _order(k: object) -> tuple[int, str]:
        ks = str(k).lower()
        return (0 if "264" in ks or "avc" in ks else 1, str(k))

    ordered_keys = sorted(stream.keys(), key=_order)
    out: list[str] = []
    for k in ordered_keys:
        out += _collect_urls(stream[k])
    return dedupe_urls(out)
