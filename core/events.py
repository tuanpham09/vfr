from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.types import VideoItem


@dataclass
class Log:
    level: str
    msg: str


@dataclass
class VideoUpsert:
    item: VideoItem
    is_new: bool


@dataclass
class ExtStatus:
    connected: bool
    version: str = ""


@dataclass
class JobState:
    state: str  # running | done | stopped | error
    msg: str = ""


@dataclass
class Paused:
    reason: str  # login_required | captcha
    platform: str
    input: str
    url: str


@dataclass
class Progress:
    got: int
    target: int
    input: str
    index: int
    total: int


class EventBus:
    def __init__(self) -> None:
        self._subs: list[Callable[[object], None]] = []

    def subscribe(self, cb: Callable[[object], None]) -> None:
        self._subs.append(cb)

    def publish(self, ev: object) -> None:
        for cb in list(self._subs):
            try:
                cb(ev)
            except Exception:  # noqa: BLE001 - subscriber lỗi không được làm hỏng core
                pass

    def log(self, msg: str, level: str = "info") -> None:
        self.publish(Log(level, msg))
