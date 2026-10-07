// Adapter TikTok: chuẩn từ khóa nghiệp vụ (VFR003). Runtime hiện chỉ forward JSON thô
// (xem inject.js); parse nằm ở core/pipeline/normalizers/tiktok.py.
// Tên trường/API pattern là [VERIFY] tới khi có fixture thật (docs/platforms/tiktok.md).
(function () {
  const FIELDS = {
    id: "id",
    stats: "stats",
    statsV2: "statsV2",
    video: "video",
    desc: "desc",
    author: "author",
    uniqueId: "uniqueId",
    nickname: "nickname",
    playAddr: "playAddr",
    downloadAddr: "downloadAddr",
    cover: "cover",
    originCover: "originCover",
    dynamicCover: "dynamicCover",
    duration: "duration",
    playCount: "playCount",
    diggCount: "diggCount",
    commentCount: "commentCount",
    collectCount: "collectCount",
    shareCount: "shareCount",
    textExtra: "textExtra",
    hashtagName: "hashtagName",
    anchors: "anchors",
    anchorType: "type",
    componentKey: "component_key",
    isECVideo: "isECVideo",
    extra: "extra",
    createTime: "createTime",
  };
  const API_PATTERNS = ["search/item", "search/general", "challenge/item_list", "post/item_list"];
  // [VERIFY] selector/cookie có thể đổi — chỉnh tại đây.
  const HOST = "tiktok.com";
  const SSR_ID = "__UNIVERSAL_DATA_FOR_REHYDRATION__";
  const SELECTORS = {
    captcha: ["#captcha_container", ".captcha-verify-container", '[id*="captcha-verify"]'],
    login: [],
    loadMoreRe: "load more|tải thêm|xem thêm",
  };
  globalThis.__vfrAdapters = globalThis.__vfrAdapters || {};
  globalThis.__vfrAdapters.tiktok = { FIELDS, API_PATTERNS, HOST, SSR_ID, SELECTORS };
})();
