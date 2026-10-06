"""Độ sát từ khóa dạng luật (thuần, stdlib). Không dùng embedding (ADR-002).

Chuẩn hóa: chữ thường, bỏ dấu tiếng Việt. Latin: tách theo khoảng trắng. CJK: bigram ký tự.
Điểm = tỉ lệ token của truy vấn xuất hiện trong (mô tả + hashtag + tên tác giả).
"""
from __future__ import annotations

import re
import unicodedata

from core.types import VideoItem

_CJK = r"\u3400-\u9fff"
_SPLIT = re.compile(r"[\s,，、/|;；]+")
_RUNS = re.compile(rf"[{_CJK}]+|[^{_CJK}]+")
_JUNK = re.compile(rf"[^\w{_CJK}]+")


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("đ", "d")


def tokens(query: str) -> list[str]:
    out: list[str] = []
    for chunk in _SPLIT.split(normalize_text(query)):
        chunk = _JUNK.sub("", chunk)
        for run in _RUNS.findall(chunk):
            if re.match(rf"[{_CJK}]", run):
                out += [run] if len(run) <= 2 else [run[i:i + 2] for i in range(len(run) - 1)]
            elif len(run) >= 2:
                out.append(run)
    seen: set[str] = set()
    return [t for t in out if not (t in seen or seen.add(t))]


def has_signal(item: VideoItem) -> bool:
    """False nếu không có chữ nào để chấm (desc rỗng, không hashtag) -> không nên loại."""
    return bool((item.desc or "").strip() or item.hashtags)


def relevance_score(query: str, item: VideoItem) -> float:
    toks = tokens(query)
    if not toks:
        return 1.0
    text = normalize_text(" ".join([item.desc, " ".join(item.hashtags), item.author_name]))
    phrase = _JUNK.sub("", normalize_text(query))
    if phrase and phrase in _JUNK.sub("", text):   # cả cụm nằm trong text -> khớp hoàn toàn
        return 1.0
    return sum(1 for t in toks if t in text) / len(toks)
