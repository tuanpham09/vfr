"""Chuyển event của core (thread asyncio) sang Qt signal (thread UI)."""
from PySide6.QtCore import QObject, Signal

from core import events as ev


class Bridge(QObject):
    log = Signal(str, str)
    video = Signal(object, bool)
    ext = Signal(bool, str)
    job = Signal(str, str)
    paused = Signal(str, str, str, str)
    progress = Signal(int, int, str)

    def handle(self, e: object) -> None:  # gọi từ thread core; emit signal là thread-safe
        if isinstance(e, ev.Log):
            self.log.emit(e.level, e.msg)
        elif isinstance(e, ev.VideoUpsert):
            self.video.emit(e.item, e.is_new)
        elif isinstance(e, ev.ExtStatus):
            self.ext.emit(e.connected, e.version)
        elif isinstance(e, ev.JobState):
            self.job.emit(e.state, e.msg)
        elif isinstance(e, ev.Paused):
            self.paused.emit(e.reason, e.platform, e.input, e.url)
        elif isinstance(e, ev.Progress):
            self.progress.emit(e.got, e.target, e.input)
