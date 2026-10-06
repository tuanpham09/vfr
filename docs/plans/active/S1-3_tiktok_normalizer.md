# S1-3 — Normalizer TikTok (task mẫu)
**Mục tiêu:** `normalize(api: str, payload: dict) -> list[VideoItem]` cho TikTok từ fixture thật.
**Đọc trước:** `design/DATA_MODEL.md`, `platforms/tiktok.md`, `harness/FIXTURES.md`.
**File:** `core/pipeline/normalizers/tiktok.py`, `tests/unit/test_tiktok_normalizer.py`, `tests/fixtures/tiktok/*`.
**Không làm:** IO, gọi mạng, đọc giờ hiện tại, parse trong extension.
**Bước:** (1) xác nhận tên trường từ fixture, cập nhật `[VERIFY]` trong `platforms/tiktok.md`; (2) Pydantic model cho payload thô, `extra="ignore"`; (3) map sang `VideoItem`; (4) snapshot test ≥ 3 fixture; (5) case thiếu trường không raise, trả `None`/bỏ item kèm log.
**Xong khi:** `make check` xanh; hashtag, stats, cover, play_url, has_cart được điền đúng trên fixture; docs đã gỡ [VERIFY] tương ứng.
