# Giao thức App ↔ Extension

Transport: WebSocket `ws://127.0.0.1:{port}` (mặc định 8765), chỉ bind loopback. Mọi message là JSON có `type` và `v` (phiên bản giao thức, hiện = 1). Định nghĩa Pydantic: `core/types.py::WsMessage` (nguồn sự thật). Extension kiểm tra `v`; lệch phiên bản → báo "Cần cập nhật extension".

**Xác thực:** app sinh `token` ngẫu nhiên lúc khởi động, hiển thị/ghi vào file mà extension đọc qua trang options. Extension gửi token trong `hello`. Sai token → đóng kết nối. (Chặn trang web bất kỳ nối vào cổng local.)

## ext → app
| type | Trường | Khi nào |
|---|---|---|
| `hello` | `ver`, `token`, `browser` | Khi kết nối |
| `ping` | `ts` | Mỗi 20s (giữ service worker sống) |
| `cookies` | `platform`, `cookies[]` | Khi kết nối và sau mỗi `resume` (cho downloader) |
| `state` | `task_id`, `platform`, `payload` | Dữ liệu SSR đầu trang |
| `captured` | `task_id`, `api`, `payload`, `seq` | Mỗi response JSON khớp pattern |
| `progress` | `task_id`, `scrolls`, `idle_count` | Mỗi vài lần scroll |
| `task_done` | `task_id`, `reason`, `platform?` | Kết thúc |

`reason` ∈ `idle` · `max_scroll` · `stopped` · `login_required` · `captcha` · `error` (kèm `detail`).

## app → ext
| type | Trường |
|---|---|
| `task` | `task_id`, `platform`, `mode`, `query`, `url`, `max_scrolls`, `behavior` (jitter config) |
| `stop` | `task_id` |
| `resume` | `task_id` (mở lại URL, kiểm tra lại cookie/login) |
| `pong` | `ts` |

## Máy trạng thái task (app)
```
queued → running → done
              ├─► paused_login ──resume──► running
              ├─► paused_captcha ─resume─► running
              ├─► stopped (user)
              └─► failed (error, retry < 2 thì quay lại queued)
```
- `login_required`/`captcha` → `paused_*`, phát event cho UI hiện hộp thoại: **Mở trang đăng nhập / Tiếp tục / Bỏ qua mục này**. Thông báo: "Hãy đăng nhập {XHS} trong Chrome rồi bấm Tiếp tục".
- Dữ liệu đã nhận trước khi pause **được giữ**; resume không tính lại video trùng (dedupe DB).

## Phát hiện đăng nhập (extension, `adapters/*.js`)
Một tín hiệu khớp là đủ:
1. Cookie phiên thiếu (`chrome.cookies.get`): XHS `web_session` [VERIFY], Douyin `sessionid`/`sid_guard` [VERIFY], TikTok `sessionid` [VERIFY].
2. DOM có modal login (selector trong adapter) [VERIFY].
3. API trả mã chưa đăng nhập (XHS code kiểu `-100` [VERIFY]) hoặc rỗng bất thường.
TikTok: chỉ gửi `progress` kèm cờ `soft_login_warning`, không chặn.

## Quy tắc extension
- Mở bằng `chrome.windows.create({focused:false, width:600, height:800})`; không dùng tab nền/minimized (bị throttle).
- Kết thúc sớm khi: `stop`; 3 lần scroll liên tiếp không có `captured` mới; hết `max_scrolls`.
- Reconnect tự động (backoff 1→10s). Mất kết nối giữa task → đóng cửa sổ, task ở app chuyển `failed` sau 30s.
- Extension **không** parse nội dung payload.
