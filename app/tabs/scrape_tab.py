from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDialog,
                               QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QScrollArea, QSpinBox, QTableView, QVBoxLayout, QWidget)

from app.bridge import Bridge
from app.models.video_model import (C_AUTHOR, C_CART, C_CHECK, C_CMT, C_DESC, C_FACE, C_LIKE, C_PLAT,
                                    C_REL, C_SAVE, C_THUMB, C_VIEWS, THUMB, VideoModel)
from core.api import CoreApi
from core.types import PLATFORM_LABEL, ScrapeJob

PLATFORMS = [("tiktok", "TikTok"), ("douyin", "Douyin"), ("xhs", "Xiaohongshu")]
MODES = [("keyword", "Từ khóa tìm kiếm"), ("user", "@User"), ("hashtag", "Hashtag"), ("link", "Link video")]
HINTS = {
    "keyword": "Từ khóa (mỗi dòng 1 mục)", "user": "@User hoặc link trang cá nhân (mỗi dòng 1 mục)",
    "hashtag": "Hashtag (mỗi dòng 1 mục)", "link": "Link video (mỗi dòng 1 mục)",
}
LOGIN_URL = {"tiktok": "https://www.tiktok.com/login", "douyin": "https://www.douyin.com/",
             "xhs": "https://www.xiaohongshu.com/explore"}


def _panel() -> QFrame:
    f = QFrame()
    f.setObjectName("panel")
    return f


def _h(text: str) -> QLabel:
    l = QLabel(text)
    l.setObjectName("h")
    return l


class PauseDialog(QDialog):
    """Hiện khi extension báo login_required / captcha."""
    RESUME, SKIP = 1, 2

    def __init__(self, reason: str, platform: str, text: str, parent=None) -> None:
        super().__init__(parent)
        label = PLATFORM_LABEL.get(platform, platform)
        self.setWindowTitle("Tạm dừng")
        lay = QVBoxLayout(self)
        if reason == "login_required":
            msg = f"Hãy đăng nhập {label} trong Chrome rồi bấm Tiếp tục."
        else:
            msg = f"{label} yêu cầu xác minh (captcha). Hãy xử lý trong Chrome rồi bấm Tiếp tục."
        lay.addWidget(QLabel(msg))
        lay.addWidget(QLabel(f"Mục đang chạy: {text}"))
        row = QHBoxLayout()
        b_open = QPushButton("Mở trang đăng nhập")
        b_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(LOGIN_URL.get(platform, ""))))
        b_ok = QPushButton("Tiếp tục")
        b_ok.setObjectName("primary")
        b_ok.clicked.connect(lambda: self.done(self.RESUME))
        b_skip = QPushButton("Bỏ qua mục này")
        b_skip.clicked.connect(lambda: self.done(self.SKIP))
        for b in (b_open, b_ok, b_skip):
            row.addWidget(b)
        lay.addLayout(row)


class ScrapeTab(QWidget):
    def __init__(self, api: CoreApi, bridge: Bridge, goto_process=None, parent=None) -> None:
        super().__init__(parent)
        self.api, self.bridge, self._goto = api, bridge, goto_process
        self.platform, self.running = "tiktok", False
        self.model = VideoModel(api.cfg.page_size, self)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        root.addWidget(self._left(), 0)
        root.addWidget(self._right(), 1)

        b = bridge
        b.log.connect(self.add_log)
        b.video.connect(lambda item, new: self.model.upsert(item))
        b.ext.connect(self.on_ext)
        b.job.connect(self.on_job)
        b.paused.connect(self.on_paused)
        b.progress.connect(self.on_progress)
        self.model.countsChanged.connect(self._refresh_counts)
        self.model.selectionChanged.connect(self._refresh_counts)
        self.model.load(api.list_videos())
        self._on_platform("tiktok")
        self.on_ext(False, "")

    # ---------- panel trái ----------
    def _left(self) -> QWidget:
        panel = _panel()
        panel.setFixedWidth(490)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)
        lay.addWidget(_h("1. Chọn nền tảng và mục tiêu"))

        seg = QFrame()
        seg.setObjectName("segbar")
        sl = QHBoxLayout(seg)
        sl.setContentsMargins(4, 4, 4, 4)
        self.plat_group = QButtonGroup(self)
        for key, label in PLATFORMS:
            btn = QPushButton(label)
            btn.setObjectName("seg")
            btn.setCheckable(True)
            btn.setChecked(key == "tiktok")
            btn.clicked.connect(lambda _=False, k=key: self._on_platform(k))
            self.plat_group.addButton(btn)
            sl.addWidget(btn)
        lay.addWidget(seg)

        row = QHBoxLayout()
        row.addWidget(_h("Chế độ cào:"))
        self.mode = QComboBox()
        for key, label in MODES:
            self.mode.addItem(label, key)
        self.mode.currentIndexChanged.connect(self._on_mode)
        row.addWidget(self.mode, 1)
        lay.addLayout(row)

        self.hint = _h(HINTS["keyword"])
        lay.addWidget(self.hint)
        self.text = QPlainTextEdit()
        self.text.setMinimumHeight(180)
        lay.addWidget(self.text, 1)

        self.cart = QCheckBox("Chỉ lấy video có giỏ hàng")
        self.cart.setStyleSheet("color:#fbbf24;font-weight:600;")
        lay.addWidget(self.cart)
        self.face = QPushButton("Phân biệt video có mặt người")
        self.face.setEnabled(False)
        self.face.setToolTip("Sắp có ở bản sau (badge 👤 hiện là '?')")
        lay.addWidget(self.face)

        lay.addWidget(_h("2. Cấu hình cào và xác thực"))
        row = QHBoxLayout()
        row.addWidget(QLabel("Số video:"))
        self.n = QSpinBox()
        self.n.setRange(1, 5000)
        self.n.setValue(30)
        self.n.setToolTip("Số video cho MỖI mục nhập")
        row.addWidget(self.n)
        self.min_label = QLabel("Lượt xem tối thiểu:")
        row.addWidget(self.min_label)
        self.minv = QSpinBox()
        self.minv.setRange(0, 2_000_000_000)
        row.addWidget(self.minv)
        lay.addLayout(row)

        row = QHBoxLayout()
        self.rel_label = QLabel("Độ sát từ khóa (%):")
        row.addWidget(self.rel_label)
        self.rel = QSpinBox()
        self.rel.setRange(0, 100)
        self.rel.setValue(50)
        self.rel.setToolTip("Loại video có mô tả/hashtag không khớp từ khóa. 0 = chỉ gắn nhãn, không loại. "
                            "Từ khóa ngắn chỉ có vài mức điểm (vd 3 chữ Hán: 0/50/100%). "
                            "Douyin/XHS mặc định 0 vì nền tảng đã tự xếp theo ngữ nghĩa.")
        row.addWidget(self.rel)
        row.addStretch(1)
        lay.addLayout(row)

        row = QHBoxLayout()
        self.btn_start = QPushButton("Bắt đầu cào video")
        self.btn_start.setObjectName("primary")
        self.btn_start.clicked.connect(self._start)
        self.btn_stop = QPushButton("Dừng")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.clicked.connect(self._stop)
        self.btn_stop.setEnabled(False)
        row.addWidget(self.btn_start, 3)
        row.addWidget(self.btn_stop, 1)
        lay.addLayout(row)

        self.ext_label = QLabel()
        lay.addWidget(self.ext_label)

        lay.addWidget(_h("3. Tải trực tiếp"))
        row = QHBoxLayout()
        self.direct = QLineEdit()
        self.direct.setPlaceholderText("Dán link video (sắp có)")
        self.direct.setEnabled(False)
        b = QPushButton("Tải")
        b.setEnabled(False)
        row.addWidget(self.direct, 1)
        row.addWidget(b)
        lay.addLayout(row)
        return panel

    # ---------- panel phải ----------
    def _right(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        top = _panel()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(12, 10, 12, 10)
        head = QHBoxLayout()
        self.list_title = _h("Danh sách Video (0 video | 0 đã chọn)")
        head.addWidget(self.list_title)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Lọc theo mô tả / tác giả / từ khóa")
        self.search.setFixedWidth(240)
        self.search.textChanged.connect(self.model.set_text_filter)
        head.addWidget(self.search)
        head.addStretch(1)
        b1 = QPushButton("Chuyển đến phần xử lý")
        b1.clicked.connect(self._to_process)
        b2 = QPushButton("Bỏ chọn")
        b2.clicked.connect(lambda: self.model.select_all(False))
        b3 = QPushButton("Chọn tất cả")
        b3.clicked.connect(lambda: self.model.select_all(True))
        for b in (b1, b2, b3):
            head.addWidget(b)
        tl.addLayout(head)

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(THUMB.height() + 12)
        self.table.setIconSize(THUMB)
        self.table.setWordWrap(True)
        self.table.setShowGrid(False)
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(C_DESC, QHeaderView.ResizeMode.Stretch)
        for c, wd in ((C_CHECK, 36), (C_THUMB, 72), (C_PLAT, 92), (C_AUTHOR, 130), (C_VIEWS, 90),
                      (C_LIKE, 80), (C_CMT, 80), (C_SAVE, 80), (C_CART, 46), (C_FACE, 46), (C_REL, 60)):
            self.table.setColumnWidth(c, wd)
        tl.addWidget(self.table, 1)

        pg = QHBoxLayout()
        self.prev = QPushButton("Trước")
        self.prev.clicked.connect(lambda: self.model.set_page(self.model.page() - 1))
        self.nextb = QPushButton("Sau")
        self.nextb.clicked.connect(lambda: self.model.set_page(self.model.page() + 1))
        self.page_label = QLabel("Trang 0 / 0 (Tổng 0 video)")
        self.page_label.setObjectName("muted")
        pg.addWidget(self.prev)
        pg.addStretch(1)
        pg.addWidget(self.page_label)
        pg.addStretch(1)
        pg.addWidget(self.nextb)
        tl.addLayout(pg)
        lay.addWidget(top, 1)

        logp = _panel()
        ll = QVBoxLayout(logp)
        ll.setContentsMargins(12, 10, 12, 10)
        hr = QHBoxLayout()
        hr.addWidget(_h("Nhật ký Cào dữ liệu:"))
        hr.addStretch(1)
        clr = QPushButton("Xóa log")
        hr.addWidget(clr)
        ll.addLayout(hr)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setFixedHeight(150)
        clr.clicked.connect(self.log.clear)
        ll.addWidget(self.log)
        lay.addWidget(logp, 0)
        return w

    # ---------- hành vi ----------
    def _on_platform(self, key: str) -> None:
        self.platform = key
        self.rel.setValue(50 if key == "tiktok" else 0)
        self.min_label.setText("Lượt xem tối thiểu:" if key == "tiktok" else "Lượt tim tối thiểu:")
        xhs = key == "xhs"
        self.cart.setEnabled(not xhs)
        if xhs:
            self.cart.setChecked(False)
        self.cart.setToolTip("XHS không có giỏ hàng" if xhs else "")
        self.table.setColumnHidden(C_VIEWS, False)
        self._update_hint()

    def _on_mode(self) -> None:
        self._update_hint()

    def _update_hint(self) -> None:
        mode = self.mode.currentData()
        text = HINTS[mode]
        if mode == "user" and self.platform != "tiktok":
            text = "Link trang cá nhân (mỗi dòng 1 mục)"
        self.hint.setText(text)
        kw = mode == "keyword"
        self.rel.setEnabled(kw)
        self.rel_label.setEnabled(kw)

    def _inputs(self) -> list[str]:
        seen, out = set(), []
        for line in self.text.toPlainText().splitlines():
            s = line.strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        return out

    def _start(self) -> None:
        inputs = self._inputs()
        if not inputs:
            self.add_log("warn", "Hãy nhập từ khóa / user / hashtag / link (mỗi dòng 1 mục).")
            return
        job = ScrapeJob(self.platform, self.mode.currentData(), inputs, self.n.value(),
                        self.minv.value(), self.cart.isChecked(), self.rel.value() / 100)
        self._set_running(True)
        self.api.start_scrape(job)

    def _stop(self) -> None:
        self.add_log("info", "Đang dừng…")
        self.api.stop()

    def _set_running(self, on: bool) -> None:
        self.running = on
        self.btn_start.setEnabled(not on)
        self.btn_stop.setEnabled(on)

    def on_job(self, state: str, msg: str) -> None:
        if state in ("done", "stopped", "error"):
            self._set_running(False)
            self.add_log("info", {"done": "Hoàn tất.", "stopped": "Đã dừng.", "error": "Lỗi: " + msg}[state])

    def on_progress(self, got: int, target: int, text: str) -> None:
        self.btn_start.setText(f"Đang cào… {got}/{target}") if self.running else None

    def on_paused(self, reason: str, platform: str, text: str, url: str) -> None:
        dlg = PauseDialog(reason, platform, text, self)
        res = dlg.exec()
        self.api.decide("resume" if res == PauseDialog.RESUME else "skip")

    def on_ext(self, connected: bool, ver: str) -> None:
        if connected:
            self.ext_label.setText(f"Chrome Ext: Đã kết nối{(' v' + ver) if ver else ''}")
            self.ext_label.setStyleSheet("color:#34d399;")
        else:
            self.ext_label.setText("Chrome Ext: Đang tìm extension")
            self.ext_label.setStyleSheet("color:#fbbf24;")

    def add_log(self, level: str, msg: str) -> None:
        color = {"error": "#f87171", "warn": "#fbbf24"}.get(level, "#cbd5e1")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.appendHtml(f'<span style="color:{color}">[{ts}] {msg}</span>')
        if not self.running:
            self.btn_start.setText("Bắt đầu cào video")

    def _refresh_counts(self) -> None:
        self.list_title.setText(f"Danh sách Video ({self.model.total()} video | "
                                f"{self.model.selected_count()} đã chọn)")
        pages = self.model.pages()
        self.page_label.setText(f"Trang {self.model.page() + 1 if pages else 0} / {pages} "
                                f"(Tổng {self.model.total()} video)")
        self.prev.setEnabled(self.model.page() > 0)
        self.nextb.setEnabled(self.model.page() + 1 < pages)

    def _to_process(self) -> None:
        n = self.model.selected_count()
        self.add_log("info", f"Đã đánh dấu {n} video cho phần xử lý (tính năng xử lý sẽ có ở bản sau).")
        if self._goto:
            self._goto()
