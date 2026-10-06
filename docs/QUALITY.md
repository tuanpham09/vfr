# Quality scorecard
Điểm 0–3 (0 chưa có · 1 chạy được · 2 có test+docs · 3 ổn định, đã soak). Cập nhật khi đóng task.

| Module | Điểm | Khoảng trống/ghi chú |
|---|---|---|
| Harness (lint, CI, Makefile) | 0 | S0 |
| Fixtures 3 nền tảng | 0 | S0-5 |
| Extension core (WS, hook, scroll) | 0 | |
| Adapter TikTok / Douyin / XHS | 0 / 0 / 0 | |
| Normalizer TikTok / Douyin / XHS | 0 / 0 / 0 | cần fixture |
| Login/captcha pause-resume | 0 | |
| Keyword Gemini | 0 | |
| Filters + relevance luật | 1 | Đã code + unit test; chờ fixture thật |
| Tìm bằng ảnh (Gemini vision) | 0 | Đợt 2, `design/IMAGE_SEARCH.md` |
| parse_count + số liệu tương tác | 0 | S0-6 |
| Face detect + badge | 0 | |
| Downloader | 0 | |
| UI tab Cào dữ liệu | 0 | |
| Chống bot / rate limit | 0 | |
| Đóng gói | 0 | |

## Câu hỏi mở
- XHS dùng từ khóa tiếng Trung giản thể — xác nhận.
- Nhãn "lượt xem tối thiểu" cho XHS/Douyin khi không có play_count — chấp nhận dùng like?
- Hệ điều hành đích: Windows + Chrome (giả định).
