"""Độ sát từ khóa dạng luật (thuần, stdlib). Không dùng embedding (ADR-002).

- Latin: chuẩn hóa chữ thường + bỏ dấu; điểm = tỉ lệ từ của truy vấn có mặt trong văn bản.
- CJK: **không** bắt buộc đúng từng cặp ký tự liền kề. Điểm = max(tỉ lệ bigram khớp, 0.85 × tỉ lệ
  ký tự của truy vấn có mặt trong văn bản). Nhờ đó "口红测评推荐" vẫn khớp mô tả "口红 推荐".
- Phồn thể → giản thể nếu cài `opencc-python-reimplemented` (tùy chọn).
- Truy vấn không có chữ Hán trên Douyin/XHS **không đo được** → `measurable()` trả False,
  runner bỏ qua lọc.
"""
from __future__ import annotations

import re
import unicodedata

from core.types import VideoItem

_CJK_RANGE = "㐀-鿿"
_CJK = re.compile(f"[{_CJK_RANGE}]")
_SPLIT = re.compile(r"[\s,，、/|;；]+")
_RUNS = re.compile(f"[{_CJK_RANGE}]+|[^{_CJK_RANGE}]+")
_JUNK = re.compile(f"[^\\w{_CJK_RANGE}]+")

CJK_CHAR_WEIGHT = 0.85

try:  # tùy chọn
    from opencc import OpenCC  # type: ignore[import-not-found]

    _T2S = OpenCC("t2s")
except Exception:  # noqa: BLE001
    _T2S = None


def has_cjk(text: str) -> bool:
    return bool(_CJK.search(text or ""))


def normalize_text(s: str) -> str:
    s = s or ""
    if _T2S is not None and has_cjk(s):
        try:
            s = _T2S.convert(s)
        except Exception:  # noqa: BLE001
            pass
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("đ", "d")


def _split(query: str) -> tuple[list[str], list[str]]:
    """(các cụm chữ Hán, các từ Latin ≥ 2 ký tự) của truy vấn đã chuẩn hóa."""
    cjk_runs: list[str] = []
    latin: list[str] = []
    for chunk in _SPLIT.split(normalize_text(query)):
        chunk = _JUNK.sub("", chunk)
        for run in _RUNS.findall(chunk):
            if _CJK.match(run):
                cjk_runs.append(run)
            elif len(run) >= 2:
                latin.append(run)
    return cjk_runs, latin


def tokens(query: str) -> list[str]:
    """Token để đối chiếu/hiển thị: Hán → bigram (cụm ≤ 2 ký tự giữ nguyên), Latin → từ."""
    cjk_runs, latin = _split(query)
    out: list[str] = []
    for run in cjk_runs:
        out += [run] if len(run) <= 2 else [run[i : i + 2] for i in range(len(run) - 1)]
    out += latin
    seen: set[str] = set()
    return [t for t in out if not (t in seen or seen.add(t))]


def measurable(query: str, platform: str) -> bool:
    """Douyin/XHS: truy vấn không có chữ Hán (vd. tiếng Việt) không thể so với mô tả tiếng Trung."""
    if platform in ("douyin", "xhs"):
        return has_cjk(query)
    return True


def has_signal(item: VideoItem) -> bool:
    """False nếu không có chữ nào để chấm (desc rỗng, không hashtag) -> không nên loại."""
    return bool((item.desc or "").strip() or item.hashtags)


def relevance_score(query: str, item: VideoItem) -> float:
    cjk_runs, latin = _split(query)
    text = normalize_text(" ".join([item.desc, " ".join(item.hashtags), item.author_name]))
    parts: list[tuple[float, int]] = []  # (điểm, trọng số)
    if cjk_runs:
        chars = list(dict.fromkeys("".join(cjk_runs)))
        bigrams: list[str] = []
        for r in cjk_runs:
            bigrams += [r] if len(r) <= 2 else [r[i : i + 2] for i in range(len(r) - 1)]
        bigrams = list(dict.fromkeys(bigrams))
        bi = sum(1 for b in bigrams if b in text) / len(bigrams)
        ch = sum(1 for c in chars if c in text) / len(chars)
        parts.append((max(bi, CJK_CHAR_WEIGHT * ch), len(chars)))
    if latin:
        latin = list(dict.fromkeys(latin))
        parts.append((sum(1 for t in latin if t in text) / len(latin), len(latin)))
    if not parts:
        return 1.0
    return sum(s * w for s, w in parts) / sum(w for _, w in parts)
