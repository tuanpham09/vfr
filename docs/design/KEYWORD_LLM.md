# Sinh từ khóa bằng Gemini

## Model
`gemini-3.6-flash` (ID ổn định, phát hành 21/07/2026). Đặt trong `config.LLM_MODEL`, không hardcode ở chỗ khác. Xác nhận lại ID trước khi release.

## Quy tắc
- Chỉ áp dụng mode **Từ khóa**. @User, Hashtag, Link: không gọi LLM.
- **Tối đa 2 truy vấn/mục nhập** (`MAX_QUERIES_PER_INPUT = 2`), bao gồm cả truy vấn gốc nếu LLM trả về lại.
- Gọi **một lần** cho mỗi mục nhập, timeout 15s, 1 retry. Lỗi/thiếu key → fallback `[input nguyên văn]`, log cảnh báo, không chặn cào.
- Cache theo `(input, platform, model)` trong DB (bảng `kw_cache`) để không gọi lại.

## Ngôn ngữ đích
| Nền tảng | Truy vấn 1 | Truy vấn 2 |
|---|---|---|
| Douyin | Trung giản thể: tên sản phẩm/thương hiệu | Trung giản thể + cụm review (测评/开箱/真实使用) |
| XHS | Như Douyin (giả định, cần xác nhận) | + 种草/避雷 |
| TikTok | Việt (nếu input Việt) hoặc Anh | Anh hoặc Việt (ngôn ngữ còn lại) + "review" |

Nếu input đã đúng ngôn ngữ đích, truy vấn 1 giữ nguyên và truy vấn 2 là biến thể review.

## Hợp đồng gọi API
- Structured output (JSON schema): `{"queries": [{"text": str, "lang": "zh-Hans|vi|en"}]}`; `maxItems: 2`.
- Prompt hệ thống: giữ nguyên tên thương hiệu/model sản phẩm, không thêm sản phẩm khác, không thêm giải thích.
- **Gemini 3.x**: lượt cuối của `contents` phải là role `user` (turn cuối role `model` bị HTTP 400). Không gửi tham số đã bị Gemini 3 cấm; kiểm tra tài liệu hiện hành khi nâng model.
- Validate đầu ra: bỏ chuỗi rỗng/trùng/quá 60 ký tự; cắt còn tối đa 2.
- Giao diện: `KeywordGenerator` (Protocol) trong `core/infra/llm_gemini.py`; test dùng `FakeKeywordGenerator`.

## Hiển thị
Log: `Từ khóa "X" → Douyin: ["…","…"]`. Cài đặt có ô API key, nút "Thử kết nối", công tắc "Dùng AI sinh từ khóa".

## Test
Unit: parser JSON, cắt giới hạn 2, fallback khi lỗi, cache hit. Không gọi mạng thật trong `make check`; test thật nằm ở `tests/live/` (marker `live`, chạy tay).

## Từ khóa sinh từ ảnh (Đợt 2)
Dùng cùng giới hạn (≤ 2 truy vấn, fallback, cache). Chi tiết ở `design/IMAGE_SEARCH.md`. Ảnh gửi dạng inline data; lượt cuối vẫn là role `user`.
