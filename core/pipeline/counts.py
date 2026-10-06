"""parse_count: chuẩn hóa số liệu tương tác. Hàm thuần, không bao giờ raise."""
from __future__ import annotations

import math
import re

_UNITS = {"万": 1e4, "w": 1e4, "W": 1e4, "亿": 1e8, "k": 1e3, "K": 1e3,
          "m": 1e6, "M": 1e6, "b": 1e9, "B": 1e9}
_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)*)\s*([万亿wWkKmMbB]?)\s*(\+?)\s*$")


def parse_count(value: object) -> tuple[int | None, bool]:
    """Trả (giá_trị, là_xấp_xỉ). None = không có số liệu."""
    try:
        if value is None or isinstance(value, bool):
            return None, False
        if isinstance(value, (int, float)):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return None, False
            if value < 0:
                return None, False
            return int(round(value)), False
        if not isinstance(value, str):
            return None, False
        m = _RE.match(value)
        if not m:
            return None, False
        num, unit, plus = m.groups()
        if unit:
            n = float(num.replace(",", "."))
            return int(round(n * _UNITS[unit])), True
        if "," in num:
            n = float(num.replace(",", ""))
        else:
            n = float(num)
        approx = bool(plus) or ("." in num)
        return int(round(n)), approx
    except (ValueError, OverflowError):
        return None, False
