# Product Spec — MVP v0.3

## Mục đích
Tải video review sản phẩm về để nghiên cứu nội dung. Dùng nội bộ, không phân phối lại.

## Phạm vi
| Có | Không (ngoài MVP) |
|---|---|
| Tab "1. Cào dữ liệu" đầy đủ | Facebook |
| TikTok, Douyin, Xiaohongshu | Tab Auto, 2. Xử lý video, 3. Review & xuất (chỉ placeholder) |
| Chế độ: Từ khóa, @User, Hashtag, Link video | Tìm theo ảnh bằng Gemini vision (Đợt 2, `design/IMAGE_SEARCH.md`); embedding chấm điểm, LLM giám khảo text |
| Sinh từ khóa bằng Gemini (tối đa 2 truy vấn) — **chưa làm ở đợt 1** | ASR/VLM phân loại nội dung |
| Độ sát từ khóa dạng luật (cột "Sát", ô "Độ sát từ khóa (%)") | |
| Face detect → badge 👤 | Phát hiện người nói chung (chỉ khuôn mặt) |
| Tải video, Tải trực tiếp bằng link | Headless/server mode |

## UI (theo ảnh tham chiếu)
- Header: Auto | 1. Cào dữ liệu | 2. Xử lý video | 3. Review & xuất | Cài đặt | Mở video đã cào.
- Panel trái: tab nền tảng (TikTok, Douyin, Xiaohongshu); "Chế độ cào" (Từ khóa tìm kiếm / @User / Hashtag / Link video); ô nhập mỗi dòng 1 mục; checkbox "Chỉ lấy video có giỏ hàng"; nút "Phân biệt video có mặt người" (bật lọc badge); "Số video", "Lượt xem tối thiểu"; Bắt đầu / Dừng; trạng thái "Chrome Ext"; mục "3. Tải trực tiếp".
- Panel phải: bảng video (thumbnail, mô tả, tác giả, số liệu, badge giỏ hàng, badge 👤, trạng thái tải), phân trang Trước/Sau, Chọn tất cả / Bỏ chọn / Chuyển đến phần xử lý (chỉ đánh dấu).
- Dưới: Nhật ký cào + Xóa log.

## Hành vi theo nền tảng
| | TikTok | Douyin | XHS |
|---|---|---|---|
| Ngôn ngữ từ khóa | Việt hoặc Anh | Trung giản thể | Trung giản thể (giả định, cần xác nhận) |
| Số liệu lấy được | view, tim, comment, lưu, share | tim, comment, lưu, share | tim, comment, lưu, share |
| "Lượt xem tối thiểu" | `play` | Đổi nhãn "Lượt tim tối thiểu" (lọc `like`) | Đổi nhãn "Lượt tim tối thiểu" (lọc `like`) |
| "Có giỏ hàng" | Hỗ trợ [VERIFY] | Hỗ trợ [VERIFY] | Vô hiệu hóa checkbox |
| Đăng nhập | Cảnh báo mềm | Bắt buộc | Bắt buộc |

## Pipeline một mục nhập
1. Người dùng nhập từ khóa (mode Từ khóa) → Gemini sinh **tối đa 2 truy vấn** đúng ngôn ngữ nền tảng (fallback: dùng nguyên văn).
2. Task chạy tuần tự từng truy vấn qua extension.
3. App: normalize → dedupe `(platform, video_id)` → lọc (lượt xem, giỏ hàng, sát từ khóa dạng luật) → **face detect trên cover → badge 👤** → xếp hàng tải → tải.
4. Đủ `Số video` thì `stop`. Tính tổng sau lọc.

## Tiêu chí nghiệm thu MVP
- AC1: Mỗi nền tảng, 1 từ khóa + Số video=30 → đúng 30 dòng không trùng, Dừng được giữa chừng.
- AC2: Video tải về phát được, nằm ở `downloads/{platform}/{author_id}/{video_id}.mp4` + `.json`.
- AC3: Chưa đăng nhập XHS/Douyin → app tạm dừng với thông báo "Hãy đăng nhập XHS trong Chrome rồi bấm Tiếp tục"; Tiếp tục chạy lại đúng.
- AC4: Badge 👤 hiển thị cho mọi video đạt lọc; lọc "có người / không người" hoạt động.
- AC5: Chạy 100 video/nền tảng liên tục không crash, UI không đứng.
- AC6: Mỗi mục nhập gọi Gemini tối đa 1 lần; thiếu API key vẫn cào được.
