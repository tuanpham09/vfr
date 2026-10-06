# Xiaohongshu
| Mode | URL |
|---|---|
| Từ khóa | `https://www.xiaohongshu.com/search_result?keyword={kw}&type=51` [VERIFY] (type=51 = video) |
| Hashtag | Tìm `#tag` như từ khóa, lọc theo tag trong note |
| User | Link profile `xiaohongshu.com/user/profile/{id}` do người dùng dán |
| Link video | Link note **có `xsec_token`**; link thiếu token → báo lỗi rõ ràng |

- API pattern: `api/sns/web/v1/search/notes`, `feed`, `user_posted` [VERIFY].
- SSR: `window.__INITIAL_STATE__` [VERIFY].
- Link note phải lấy từ kết quả (kèm `xsec_token`), không tự ghép.
- Số liệu (đi qua `parse_count`; XHS hay trả chuỗi như `"1.2万"`):

| VideoItem | Trường JSON [VERIFY] |
|---|---|
| play | **không có** (luôn `None`) |
| like | `interact_info.liked_count` |
| comment | `interact_info.comment_count` |
| collect | `interact_info.collected_count` |
| share | `interact_info.share_count` / `shared_count` |

- Kết quả search có thể trả số liệu thiếu hoặc rút gọn hơn trang chi tiết (đặc biệt `comment_count`). Nếu `comment is None` sau search: **bổ sung bằng trang chi tiết** (extension mở note, bắt `feed`) cho các video đã qua lọc; giới hạn tối đa 1 lần mở/video và tuân thủ delay, nếu không thì giữ `None`.
- Chữ thay số khi chưa có lượt (ví dụ "赞") → `None` [VERIFY].
- Không có giỏ hàng → vô hiệu checkbox. Lọc "lượt xem" đổi thành lọc theo tim.
- Đăng nhập: bắt buộc. Cookie `web_session` [VERIFY]. Phiên có thể bị hủy khi đổi IP/đa thiết bị.
- Ngôn ngữ truy vấn: Trung giản thể (giả định).
- Chỉ lấy note `type=video`; bỏ note ảnh.
