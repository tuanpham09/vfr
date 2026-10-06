import sys

from PySide6.QtWidgets import QApplication

from app.bridge import Bridge
from app.main_window import MainWindow
from app.theme import QSS
from core.api import CoreApi
from core.config import Config


def main() -> int:
    qt = QApplication(sys.argv)
    qt.setStyleSheet(QSS)
    cfg = Config.load()
    api = CoreApi(cfg)
    bridge = Bridge()
    api.subscribe(bridge.handle)
    api.start()
    win = MainWindow(api, bridge)
    win.show()
    bridge.log.emit("info", f"Khởi động Video Flow Render thành công. Cổng {cfg.port}.")
    bridge.log.emit("info", "Extension: Options → nhập cổng và token trong Cài đặt của app.")
    code = qt.exec()
    api.shutdown()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
