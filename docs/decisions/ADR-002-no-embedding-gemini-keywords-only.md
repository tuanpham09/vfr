# ADR-002 — Gemini chỉ sinh từ khóa; không embedding
**Quyết định:** dùng `gemini-3.6-flash` để sinh tối đa 2 truy vấn theo ngôn ngữ nền tảng. Không dùng embedding, không dùng LLM giám khảo trong MVP. Độ sát từ khóa dùng luật (jieba/rapidfuzz/OpenCC).
**Lý do:** giảm số lượt cào (rủi ro chặn), giữ app nhẹ, ít phụ thuộc.
**Hệ quả:** có thể lọt video lạc đề; đo bằng gắn nhãn tay ~100 video, nếu kém mới xét lại (ADR mới).
