"""Tách chuỗi gồm nhiều JSON nối nhau / NDJSON / SSE ('data: {...}'). Thuần, không raise."""
from __future__ import annotations

import json

_DEC = json.JSONDecoder()


def split_json_values(text: str) -> list[object]:
    out: list[object] = []
    i, n = 0, len(text)
    while i < n:
        starts = [p for p in (text.find("{", i), text.find("[", i)) if p != -1]
        if not starts:
            break
        i = min(starts)
        try:
            val, end = _DEC.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        out.append(val)
        i = end
    return out
