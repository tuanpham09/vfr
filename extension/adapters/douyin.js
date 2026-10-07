// Adapter Douyin: nơi duy nhất trong extension chứa từ khóa nghiệp vụ Douyin (VFR003).
// content.js / inject.js gọi qua globalThis.__vfrAdapters.douyin, không hardcode tên trường.
// Parse nghiệp vụ thật nằm ở Python (core/pipeline/normalizers/douyin.py);
// JS chỉ forward JSON thô, hoặc dựng stub tối thiểu cho DOM fallback để Python normalize.
// File chạy được ở cả MAIN world và isolated world (load trước inject.js / content.js).
(function () {
  const FIELDS = {
    id: "aweme_id",
    stats: "statistics",
    video: "video",
    author: "author",
    desc: "desc",
    nickname: "nickname",
    secUid: "sec_uid",
    cover: "cover",
    urlList: "url_list",
    playAddr: "play_addr",
    duration: "duration",
    digg: "digg_count",
    comment: "comment_count",
    collect: "collect_count",
    share: "share_count",
  };
  // Dấu hiệu nhận chunk stream Douyin trong text thô.
  const MARKER = FIELDS.id;
  // Pattern URL API Douyin (VFR003: chỉ nằm ở adapter, không rải trong inject.js).
  const URL_RE = /aweme/i;

  // Bóc item thô từ React props (fiber). Ưu tiên p.aweme/p.awemeInfo/p.item/p.data/p.videoInfo, rồi chính p.
  function pickFromProps(p) {
    if (!p || typeof p !== "object") return null;
    const cand = p.aweme || p.awemeInfo || p.item || p.data || p.videoInfo;
    if (cand && typeof cand === "object" && (cand[FIELDS.id] || cand[FIELDS.stats])) return cand;
    if (p[FIELDS.id] && p[FIELDS.stats]) return p;
    return null;
  }

  // Stub tối thiểu cho DOM fallback (shape Python hiểu). Số liệu null = chưa có.
  function buildDomStub(o) {
    const stats = {};
    stats[FIELDS.digg] = o.likeText || null;
    stats[FIELDS.comment] = null;
    stats[FIELDS.collect] = null;
    stats[FIELDS.share] = null;
    const cover = {};
    cover[FIELDS.urlList] = o.cover ? [o.cover] : [];
    const playAddr = {};
    playAddr[FIELDS.urlList] = [];
    const video = {};
    video[FIELDS.cover] = cover;
    video[FIELDS.playAddr] = playAddr;
    video[FIELDS.duration] = o.durationMs || 0;
    const author = {};
    author[FIELDS.nickname] = o.authorName || "";
    author[FIELDS.secUid] = o.authorId || "";
    const item = {};
    item[FIELDS.id] = o.vid;
    item[FIELDS.desc] = o.desc || "";
    item[FIELDS.author] = author;
    item[FIELDS.stats] = stats;
    item[FIELDS.video] = video;
    return item;
  }

  function itemId(it) {
    return (it && it[FIELDS.id]) || "";
  }

  // [VERIFY] selector/cookie có thể đổi — chỉnh tại đây, không rải trong content.js/background.js.
  const HOST = "douyin.com";
  const SSR_ID = "RENDER_DATA";
  const LOGIN_COOKIES = { url: "https://www.douyin.com/", names: ["sessionid", "sid_guard", "sessionid_ss"] };
  const SELECTORS = {
    captcha: ["#captcha_container", ".captcha_verify_container", '[class*="captcha_verify"]'],
    login: ["#login-pannel", '[id*="login-panel"]', '[class*="login-panel"]'],
    loadMore: null,
  };
  const DOM = {
    searchCard: '[data-e2e="search_result_item"]',
    videoLink: 'a[href*="/video/"]',
    videoIdRe: /\/video\/(\d+)/,
    userLink: 'a[href*="/user/"]',
    userIdRe: /\/user\/([^/?#]+)/,
    // Selector heuristic cho stub DOM fallback (text thô, Python parse số liệu).
    // [VERIFY] class nội bộ Douyin có thể đổi theo đợt deploy.
    titleSel: '[class*="title"], [class*="desc"], [class*="info"], h3, p',
    likeSel: '[class*="like"], [class*="digg"], [class*="heart"], [class*="count"]',
    timeSel: '[class*="time"], [class*="duration"]',
  };

  globalThis.__vfrAdapters = globalThis.__vfrAdapters || {};
  globalThis.__vfrAdapters.douyin = {
    FIELDS, MARKER, URL_RE, HOST, SSR_ID, LOGIN_COOKIES, SELECTORS, DOM,
    pickFromProps, buildDomStub, itemId,
  };
})();
