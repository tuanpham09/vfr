# ADR-001 — Extension hook thay vì tự ký request
**Quyết định:** dùng extension trong Chrome đã đăng nhập, hook fetch/XHR bắt JSON; app không gọi API nền tảng.
**Lý do:** chữ ký (`a_bogus`, `X-Bogus`, `x-s`...) đổi thường xuyên; để trang tự ký ít bảo trì và ít bị phát hiện hơn.
**Đánh đổi:** cần Chrome mở và đăng nhập; tốc độ thấp hơn; phụ thuộc pattern URL (giảm bằng fixtures + adapters).
