# TikTok
Mọi mục **[VERIFY]** phải được xác nhận bằng fixture thật rồi sửa tại đây.

| Mode | URL |
|---|---|
| Từ khóa | `https://www.tiktok.com/search/video?q={kw}` [VERIFY] |
| Hashtag | `https://www.tiktok.com/tag/{tag}` [VERIFY] |
| User | `https://www.tiktok.com/@{user}` [VERIFY] |
| Link video | URL do người dùng dán |

- API pattern cần hook: `search/item`, `search/general`, `challenge/item_list`, `post/item_list` [VERIFY].
- SSR: `__UNIVERSAL_DATA_FOR_REHYDRATION__` trong `<script>` [VERIFY] (trang đầu tag/user).
- Trường dự kiến: `video.cover`, `video.playAddr`/`downloadAddr`, giỏ hàng [VERIFY]: `isECVideo == 1`, `anchors` type `5/33/35` hoặc `component_key="anchor_shop"`, `extra` chứa `product_id`, `commerceInfo` (logic ở `has_cart_signals` trong `common.py`, test synthetic ở `test_normalizers.py::TestCartSignals`).
- Số liệu (đi qua `parse_count`):

| VideoItem | Trường JSON [VERIFY] |
|---|---|
| play | `stats.playCount` |
| like | `stats.diggCount` |
| comment | `stats.commentCount` |
| collect | `stats.collectCount` |
| share | `stats.shareCount` |

  Một số response có thể dùng `statsV2` (giá trị dạng chuỗi) [VERIFY]; ưu tiên `stats`, fallback `statsV2`.
- Fallback khi thiếu số liệu: `yt-dlp` `extract_info(download=False)` trả `view_count`, `like_count`, `comment_count`, `repost_count`; chỉ dùng cho link video, không dùng cho cào hàng loạt.
- Tải: ưu tiên URL trong JSON (+Referer); fallback `yt-dlp` với cookie.
- Đăng nhập: không bắt buộc; cảnh báo mềm.
- Ngôn ngữ truy vấn: Việt/Anh.

## Tìm bằng ảnh
TikTok Shop có image search (camera ở thanh tìm Shop) nhưng chỉ trả sản phẩm, không trả video, và không ổn định theo vùng. **Không dùng**. Xem `design/IMAGE_SEARCH.md`.
