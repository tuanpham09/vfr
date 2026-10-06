from __future__ import annotations

import re
from typing import Iterator

from core.pipeline.counts import parse_count


def walk(obj: object, _depth: int = 0) -> Iterator[dict]:
    """Duyệt đệ quy mọi dict trong JSON (chịu được việc nền tảng đổi cấu trúc bọc ngoài)."""
    if _depth > 30:
        return
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v, _depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, _depth + 1)


def dig(d: object, *path: object, default: object = None) -> object:
    cur = d
    for k in path:
        if isinstance(cur, dict):
            cur = cur.get(k)
        elif isinstance(cur, list) and isinstance(k, int) and -len(cur) <= k < len(cur):
            cur = cur[k]
        else:
            return default
        if cur is None:
            return default
    return cur


def as_str(v: object) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(int(v)) if float(v).is_integer() else str(v)
    return ""


def first_url(v: object) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("url_list", "UrlList", "urlList"):
            lst = v.get(k)
            if isinstance(lst, list) and lst and isinstance(lst[0], str):
                return lst[0]
        for k in ("url", "Uri", "uri", "master_url", "url_default"):
            if isinstance(v.get(k), str):
                return v[k]
    if isinstance(v, list) and v:
        return first_url(v[0])
    return ""


def to_epoch(v: object) -> int | None:
    try:
        n = int(float(v))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n // 1000 if n > 10**12 else n


_TAG = re.compile(r"#([^\s#@,，。!！?？\[\]]+)")


def hashtags_from_text(text: str) -> list[str]:
    return _TAG.findall(text or "")


def read_counts(src: dict, mapping: dict[str, tuple[str, ...]]) -> tuple[dict[str, int | None], bool]:
    """mapping: field -> các key ứng viên (ưu tiên từ trái). Trả (giá trị, có_xấp_xỉ)."""
    out: dict[str, int | None] = {}
    approx_any = False
    for fld, keys in mapping.items():
        out[fld] = None
        for k in keys:
            if k in src and src[k] is not None:
                val, approx = parse_count(src[k])
                if val is not None:
                    out[fld] = val
                    approx_any = approx_any or approx
                    break
    return out, approx_any


def dedupe_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    res = []
    for t in tags:
        t = t.strip().lstrip("#")
        if t and t.lower() not in seen:
            seen.add(t.lower())
            res.append(t)
    return res
