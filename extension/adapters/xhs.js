// Adapter XHS: chuẩn từ khóa nghiệp vụ (VFR003). Runtime hiện chỉ forward JSON thô
// (xem inject.js); parse nằm ở core/pipeline/normalizers/xhs.py.
// Tên trường là [VERIFY] tới khi có fixture thật (docs/platforms/xhs.md).
(function () {
  const FIELDS = {
    card: "note_card",
    id: "id",
    noteId: "note_id",
    interact: "interact_info",
    liked: "liked_count",
    collected: "collected_count",
    comment: "comment_count",
    shared: "shared_count",
    share: "share_count",
    user: "user",
    userId: "user_id",
    nickname: "nickname",
    nickName: "nick_name",
    title: "display_title",
    desc: "desc",
    tags: "tag_list",
    tagName: "name",
    cover: "cover",
    urlDefault: "url_default",
    video: "video",
    media: "media",
    stream: "stream",
    h264: "h264",
    xsecToken: "xsec_token",
    time: "time",
  };
  // [VERIFY] selector/cookie có thể đổi — chỉnh tại đây.
  const HOST = "xiaohongshu.com";
  const SSR_KEY = "__INITIAL_STATE__";
  const LOGIN_COOKIES = { url: "https://www.xiaohongshu.com/", names: ["web_session"] };
  const SELECTORS = {
    captcha: [".red-captcha", '[class*="captcha"]'],
    login: [".login-container", '[class*="login-modal"]', ".login-box"],
    loadMore: null,
  };
  globalThis.__vfrAdapters = globalThis.__vfrAdapters || {};
  globalThis.__vfrAdapters.xhs = { FIELDS, HOST, SSR_KEY, LOGIN_COOKIES, SELECTORS };
})();
