"""Cấu hình app, lưu JSON ở ~/.vfr/config.json."""
from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_DIR = Path.home() / ".vfr"
CONFIG_PATH = APP_DIR / "config.json"
LLM_MODEL = "gemini-3.6-flash"  # chưa dùng ở đợt 1; giữ một chỗ duy nhất


@dataclass
class Config:
    port: int = 8765
    token: str = field(default_factory=lambda: secrets.token_urlsafe(12))
    save_dir: str = str(Path.home() / "VideoFlowRender" / "downloads")
    db_path: str = str(APP_DIR / "vfr.db")
    captures_dir: str = str(APP_DIR / "captures")
    task_delay_min: float = 20.0
    task_delay_max: float = 60.0
    max_scrolls: int = 40
    idle_limit: int = 3
    page_size: int = 50
    save_raw_captures: bool = False

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "Config":
        cfg = cls()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
            except (OSError, ValueError):
                pass
        cfg.save(path)  # đảm bảo token được lưu lại
        return cfg

    def save(self, path: Path = CONFIG_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
