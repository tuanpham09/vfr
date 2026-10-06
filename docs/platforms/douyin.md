# Douyin
| Mode | URL |
|---|---|
| Từ khóa | `https://www.douyin.com/search/{kw}?type=video` [VERIFY] |
| Hashtag | Tìm `#tag` như từ khóa, lọc theo `text_extra` |
| User | Link profile `douyin.com/user/{sec_uid}` (người dùng dán link, cần `sec_uid`) |
| Link video | URL `douyin.com/video/{id}` hoặc link rút gọn `v.douyin.com` |

- API pattern: `aweme/v1/web/general/search`, `search/item`, `challenge/aweme`, `aweme/post` [VERIFY].
- SSR: `RENDER_DATA` (URL-encoded JSON) [VERIFY].
- Trường dự kiến: `aweme_id`, `desc`, `video.cover`, `video.play_addr`, `anchor_info`/trường sản phẩm [VERIFY], `text_extra` (hashtag).
- Số liệu (đi qua `parse_count`):

| VideoItem | Trường JSON [VERIFY] |
|---|---|
| play | **bỏ qua** (luôn `None`, `play_count` thường 0/ẩn) |
| like | `statistics.digg_count` |
| comment | `statistics.comment_count` |
| collect | `statistics.collect_count` |
| share | `statistics.share_count` |

- Lọc "lượt xem tối thiểu" đổi thành lọc theo tim (xem FILTERS_AND_FACE).
- Đăng nhập: bắt buộc (chặn cứng). Cookie phiên [VERIFY].
- Ngôn ngữ truy vấn: Trung giản thể.
