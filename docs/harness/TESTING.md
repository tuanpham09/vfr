# Testing

| Tầng | Công cụ | Phạm vi | Mạng |
|---|---|---|---|
| Unit | pytest | normalizers, filters, relevance, face_detect, keyword parsing, config | Không |
| Contract | pytest | `WsMessage` schema ↔ message mẫu trong `tests/fixtures/ws/` | Không |
| Integration | pytest-asyncio | `ws_server` + `task_runner` + `FakeExtension` (script phát lại fixture) + DB tạm | Không |
| Extension | vitest + jsdom | adapters (detect login, URL builder), hook parse pattern, state machine scroll | Không |
| UI smoke | pytest-qt | Khởi tạo cửa sổ, table model nhận event, nút Bắt đầu/Dừng | Không |
| Live | pytest `-m live` | Gemini thật, một trang thật | Có, chạy tay |

## Quy tắc
- `make check` chỉ chạy các tầng không mạng; thời gian mục tiêu < 60s.
- Mỗi normalizer: test với ≥ 3 fixture thật (có giỏ hàng, không giỏ hàng, thiếu trường), kèm snapshot `VideoItem` (syrupy).
- `FakeExtension` phát lại chuỗi `captured` từ fixture để chạy end-to-end AC1 mà không cần Chrome.
- Property test (hypothesis) cho dedupe: thứ tự và trùng lặp không đổi tập kết quả.
- Mỗi bug sửa xong phải kèm test tái hiện.

## Kiểm thử thủ công (checklist trước release)
Chạy tay từng nền tảng với Chrome thật: AC1–AC5 trong `product/SPEC.md`; ghi kết quả vào `QUALITY.md`.
