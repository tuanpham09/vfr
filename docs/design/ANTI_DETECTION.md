# Mượt và hạn chế bị phát hiện

Không có đảm bảo tuyệt đối. Thiết kế giảm rủi ro: trình duyệt thật, đã đăng nhập, request do chính trang sinh ra.

## Bất biến
1. App không gọi API nền tảng. Chỉ extension duyệt trang.
2. Mỗi lúc chỉ **một** cửa sổ cào, tuần tự.
3. Một profile Chrome cố định, một IP ổn định, tài khoản phụ.
4. Gặp captcha/đăng nhập → dừng ngay, chờ người dùng. **Không** cố vượt captcha.

## Tham số (trong `config`, có UI ở Cài đặt)
| Tham số | Mặc định |
|---|---|
| `task_delay_s` | ngẫu nhiên 20–60 giữa các task |
| `scroll_interval_s` | 1.5–4.0, không đều |
| `scroll_px` | 600–1400 ngẫu nhiên; 10% cuộn ngược nhẹ |
| `pause_chance` | 15% dừng thêm 3–8s |
| `max_tasks_per_hour` | 12 mỗi nền tảng |
| `max_videos_per_day` | 500 mỗi nền tảng |
| `max_queries_per_input` | 2 |

Hành vi được gửi trong `task.behavior`; extension chỉ thực thi, không tự quyết.

## Tải file
Tải media là request tới CDN, dùng `User-Agent` trùng Chrome của người dùng, `Referer` đúng nền tảng, cookie từ extension nếu cần; tối đa 3 luồng, delay nhỏ ngẫu nhiên 0.3–1.2s giữa các file.

## Mượt
Event-driven (không polling), DB ghi batch, thumbnail lazy + LRU cache, face detect ở executor, bảng dùng `QAbstractTableModel` + fetchMore.

## Quan sát
Log số lần captcha/login theo nền tảng; nếu ≥ 2 captcha/giờ → tự giảm `max_tasks_per_hour` một nửa và cảnh báo.
