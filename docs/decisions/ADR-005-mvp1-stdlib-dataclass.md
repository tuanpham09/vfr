# ADR-005 — MVP đợt 1: dataclass, sqlite3, logging chuẩn, tự dựng bằng thư viện chuẩn
**Quyết định:** đợt 1 dùng `dataclasses`, `sqlite3`, `logging`, `unittest` thay cho Pydantic/SQLModel/loguru/pytest đã nêu ở docs trước. Chỉ phụ thuộc ngoài: PySide6, websockets.
**Lý do:** ít phụ thuộc, test lõi chạy được ở mọi môi trường. Normalizer vốn phải chịu được JSON thiếu trường nên dùng accessor phòng thủ (`dig`, `read_counts`).
**Hệ quả:** có thể chuyển sang Pydantic sau mà không đổi ranh giới lớp. Docs `ARCHITECTURE.md`/`LINTS.md` mô tả đích đến; đợt 1 chưa có import-linter.
**Điều chỉnh khác:** extension chuyển *mọi* JSON của API sang app; app lọc bằng normalizer + `EXCLUDE_API` (không phụ thuộc danh sách URL cứng). "Số video" tính cho mỗi mục nhập.
