# Douyin
| Mode | URL |
|---|---|
| Từ khóa | `https://www.douyin.com/search/{kw}?type=video` [VERIFY] |
| Hashtag | Tìm `#tag` như từ khóa, lọc theo `text_extra` |
| User | Link profile `douyin.com/user/{sec_uid}` (người dùng dán link, cần `sec_uid`) |
| Link video | URL `douyin.com/video/{id}` hoặc link rút gọn `v.douyin.com` |

- API pattern: `aweme/v1/web/general/search`, `search/item`, `challenge/aweme`, `aweme/post` [VERIFY].
- SSR: `RENDER_DATA` (URL-encoded JSON) [VERIFY].
- Trường dự kiến: `aweme_id`, `desc`, `video.cover`, `video.play_addr`, giỏ hàng [VERIFY]: `isECVideo == 1`, `anchors` type `5/33/35` hoặc `component_key="anchor_shop"`, `anchor_info`/`shop_product_info`/`commerce_info`/`commerceInfo`/`extra` chứa hint (`shop`/`product`/`commerce`/`goods`/`product_id`), `text_extra` (hashtag). Logic ở `has_cart_signals` trong `common.py`, test synthetic ở `test_normalizers.py::TestCartSignals`.
- Chuỗi tải (synthetic [VERIFY]): `play_addr → bit_rate H264 (res cao trước) → play_addr_265 → bit_rate H265 → download_addr`. Logic thuần ở `core/pipeline/media_urls.py::douyin_url_chain`, khung tải ở `core/infra/downloader.py::resolve_chain`, test ở `test_media_urls.py`.
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
