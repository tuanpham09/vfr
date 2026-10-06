from PySide6.QtWidgets import (QCheckBox, QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)

from core.config import Config


class SettingsTab(QWidget):
    def __init__(self, cfg: Config, parent=None) -> None:
        super().__init__(parent)
        self.cfg = cfg
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Thay đổi cổng/token cần khởi động lại app và nhập lại trong Options của extension."))
        form = QFormLayout()
        self.port = QSpinBox(); self.port.setRange(1024, 65535); self.port.setValue(cfg.port)
        self.token = QLineEdit(cfg.token); self.token.setReadOnly(True)
        self.save_dir = QLineEdit(cfg.save_dir)
        self.dmin = QDoubleSpinBox(); self.dmin.setRange(0, 600); self.dmin.setValue(cfg.task_delay_min)
        self.dmax = QDoubleSpinBox(); self.dmax.setRange(0, 600); self.dmax.setValue(cfg.task_delay_max)
        self.scrolls = QSpinBox(); self.scrolls.setRange(5, 300); self.scrolls.setValue(cfg.max_scrolls)
        self.raw = QCheckBox("Lưu JSON thô (để làm fixture/gỡ lỗi)"); self.raw.setChecked(cfg.save_raw_captures)
        for label, w in (("Cổng WS", self.port), ("Token (dán vào extension)", self.token),
                         ("Thư mục lưu video", self.save_dir), ("Nghỉ giữa các mục, tối thiểu (s)", self.dmin),
                         ("Nghỉ giữa các mục, tối đa (s)", self.dmax), ("Số lần cuộn tối đa", self.scrolls),
                         ("", self.raw)):
            form.addRow(label, w)
        lay.addLayout(form)
        lay.addWidget(QLabel(f"Thư mục capture: {cfg.captures_dir}"))
        b = QPushButton("Lưu cài đặt")
        b.clicked.connect(self.save)
        lay.addWidget(b)
        self.status = QLabel("")
        lay.addWidget(self.status)
        lay.addStretch(1)

    def save(self) -> None:
        c = self.cfg
        c.port, c.save_dir = self.port.value(), self.save_dir.text()
        c.task_delay_min = min(self.dmin.value(), self.dmax.value())
        c.task_delay_max = max(self.dmin.value(), self.dmax.value())
        c.max_scrolls, c.save_raw_captures = self.scrolls.value(), self.raw.isChecked()
        c.save()
        self.status.setText("Đã lưu. Khởi động lại app để áp dụng cổng mới.")
