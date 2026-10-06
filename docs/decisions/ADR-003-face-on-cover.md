# ADR-003 — Face detect trên cover, trước khi tải
**Quyết định:** YuNet chạy trên ảnh cover; badge 👤 gắn trước khi tải; lỗi → badge `?` và vẫn tải.
**Lý do:** nhanh, không cần tải video để biết badge; phù hợp luồng "đạt lọc → face → badge → tải".
**Đánh đổi:** độ chính xác thấp hơn phân tích khung hình video. Nâng cấp sau MVP.
