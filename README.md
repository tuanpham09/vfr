# Video Flow Render — MVP đợt 1 (tab "1. Cào dữ liệu")

Cào video từ TikTok / Douyin / Xiaohongshu qua Chrome extension + app Python.
Hiển thị: **TikTok** view, tim, comment, lưu; **Douyin/XHS** tim, comment, lưu.

## Chạy
```
python -m venv .venv && . .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```
1. Mở Chrome (profile cố định, đã đăng nhập các nền tảng) → `chrome://extensions` → bật Developer mode → **Load unpacked** → chọn thư mục `extension/`.
2. Trong app: **Cài đặt** → xem *Cổng* và *Token*. Trong extension: Chi tiết → **Extension options** → dán cổng + token → Lưu.
3. Trạng thái "Chrome Ext" ở tab 1 chuyển xanh "Đã kết nối".
4. Chọn nền tảng, chế độ, nhập mục (mỗi dòng 1 mục), **Bắt đầu cào video**.

## Lần chạy đầu: LÀM NGAY để đảm bảo đúng số liệu
Tên trường JSON của nền tảng chưa được kiểm chứng bằng dữ liệu thật (fixtures hiện tại là *synthetic*).
1. Cài đặt → tick **Lưu JSON thô** → cào 1 từ khóa mỗi nền tảng.
2. JSON thô nằm ở `~/.vfr/captures/`. Xóa cookie/token trước khi chia sẻ, rồi đưa vào `tests/fixtures/` để kiểm tra normalizer.
3. Nếu bảng ra `—` ở cột bạn mong có số, mở file capture tương ứng để xem tên trường thật và sửa `core/pipeline/normalizers/*.py`.

## Test
```
python -m unittest discover -s tests/unit -t .     # 45 test, offline
node --test tests/ext/inject.test.js               # hook fetch/XHR
```

## Phạm vi đợt 1
Có: cào 4 chế độ (từ khóa, @User/kênh, hashtag, link) + lọc sát từ khóa, đăng nhập/captcha tạm dừng-tiếp tục, lọc view/tim/giỏ hàng, bảng + phân trang + sắp xếp, lưu SQLite.
Chưa: sinh từ khóa Gemini, face detect/badge 👤 (cột hiện `?`), tải video, Tải trực tiếp (ô bị khóa).
