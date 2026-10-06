# S0-6 — parse_count
**Mục tiêu:** hàm thuần chuẩn hóa mọi số liệu tương tác về `(int | None, is_approx)`.
**Đọc trước:** `design/DATA_MODEL.md` (mục Số liệu tương tác), `design/FILTERS_AND_FACE.md` (bảng parse_count).
**File:** `core/pipeline/counts.py`, `tests/unit/test_counts.py`.
**Không làm:** IO, regex phức tạp khó đọc, raise exception.
**Bước:** (1) viết bảng test ≥ 25 case (số nguyên, chuỗi có dấu phẩy, 万/w/W, 亿, K/M/B, `10+`, chữ thay số, rỗng, None, âm, NaN, rác); (2) cài đặt; (3) hypothesis: không bao giờ raise; (4) cập nhật `[VERIFY]` khi có fixture XHS thật.
**Xong khi:** `make check` xanh; normalizer sau này chỉ gọi hàm này để lấy số liệu.
