# Tìm bằng hình ảnh sản phẩm (Đợt 2)

## Vì sao không dùng tìm ảnh gốc của TikTok
TikTok chỉ có tìm bằng ảnh **trong TikTok Shop** (biểu tượng máy ảnh ở thanh tìm kiếm Shop), trả về *sản phẩm đang bán*, không trả video, và được báo cáo là thử nghiệm ở Mỹ/Đông Nam Á (nguồn: TechCrunch, Search Engine Land, 2024). Không có tìm ngược ảnh → video cho Douyin/XHS. Vì vậy extension **không** tự upload ảnh vào nền tảng (xem ADR-006).

## Hướng làm: ảnh → từ khóa → cào → chấm lại bằng ảnh (đều dùng Gemini vision)
| Bước | Việc | Ở đâu |
|---|---|---|
| 1. Ảnh → truy vấn | Gemini nhìn ảnh, đọc chữ trên bao bì, trả `{brand, product, category, ocr_text, queries[≤2]}` theo ngôn ngữ nền tảng (như `KEYWORD_LLM.md`) | App |
| 2. Cào | Chạy truy vấn như mode Từ khóa (extension không đổi) | Extension |
| 3. Chấm lại | Gửi ảnh gốc + ảnh bìa các video đã qua lọc (lô tối đa 8 ảnh/lần) → `yes/no/unsure` | App |

## Hợp đồng
- Đầu vào: JPG/PNG/WEBP ≤ 8MB; app thu nhỏ cạnh dài ≤ 1024px (ảnh bìa ≤ 384px) trước khi gửi.
- Bước 1: structured output `{"queries":[{"text","lang"}], "brand", "product", "ocr_text"}`; tối đa 2 truy vấn; cache theo SHA-256 ảnh + nền tảng.
- Bước 3: structured output `[{"id":int,"match":"yes|no|unsure","reason":str<=80}]`; cache theo `(sha256(ảnh gốc), cover_url)`.
- Mỗi call Gemini 3.x: lượt cuối của `contents` phải là role `user`; ảnh gửi dạng inline data (xem `KEYWORD_LLM.md`).
- Trần chi phí: `max_vision_calls_per_job` (mặc định 20). Hết trần → các video còn lại `image_match = None`.
- Không có API key → ô "Tìm bằng ảnh" bị khóa kèm tooltip.

## Dữ liệu và UI
- `VideoItem.image_match: bool | None` (True khớp, False không khớp, None chưa biết/không chắc); `image_match_reason: str`.
- Bảng: cột **"Khớp ảnh"**: ✔ / ✖ / `?`. Sắp xếp được.
- Ô "Tìm bằng ảnh" ở panel trái (kéo thả hoặc chọn tệp, hiện thumbnail), có nút xóa ảnh. Khi có ảnh, ô nhập từ khóa là tùy chọn (nếu có thì ghép thêm làm truy vấn thứ 2 thay vì để Gemini sinh).
- Cài đặt: "Cách xử lý video không khớp ảnh": **Chỉ gắn nhãn** (mặc định) | **Loại bỏ**. `unsure` luôn được giữ.

## Vị trí trong pipeline
`normalize → dedupe → views → cart → relevance(chỉ mode từ khóa, **bỏ khi mode ảnh**) → image_match(lô) → face → badge → download`
Với "Loại bỏ", video chỉ tính vào "Số video" sau khi có kết quả `image_match`; runner giữ hàng đợi chờ lô đầy hoặc hết dữ liệu.

## Giới hạn
- Ảnh bìa không phải lúc nào cũng thấy sản phẩm → mặc định chỉ gắn nhãn, không xóa.
- Ảnh gốc không có chữ, sản phẩm chung chung → từ khóa kém chính xác (bước 1 yếu).
- Ảnh người dùng và ảnh bìa được gửi tới Google (Gemini API): hiển thị cảnh báo ở lần dùng đầu.
- Mục tiêu đo: gắn nhãn tay 100 video/nền tảng, so tỉ lệ đúng của bước 3 trước khi bật mặc định.

## Task (xem ROADMAP, nhóm S4)
