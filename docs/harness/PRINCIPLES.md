# Harness principles (cho coding agent)

Mục tiêu: để agent làm việc đúng mà không cần con người đọc từng dòng. Môi trường phải tự kiểm tra, tự hướng dẫn.

1. **AGENTS.md là bản đồ, không phải bách khoa.** Giữ < 100 dòng, trỏ tới docs. Chi tiết nằm ở `docs/` (progressive disclosure).
2. **Repo là nguồn sự thật duy nhất.** Quyết định, giao thức, quirk nền tảng đều nằm trong repo. Điều gì không có trong repo thì agent không biết.
3. **Ràng buộc bằng máy, không bằng lời.** Quy tắc kiến trúc → import-linter/ruff/test. Thông báo lỗi phải nói *sửa thế nào*.
4. **Ranh giới nghiêm, bên trong tự do.** Parse dữ liệu ở biên (Pydantic), lớp thuần không IO; trong phạm vi đó agent được tự chọn cách làm.
5. **Vòng phản hồi nhanh.** `make check` < 60s, offline, deterministic. Fixtures thay mạng.
6. **Fixtures là bộ nhớ của hệ thống.** Mỗi lần nền tảng đổi, thêm fixture mới thay vì sửa test bằng tay.
7. **Dễ đọc cho agent.** Tên rõ, module nhỏ (< 400 dòng), type annotation đầy đủ, ít magic, log có cấu trúc.
8. **Việc nhỏ, kế hoạch rõ.** Mỗi task trong `plans/active/` có mục tiêu, file đụng tới, tiêu chí xong, lệnh kiểm tra.
9. **Dọn nợ liên tục.** `QUALITY.md` ghi điểm từng module; mẫu xấu lặp lại thì biến thành lint rule.
10. **Không đoán dữ liệu ngoài.** Mục `[VERIFY]` chỉ được bỏ khi có fixture thật chứng minh.

## Quy trình một task
1. Đọc task trong `plans/active/`, đọc docs liên quan.
2. Viết test (dùng fixture) → fail.
3. Code tối thiểu → `make check` xanh.
4. Cập nhật docs/`QUALITY.md`; chuyển task sang `plans/done/`.
5. Commit nhỏ, message nêu task ID.

## Cấm
- Sửa test để qua mà không sửa nguyên nhân; xóa lint rule để qua.
- Thêm dependency không ghi ADR.
- Commit cookie/token/API key (pre-commit + `make fixtures-check` chặn).
