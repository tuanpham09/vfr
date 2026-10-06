QSS = """
* { font-family: "Segoe UI", "Inter", sans-serif; font-size: 13px; color: #e5e7eb; }
QMainWindow, QWidget#root { background: #0b111b; }
QFrame#panel { background: #0f1722; border-radius: 10px; }
QLabel#h { font-size: 15px; font-weight: 700; color: #f3f4f6; }
QLabel#muted { color: #9ca3af; }
QPushButton { background: #1b2433; border: none; border-radius: 8px; padding: 9px 16px; font-weight: 600; }
QPushButton:hover { background: #253046; }
QPushButton:disabled { color: #6b7280; background: #151c29; }
QPushButton#nav { padding: 14px 22px; }
QPushButton#nav:checked, QPushButton#seg:checked { background: #3b82f6; color: white; }
QPushButton#seg { background: transparent; padding: 7px 14px; border-radius: 6px; }
QPushButton#seg:hover:!checked { background: #1b2433; }
QPushButton#primary { background: #3b82f6; color: white; padding: 12px; font-size: 14px; }
QPushButton#primary:hover { background: #2f6fd8; }
QPushButton#danger { background: #dc2626; color: white; padding: 12px; font-size: 14px; }
QPushButton#danger:hover { background: #b91c1c; }
QFrame#segbar { background: #151c29; border-radius: 8px; }
QLineEdit, QPlainTextEdit, QSpinBox, QComboBox {
  background: #111a28; border: 1px solid #1f2a3c; border-radius: 6px; padding: 6px 8px; }
QPlainTextEdit { background: #0d1522; }
QComboBox QAbstractItemView { background: #111a28; selection-background-color: #3b82f6; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid #374151; border-radius: 4px; background: #111a28; }
QCheckBox::indicator:checked { background: #3b82f6; border-color: #3b82f6; }
QTableView { background: #0d1522; border: none; gridline-color: #17202f; alternate-background-color: #101a29;
  selection-background-color: #1d2c46; }
QHeaderView::section { background: #111a28; border: none; padding: 8px; font-weight: 600; color: #cbd5e1; }
QScrollBar:vertical { background: #0b111b; width: 10px; }
QScrollBar::handle:vertical { background: #26324a; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""
