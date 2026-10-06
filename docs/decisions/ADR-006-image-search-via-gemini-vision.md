# ADR-006 — Tìm bằng ảnh qua Gemini vision, không tự động hóa tìm ảnh của nền tảng
**Bối cảnh:** TikTok chỉ có image search trong TikTok Shop (trả sản phẩm, thử nghiệm theo vùng); Douyin/XHS không có tìm ngược ảnh → video.
**Quyết định:** ảnh → (Gemini vision) truy vấn ≤ 2 → cào như mode từ khóa → chấm lại ảnh bìa bằng Gemini vision theo lô; mặc định chỉ gắn nhãn.
**Lý do:** ổn định hơn tự động hóa giao diện, đúng nguyên tắc extension không có logic nghiệp vụ, không cần embedding/CLIP (ADR-002).
**Đánh đổi:** tốn call Gemini (có trần), gửi ảnh ra ngoài, ảnh bìa là chứng cứ yếu.
