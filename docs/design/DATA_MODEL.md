# Data Model

## VideoItem (`core/types.py`, Pydantic, frozen)
| Trường | Kiểu | Ghi chú |
|---|---|---|
| platform | `tiktok\|douyin\|xhs` | |
| video_id | str | khóa cùng platform |
| url | str | link trang; XHS giữ `xsec_token` trong URL lấy từ kết quả |
| desc | str | |
| author_id, author_name | str | |
| hashtags | list[str] | |
| cover_url, play_url | str / str\|None | |
| duration_s | float\|None | |
| play, like, comment, collect, share | int\|None | Số liệu tương tác (xem mục dưới). `None` = nền tảng không cung cấp, **khác** `0` |
| stats_approx | bool | `True` nếu có số liệu bắt nguồn từ chuỗi rút gọn (`1.2万`, `3.4K`), nghĩa là chỉ xấp xỉ |
| has_cart | bool\|None | None = không xác định (XHS) |
| product_info | dict\|None | |
| has_face | bool\|None | None = chưa kiểm tra |
| image_match, image_match_reason | bool\|None, str | Đợt 2 (`IMAGE_SEARCH.md`). None = chưa biết/không chắc |
| relevance | float\|None | điểm luật 0..1, chỉ khi mode Từ khóa; cột SQLite `relevance` |
| status | `new\|filtered_out\|queued\|downloading\|done\|error` | |
| local_path | str\|None | |
| query, task_id | str | nguồn gốc |
| created_at | datetime\|None | |
| raw | dict | JSON gốc, giữ để debug |

## Số liệu tương tác
| Trường | Ý nghĩa | TikTok | Douyin | XHS |
|---|---|---|---|---|
| play | Lượt xem | ✅ | ❌ (None) | ❌ (None) |
| like | Lượt tim/thích | ✅ | ✅ | ✅ |
| comment | Bình luận | ✅ | ✅ | ✅ |
| collect | Lượt lưu | ✅ nếu có | ✅ nếu có | ✅ nếu có |
| share | Lượt chia sẻ | ✅ nếu có | ✅ nếu có | ✅ nếu có |

Quy tắc:
- Mọi số liệu đi qua `parse_count()` (`core/pipeline/counts.py`, hàm thuần). Không parse số ở nơi khác.
- Nền tảng không trả trường → `None`. Trả `0` thật → `0`. UI hiện `—` cho `None`.
- `play` của Douyin/XHS luôn `None` dù JSON có trường (Douyin web thường trả 0/ẩn nên không đáng tin). Quyết định ở normalizer, ghi trong `platforms/*.md`.
- Số rút gọn (`万`, `亿`, `K`, `M`) → `stats_approx = True`.
- Số liệu tại thời điểm cào; cập nhật lại khi cùng video xuất hiện lần sau với số mới hơn (upsert theo `(platform, video_id)`, ghi đè số liệu, giữ `status`, `local_path`, `has_face`).

## SQLite
```
videos(platform, video_id, ..., play, like_count, comment_count, collect_count, share_count, stats_approx, raw_json, stats_updated_at, PRIMARY KEY(platform, video_id))
-- tránh từ khóa SQL `like`: cột đặt tên *_count; map sang field `like`... trong repo
tasks(task_id PK, platform, mode, input_text, query, target, got, state, reason, started_at, ended_at)
settings(key PK, value)
```
- Index: `videos(status)`, `videos(task_id)`.
- Migration: file SQL đánh số `core/infra/migrations/NNN_*.sql`, chạy theo `PRAGMA user_version`.
- API key Gemini **không** lưu trong DB; dùng `keyring` (fallback biến môi trường `GEMINI_API_KEY`).
