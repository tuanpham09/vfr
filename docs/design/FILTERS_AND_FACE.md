# Bộ lọc, Face detect, Badge

## Thứ tự trong pipeline (cố định)
`normalize → dedupe → [hashtag/kênh] → relevance(mode từ khóa) → views → cart → [image_match, Đợt 2] → face_detect(cover) → badge → enqueue_download`

Video bị loại ở bước nào thì không chạy các bước sau và **không tính** vào `Số video`.

## Bộ lọc
| Bộ lọc | Quy tắc |
|---|---|
| Lượt xem tối thiểu | TikTok: `play >= min`. Douyin/XHS: `play` luôn `None`, nên **đổi nhãn UI thành "Lượt tim tối thiểu"** và lọc `like >= min`. Video có số liệu cần lọc là `None` → **loại** khi min > 0 (ghi log lý do). Giá trị 0 = tắt |
| Giỏ hàng | `has_cart is True`. XHS: bỏ qua bộ lọc |
| Sát từ khóa (luật) | **Đã cài** (`core/pipeline/relevance.py`, stdlib, không embedding). Chuẩn hóa chữ thường + bỏ dấu tiếng Việt; Latin tách theo từ (bỏ từ 1 ký tự), CJK dùng bigram ký tự. Điểm = tỉ lệ token của truy vấn có trong `desc + hashtag + tên tác giả`. Ngưỡng mặc định 0.5 (ô "Độ sát từ khóa (%)", 0 = tắt). Chỉ chạy ở mode Từ khóa; điểm lưu ở `relevance` và hiện ở cột "Sát". Nếu mọi video bị loại vì lý do này, app cảnh báo gợi ý đổi ngôn ngữ từ khóa |
| Đúng hashtag (Douyin/XHS) | Tìm `#tag` như từ khóa rồi giữ video có hashtag/`#tag` trong mô tả. TikTok dùng trang `/tag/` nên không lọc thêm |
| Đúng kênh (TikTok @user) | Giữ video có `author_id` (uniqueId) trùng handle; nếu thiếu `author_id` thì không loại. Douyin/XHS: bắt buộc dán link trang cá nhân |

Hàm thuần, bảng test tham số hóa, mỗi bộ lọc ≥ 8 case.

## Số liệu hiển thị trong bảng
| Cột | TikTok | Douyin | XHS |
|---|---|---|---|
| Views | `play` | ẩn cột | ẩn cột |
| Tim | `like` | `like` | `like` |
| Comment | `comment` | `comment` | `comment` |
| Lưu | `collect` | `collect` | `collect` |
Cột chỉ hiện khi nền tảng đang chọn có dữ liệu. `None` hiện `—`; `stats_approx` hiện kèm dấu `~` (ví dụ `~1.2万` → `~12000`). Cho phép sắp xếp theo cột; `None` xếp cuối.

## parse_count (`core/pipeline/counts.py`)
`parse_count(value: int | float | str | None) -> tuple[int | None, bool]` trả `(giá_trị, is_approx)`.

| Đầu vào | Kết quả |
|---|---|
| `1234`, `"1234"`, `"1,234"` | `(1234, False)` |
| `"1.2万"`, `"1.2w"`, `"1.2W"` | `(12000, True)` |
| `"3.5亿"` | `(350000000, True)` |
| `"1.2K"`, `"3.4M"`, `"2B"` | `(1200, True)`, `(3400000, True)`, `(2000000000, True)` |
| `"10+"`, `"1000+"` | `(10, True)`, `(1000, True)` |
| `"赞"`, `"点赞"`, `"评论"`, `""`, `None` | `(None, False)` (XHS dùng chữ thay số khi chưa có lượt) — quy tắc [VERIFY] |
| số âm, `NaN`, chuỗi rác | `(None, False)`, không raise |

Yêu cầu: hàm thuần, không raise, làm tròn về `int` bằng `round`, test bảng tham số ≥ 25 case + hypothesis cho "không bao giờ raise".

## Face detect
- Model: OpenCV **YuNet** (`face_detection_yunet_*.onnx`, đóng gói kèm app, kiểm tra checksum).
- Đầu vào: ảnh **cover** (tải về cache `cache/covers/`). Chế độ duy nhất của MVP.
- `has_face = True` nếu có ≥ 1 mặt với `score ≥ 0.7` và chiều rộng mặt ≥ 6% chiều rộng ảnh.
- Chạy trong ThreadPool (2 luồng), timeout 5s/ảnh. Lỗi tải/giải mã → `has_face = None` (badge `?`), **vẫn tải video** (không loại).
- Lưu ý: cover không phải lúc nào cũng có mặt dù video có người. Badge là xấp xỉ; nâng cấp lấy khung hình từ video sau MVP (ngoài phạm vi).

## Badge
| Trạng thái | Hiển thị |
|---|---|
| True | 👤 |
| False | ○ |
| Đang xử lý | … |
| None | ? |
Nút "Phân biệt video có mặt người" bật bộ lọc hiển thị trong bảng: Tất cả / Chỉ có người / Chỉ không người (lọc **hiển thị**, không xóa dữ liệu).

## Test
Fixture ảnh trong `tests/fixtures/faces/` (có mặt, không mặt, mặt nhỏ, ảnh hỏng). Kiểm tra badge cho từng ảnh và hành vi timeout.

## Khớp ảnh (Đợt 2)
Xem `design/IMAGE_SEARCH.md`. Chấm lại bằng Gemini vision sau các bộ lọc ở trên; mặc định chỉ gắn nhãn.
