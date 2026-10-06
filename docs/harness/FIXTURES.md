# Fixtures

Vị trí: `tests/fixtures/{tiktok,douyin,xhs}/{mode}_{yyyymmdd}_{n}.json`, cộng `ws/`, `faces/`.

## Thu thập
1. Bật chế độ debug của extension (Options → "Lưu captured JSON") hoặc DevTools → Network → Copy response.
2. Chạy `python tools/scrub_fixture.py <file>`: xóa cookie, token, `msToken`, `xsec_token` (thay `XSEC_TOKEN_PLACEHOLDER`), ID thiết bị, email/điện thoại; giữ cấu trúc.
3. Đặt tên theo mẫu; thêm một dòng vào `tests/fixtures/INDEX.md`: nguồn, ngày, mode, có giỏ hàng?, ghi chú.
4. `make fixtures-check` kiểm tra: JSON hợp lệ, không chứa pattern bí mật, có trong INDEX.

## Khi nền tảng đổi cấu trúc
1. Thu fixture mới (giữ cái cũ nếu còn dùng được).
2. Test normalizer fail → sửa normalizer.
3. Cập nhật `docs/platforms/*.md`, gỡ/ghi lại các mục `[VERIFY]`.

## Cần thu trước khi viết normalizer (bắt buộc)
Mỗi nền tảng: 1 search có giỏ hàng, 1 search không, 1 hashtag/tag, 1 user posts, 1 detail, 1 phản hồi "chưa đăng nhập".
