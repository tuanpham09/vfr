from __future__ import annotations

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, QSize, Qt, QTimer, QUrl, Signal)
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from core.types import PLATFORM_LABEL, VideoItem

COLS = ["", "Ảnh", "Nền tảng", "Mô tả", "Tác giả", "Views", "Tim", "Comment", "Lưu", "🛒", "👤", "Sát"]
C_CHECK, C_THUMB, C_PLAT, C_DESC, C_AUTHOR, C_VIEWS, C_LIKE, C_CMT, C_SAVE, C_CART, C_FACE, C_REL = range(12)
THUMB = QSize(60, 80)
_NUMERIC = {C_VIEWS: "play", C_LIKE: "like", C_CMT: "comment", C_SAVE: "collect", C_REL: "relevance"}


def fmt(n: int | None, approx: bool) -> str:
    if n is None:
        return "—"
    return ("~" if approx else "") + f"{n:,}"


class VideoModel(QAbstractTableModel):
    selectionChanged = Signal()
    countsChanged = Signal()

    def __init__(self, page_size: int = 50, parent=None) -> None:
        super().__init__(parent)
        self.page_size = page_size
        self._all: list[VideoItem] = []
        self._index: dict[tuple[str, str], int] = {}
        self._view: list[VideoItem] = []
        self._checked: set[tuple[str, str]] = set()
        self._text = ""
        self._page = 0
        self._sort: tuple[int, Qt.SortOrder] | None = None
        self._thumbs: dict[str, QPixmap] = {}
        self._pending: set[str] = set()
        self._net = QNetworkAccessManager(self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(150)
        self._timer.timeout.connect(self._rebuild)

    # ---------- dữ liệu ----------
    def load(self, items: list[VideoItem]) -> None:
        self._all, self._index = [], {}
        for it in items:
            self._index[it.key] = len(self._all)
            self._all.append(it)
        self._rebuild()

    def upsert(self, item: VideoItem) -> None:
        i = self._index.get(item.key)
        if i is None:
            self._index[item.key] = len(self._all)
            self._all.append(item)
        else:
            self._all[i] = item
        if not self._timer.isActive():
            self._timer.start()

    def clear(self) -> None:
        self._all, self._index, self._checked = [], {}, set()
        self._rebuild()

    def _rebuild(self) -> None:
        t = self._text.lower()
        items = [v for v in self._all if not t or t in v.desc.lower() or t in v.author_name.lower()
                 or t in v.query.lower()]
        if self._sort:
            col, order = self._sort
            attr = _NUMERIC.get(col)
            if attr:
                have = [v for v in items if getattr(v, attr) is not None]
                none = [v for v in items if getattr(v, attr) is None]
                have.sort(key=lambda v: getattr(v, attr), reverse=(order == Qt.SortOrder.DescendingOrder))
                items = have + none
        self.beginResetModel()
        self._view = items
        self._page = min(self._page, max(self.pages() - 1, 0))
        self.endResetModel()
        self.countsChanged.emit()
        self.selectionChanged.emit()

    # ---------- phân trang / lọc ----------
    def set_text_filter(self, text: str) -> None:
        self._text, self._page = text.strip(), 0
        self._rebuild()

    def pages(self) -> int:
        return max((len(self._view) + self.page_size - 1) // self.page_size, 0)

    def page(self) -> int:
        return self._page

    def total(self) -> int:
        return len(self._view)

    def set_page(self, p: int) -> None:
        p = max(0, min(p, max(self.pages() - 1, 0)))
        if p != self._page:
            self.beginResetModel()
            self._page = p
            self.endResetModel()
            self.countsChanged.emit()

    def _slice(self) -> list[VideoItem]:
        s = self._page * self.page_size
        return self._view[s:s + self.page_size]

    # ---------- chọn ----------
    def selected_items(self) -> list[VideoItem]:
        return [v for v in self._all if v.key in self._checked]

    def selected_count(self) -> int:
        return len(self._checked)

    def select_all(self, on: bool) -> None:
        if on:
            self._checked |= {v.key for v in self._view}
        else:
            self._checked.clear()
        if self.rowCount():
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, 0))
        self.selectionChanged.emit()

    # ---------- Qt model ----------
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._slice())

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(COLS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return COLS[section]
        return None

    def flags(self, index):
        f = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == C_CHECK:
            f |= Qt.ItemFlag.ItemIsUserCheckable
        return f

    def sort(self, column: int, order=Qt.SortOrder.AscendingOrder) -> None:
        self._sort = (column, order) if column in _NUMERIC else None
        self._rebuild()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        rows = self._slice()
        if index.row() >= len(rows):
            return None
        v, c = rows[index.row()], index.column()
        if role == Qt.ItemDataRole.CheckStateRole and c == C_CHECK:
            return Qt.CheckState.Checked if v.key in self._checked else Qt.CheckState.Unchecked
        if role == Qt.ItemDataRole.DecorationRole and c == C_THUMB:
            return self._thumb(v.cover_url)
        if role == Qt.ItemDataRole.ToolTipRole and c in (C_DESC, C_AUTHOR):
            return v.desc
        if role == Qt.ItemDataRole.TextAlignmentRole and c >= C_VIEWS:
            return int(Qt.AlignmentFlag.AlignCenter)
        if role == Qt.ItemDataRole.ForegroundRole and c in (C_VIEWS,) and v.platform != "tiktok":
            return QColor("#4b5563")
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if c == C_PLAT:
            return PLATFORM_LABEL.get(v.platform, v.platform)
        if c == C_DESC:
            return v.desc or "(không có mô tả)"
        if c == C_AUTHOR:
            return v.author_name or v.author_id
        if c == C_VIEWS:
            return fmt(v.play, v.stats_approx) if v.platform == "tiktok" else "—"
        if c == C_LIKE:
            return fmt(v.like, v.stats_approx)
        if c == C_CMT:
            return fmt(v.comment, v.stats_approx)
        if c == C_SAVE:
            return fmt(v.collect, v.stats_approx)
        if c == C_CART:
            return "🛒" if v.has_cart else ("—" if v.has_cart is None else "")
        if c == C_FACE:
            return "👤" if v.has_face else ("○" if v.has_face is False else "?")
        if c == C_REL:
            return "—" if v.relevance is None else f"{round(v.relevance * 100)}%"
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if role == Qt.ItemDataRole.CheckStateRole and index.column() == C_CHECK:
            v = self._slice()[index.row()]
            if value == Qt.CheckState.Checked or value == 2:
                self._checked.add(v.key)
            else:
                self._checked.discard(v.key)
            self.dataChanged.emit(index, index)
            self.selectionChanged.emit()
            return True
        return False

    # ---------- thumbnail lazy ----------
    def _thumb(self, url: str):
        if not url:
            return None
        pm = self._thumbs.get(url)
        if pm is not None:
            return pm
        if url not in self._pending and len(self._pending) < 8:
            self._pending.add(url)
            req = QNetworkRequest(QUrl(url))
            req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
            req.setRawHeader(b"User-Agent", b"Mozilla/5.0")
            reply = self._net.get(req)
            reply.finished.connect(lambda r=reply, u=url: self._on_thumb(r, u))
        return None

    def _on_thumb(self, reply: QNetworkReply, url: str) -> None:
        self._pending.discard(url)
        pm = QPixmap()
        if reply.error() == QNetworkReply.NetworkError.NoError and pm.loadFromData(bytes(reply.readAll())):
            self._thumbs[url] = pm.scaled(THUMB, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
        else:
            self._thumbs[url] = QPixmap(1, 1)
        reply.deleteLater()
        if self.rowCount():
            self.dataChanged.emit(self.index(0, C_THUMB), self.index(self.rowCount() - 1, C_THUMB),
                                  [Qt.ItemDataRole.DecorationRole])
