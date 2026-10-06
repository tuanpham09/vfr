# Trạng thái MVP đợt 1
| Hạng mục | Trạng thái | Kiểm chứng |
|---|---|---|
| Cào theo **Từ khóa**, **@User/kênh**, **Hashtag**, **Link video** (3 nền tảng) | Đã code đầy đủ | 45 unit test offline (URL, điều phối, lọc hashtag/kênh/sát từ khóa) |
| Độ sát từ khóa dạng luật + cột "Sát" | Xong | Unit test (Latin không dấu, CJK bigram) |
| Số liệu: TikTok view/tim/comment/lưu; Douyin/XHS tim/comment/lưu | Xong ở tầng chuẩn hóa; **tên trường đã đối chiếu với dự án mở** (`design/FIELD_VERIFICATION.md`) | Fixture synthetic + 3 mẫu dựng từ nguồn công khai |
| Hook fetch/XHR | Xong | 3 test node |
| WS server, background/content.js, UI PySide6 | Đã viết | **Chưa chạy** (sandbox không có mạng/PySide6/Chrome) |
| Tên trường JSON thật, selector login/captcha, tên cookie phiên | **[VERIFY]** | Cần capture thật |
| Sinh từ khóa Gemini, face badge, tải video, tìm bằng ảnh | Chưa làm | Đợt 2 |

## Ràng buộc đã biết của từng chế độ
- Douyin/XHS **@User**: bắt buộc dán link trang cá nhân (cần `sec_uid`/`user_id`).
- Douyin/XHS **Hashtag**: tìm `#tag` rồi lọc theo hashtag/mô tả, nên số kết quả có thể ít hơn kỳ vọng.
- **Từ khóa** Douyin/XHS nên viết tiếng Trung; tiếng Việt sẽ bị lọc "không sát" (đến khi có Gemini dịch từ khóa).
