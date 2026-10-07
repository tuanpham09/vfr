"""SQLite (stdlib). Upsert hợp nhất: None = thiếu số liệu -> giữ cũ; 0 = giá trị thật -> ghi đè."""
from __future__ import annotations

import json
import sqlite3
import threading
import time

from core.types import VideoItem

_SCHEMA = """
CREATE TABLE IF NOT EXISTS videos(
  platform TEXT NOT NULL, video_id TEXT NOT NULL, url TEXT, desc TEXT,
  author_id TEXT, author_name TEXT, hashtags TEXT, cover_url TEXT, play_url TEXT,
  duration_s REAL, play INTEGER, like_count INTEGER, comment_count INTEGER,
  collect_count INTEGER, share_count INTEGER, stats_approx INTEGER DEFAULT 0,
  has_cart INTEGER, has_face INTEGER, status TEXT DEFAULT 'new', local_path TEXT,
  query TEXT, task_id TEXT, created_at INTEGER, first_seen REAL, updated_at REAL,
  raw_json TEXT, relevance REAL, PRIMARY KEY(platform, video_id));
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
"""
_RENAME = {"like": "like_count", "comment": "comment_count", "collect": "collect_count",
           "share": "share_count"}
_KEEP_OLD = ("status", "local_path", "has_face")
_TEXT_FIELDS = ("url", "desc", "author_id", "author_name", "cover_url", "play_url", "query", "task_id")
# Số đếm: None = thiếu số liệu -> giữ cũ; 0 = giá trị thật (video 0 tim) -> ghi đè.
# Quy ước khớp omit_unavailable ở normalizer (None≠0) và test TestOmitUnavailable.
_COUNT_FIELDS = ("play", "like", "comment", "collect", "share")
# Số khác: None = thiếu -> giữ cũ; mọi giá trị khác (kể cả 0/0.0) đều ghi đè.
_PLAIN_NUM_FIELDS = ("duration_s", "created_at", "relevance")


def _b(v: bool | None) -> int | None:
    return None if v is None else int(v)


def _nb(v: int | None) -> bool | None:
    return None if v is None else bool(v)


def merge(old: VideoItem | None, new: VideoItem) -> VideoItem:
    if old is None:
        return new
    for f in _TEXT_FIELDS:
        if not getattr(new, f):
            setattr(new, f, getattr(old, f))
    for f in _COUNT_FIELDS:
        # P0: None = thiếu số liệu -> giữ cũ; 0 = giá trị thật -> ghi đè.
        # Điều kiện cũ (0 giữ old) làm DB không bao giờ hiện 0 thật, vỡ
        # contract omit_unavailable None≠0 ở normalizer.
        if getattr(new, f) is None:
            setattr(new, f, getattr(old, f))
    for f in _PLAIN_NUM_FIELDS:
        # None = thiếu số liệu -> giữ cũ; 0/0.0 là giá trị thật -> ghi đè.
        if getattr(new, f) is None:
            setattr(new, f, getattr(old, f))
    # has_cart là tri-state bool|None: chỉ None mới giữ cũ. So sánh == 0
    # trước đây giữ stale True mãi vì False == 0 trong Python (vỡ only_cart).
    if new.has_cart is None:
        new.has_cart = old.has_cart
    if not new.hashtags:
        new.hashtags = old.hashtags
    for f in _KEEP_OLD:
        v = getattr(old, f)
        if v not in (None, "new"):
            setattr(new, f, v)
    return new


class Repo:
    def __init__(self, path: str) -> None:
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(_SCHEMA)
            cols = {r[1] for r in self._db.execute("PRAGMA table_info(videos)")}
            if "relevance" not in cols:  # DB tạo bởi bản cũ
                self._db.execute("ALTER TABLE videos ADD COLUMN relevance REAL")

    def get(self, platform: str, video_id: str) -> VideoItem | None:
        with self._lock:
            r = self._db.execute("SELECT * FROM videos WHERE platform=? AND video_id=?",
                                 (platform, video_id)).fetchone()
        return self._row(r) if r else None

    def upsert(self, item: VideoItem) -> tuple[VideoItem, bool]:
        """Trả (item đã hợp nhất, is_new)."""
        with self._lock:
            old = self.get(item.platform, item.video_id)
            merged = merge(old, item)
            now = time.time()
            first = now
            if old is not None:
                r = self._db.execute("SELECT first_seen FROM videos WHERE platform=? AND video_id=?",
                                     (item.platform, item.video_id)).fetchone()
                first = r["first_seen"] or now
            self._db.execute(
                """INSERT OR REPLACE INTO videos(platform,video_id,url,desc,author_id,author_name,
                hashtags,cover_url,play_url,duration_s,play,like_count,comment_count,collect_count,
                share_count,stats_approx,has_cart,has_face,status,local_path,query,task_id,created_at,
                first_seen,updated_at,raw_json,relevance) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (merged.platform, merged.video_id, merged.url, merged.desc, merged.author_id,
                 merged.author_name, json.dumps(merged.hashtags, ensure_ascii=False), merged.cover_url,
                 merged.play_url, merged.duration_s, merged.play, merged.like, merged.comment,
                 merged.collect, merged.share, int(merged.stats_approx), _b(merged.has_cart),
                 _b(merged.has_face), merged.status, merged.local_path, merged.query, merged.task_id,
                 merged.created_at, first, now,
                 json.dumps(merged.raw, ensure_ascii=False, default=str), merged.relevance),
            )
            self._db.commit()
        return merged, old is None

    def list_videos(self, limit: int = 5000) -> list[VideoItem]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM videos ORDER BY first_seen DESC LIMIT ?",
                                    (limit,)).fetchall()
        return [self._row(r) for r in reversed(rows)]

    def close(self) -> None:
        with self._lock:
            self._db.close()

    @staticmethod
    def _row(r: sqlite3.Row) -> VideoItem:
        try:
            tags = json.loads(r["hashtags"] or "[]")
        except ValueError:
            tags = []
        try:
            raw = json.loads(r["raw_json"] or "{}")
        except ValueError:
            raw = {}
        return VideoItem(
            platform=r["platform"], video_id=r["video_id"], url=r["url"] or "", desc=r["desc"] or "",
            author_id=r["author_id"] or "", author_name=r["author_name"] or "", hashtags=tags,
            cover_url=r["cover_url"] or "", play_url=r["play_url"] or "", duration_s=r["duration_s"],
            play=r["play"], like=r["like_count"], comment=r["comment_count"],
            collect=r["collect_count"], share=r["share_count"], stats_approx=bool(r["stats_approx"]),
            has_cart=_nb(r["has_cart"]), has_face=_nb(r["has_face"]), status=r["status"] or "new",
            local_path=r["local_path"], query=r["query"] or "", task_id=r["task_id"] or "",
            created_at=r["created_at"], relevance=r["relevance"], raw=raw,
        )
