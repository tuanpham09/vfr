# Đối chiếu tên trường với dự án mã nguồn mở

Ngày: 06/10/2026. Phương pháp: so tên trường mà normalizer đang đọc với mẫu/tài liệu của các scraper công khai. **Hạn chế:** không đọc được trực tiếp mã nguồn MediaCrawler/Douyin_TikTok_Download_API/XHS-Downloader (công cụ tìm kiếm không trả về file đó), nên bằng chứng là *mẫu đầu ra và tài liệu* của các scraper khác. Đây là bằng chứng thứ cấp, không thay được fixture thật.

## Số liệu tương tác
| Nền tảng | Trường normalizer đọc | Kết quả đối chiếu | Nguồn |
|---|---|---|---|
| TikTok | `stats.playCount`, `diggCount`, `commentCount`, `shareCount` | **Khớp** | gist mẫu của davidteather/TikTok-Api |
| TikTok | `stats.collectCount` (lượt lưu) | **Khớp** | script lấy stats hashtag dùng TikTok-Api (gist nickjevershed) |
| TikTok | `author.uniqueId`, `id`, `desc`, `createTime`, `video.playAddr/downloadAddr/duration` | **Khớp** | gist davidteather |
| Douyin | `statistics.digg_count`, `comment_count`, `collect_count` | **Khớp** | mẫu JSON Douyin (issue Meekdai), mô tả đầu ra Apify |
| Douyin | `statistics.share_count` | **Khớp** | mô tả Apify, scraper Douyin cũ |
| Douyin | `statistics.play_count` luôn 0 → bỏ qua `play` | **Khớp với quyết định** | tài liệu Apify toolzerhub: `play_count` trong `statistics` đọc ra 0, số thật nằm ở nguồn khác |
| Douyin | `video.play_addr.url_list` (có `playwm`) | **Khớp** | mẫu issue Meekdai |
| XHS | `note_card.interact_info.liked_count`, `collected_count`, `comment_count` | **Khớp** | tài liệu CLI redbook/xiaohongshu-cli |
| XHS | `share_count` (chi tiết note) / `shared_count` (đang đọc cả hai) | **Khớp một phần**: chi tiết dùng `share_count`; chưa thấy nguồn xác nhận `shared_count` ở search | tài liệu API note detail |
| XHS | số dạng chuỗi `"1.5万"` | **Khớp** (cần `parse_count`) | tài liệu redbook |
| XHS | `note_card.user.{user_id,nickname}`, `type` = `normal`/`video`, user-posts: `notes[].interact_info`, `display_title` | **Khớp** | tài liệu redbook |

## Chưa đối chiếu được (vẫn [VERIFY])
- TikTok `statsV2` (chuỗi), trường giỏ hàng `anchors`; Douyin `anchor_info`/trường sản phẩm; mọi `has_cart`.
- Douyin `video.cover.url_list`, đơn vị `video.duration` (đang giả định mili giây).
- Cấu trúc bọc ngoài của API *tìm kiếm* (`data[].item`, `data[].aweme_info`, `data.items[]`): normalizer duyệt đệ quy nên ít phụ thuộc, nhưng chưa thấy mẫu thật.
- Một nguồn hướng dẫn dùng `note['liked_count']` phẳng cho XHS; chưa xác nhận, chưa hỗ trợ.
- Tên cookie phiên, selector login/captcha.

## Kiểm thử đi kèm
`tests/fixtures/reference/*` + `tests/unit/test_reference_shapes.py`: 3 mẫu dựng lại từ cấu trúc và giá trị công khai ở trên; cả 3 qua.

## Bước kế tiếp để chốt 100%
Capture thật (README → "Lần chạy đầu") rồi thêm vào `tests/fixtures/{platform}/` và gỡ `[VERIFY]` tương ứng.
