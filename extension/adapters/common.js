// Adapter chung: pattern URL + ngưỡng forward. Nạp trước mọi script khác (xem manifest.json).
// VFR003: pattern URL chỉ nằm ở đây, không rải trong inject.js / content.js.
(function () {
  const API_RE = /(\/api\/|\/aweme\/|\/web\/api\/|\/sns\/web\/|\/search\/|\/discover\/|\/general\/)/i;
  const MIN_LEN = 150;
  const SEARCH_RE = /(\/search\/|\/discover\/|\/general\/|search_item)/i;
  globalThis.__vfrAdapters = globalThis.__vfrAdapters || {};
  globalThis.__vfrAdapters.common = { API_RE: API_RE, MIN_LEN: MIN_LEN, SEARCH_RE: SEARCH_RE };
})();
