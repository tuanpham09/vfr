from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QStackedWidget, QVBoxLayout, QWidget)

from app.bridge import Bridge
from app.tabs.scrape_tab import ScrapeTab
from app.tabs.settings_tab import SettingsTab
from core.api import CoreApi

VERSION = "0.1.0"


def _placeholder(text: str) -> QWidget:
    w = QWidget()
    l = QVBoxLayout(w)
    lab = QLabel(text)
    lab.setObjectName("muted")
    l.addStretch(1)
    l.addWidget(lab, 0, Qt.AlignmentFlag.AlignCenter)
    l.addStretch(1)
    return w


class MainWindow(QMainWindow):
    def __init__(self, api: CoreApi, bridge: Bridge) -> None:
        super().__init__()
        self.api = api
        self.setWindowTitle(f"Video Flow Render v{VERSION}")
        self.resize(1500, 860)
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        lay.setContentsMargins(12, 10, 12, 10)

        self.stack = QStackedWidget()
        self.scrape = ScrapeTab(api, bridge, goto_process=lambda: self._go(2))
        pages = [
            ("Auto", _placeholder("Tính năng Auto sẽ có ở bản sau")),
            ("1. Cào dữ liệu", self.scrape),
            ("2. Xử lý video", _placeholder("Xử lý video: sẽ có ở bản sau")),
            ("3. Review & xuất", _placeholder("Review & xuất: sẽ có ở bản sau")),
            ("Cài đặt", SettingsTab(api.cfg)),
        ]
        nav = QHBoxLayout()
        title = QLabel("VIDEO FLOW RENDER")
        title.setObjectName("h")
        title.setStyleSheet("font-size:17px;margin-right:16px;")
        nav.addWidget(title)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.btns: list[QPushButton] = []
        for i, (label, page) in enumerate(pages):
            b = QPushButton(label)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, i=i: self._go(i))
            self.group.addButton(b)
            self.btns.append(b)
            nav.addWidget(b)
            self.stack.addWidget(page)
        nav.addStretch(1)
        open_btn = QPushButton("Mở video đã cào")
        open_btn.setObjectName("nav")
        open_btn.clicked.connect(self._open_dir)
        nav.addWidget(open_btn)
        lay.addLayout(nav)
        lay.addWidget(self.stack, 1)
        self._go(1)

    def _go(self, i: int) -> None:
        self.stack.setCurrentIndex(i)
        self.btns[i].setChecked(True)

    def _open_dir(self) -> None:
        p = Path(self.api.cfg.save_dir)
        p.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
