// Chạy trong MAIN world. Chỉ làm 1 việc: chuyển mọi response JSON "giống API" lên content.js.
// KHÔNG parse nghiệp vụ ở đây (parse nằm ở Python).
// VFR003 + quy tắc 6: pattern URL + tên trường nghiệp vụ CHỈ nằm ở extension/adapters/
// (single source of truth, không fallback hardcode ở đây). Manifest nạp adapters trước
// file này; thiếu adapters thì không hook để tránh forward sai.
(() => {
  const __A = (() => { try { return globalThis.__vfrAdapters || null; } catch (e) { return null; } })();
  // P0: chỉ yêu cầu common. Thiếu common thì không hook; thiếu douyin adapter
  // thì TikTok/XHS vẫn hook bình thường, riêng tính năng Douyin giảm cấp.
  if (!__A || !__A.common || !__A.common.API_RE || !__A.common.SEARCH_RE) return;
  if (window.__vfrInjected) return;
  window.__vfrInjected = true;

  const API_RE = __A.common.API_RE;
  const MIN_LEN = __A.common.MIN_LEN || 150;
  const SEARCH_RE = __A.common.SEARCH_RE;
  const __dy = function () { try { return __A.douyin || null; } catch (e) { return null; } };
  // Test URL API Douyin qua adapter (tùy chọn — thiếu thì coi như không phải URL Douyin).
  const __dyUrlOk = function (u) {
    try {
      const a = __dy();
      if (!a || !a.URL_RE) return false;
      return a.URL_RE.test(String(u));
    } catch (e) { return false; }
  };
  // Dấu hiệu chunk stream Douyin trong text thô (tên trường từ adapter, tùy chọn).
  const __dyMarker = function () {
    try {
      const a = __dy();
      if (!a) return "";
      return a.MARKER || "";
    } catch (e) { return ""; }
  };

  const emit = (kind, url, data) => {
    try { window.postMessage({ __vfr: 1, kind, url: String(url), data }, "*"); } catch (e) {}
  };

  const getUrl = (arg) => {
    if (!arg) return "";
    if (typeof arg === "string") return arg;
    if (arg.url) return String(arg.url);
    if (arg.href) return String(arg.href);
    return String(arg);
  };

  const interesting = (url) => {
    try { return API_RE.test(String(url)); } catch (e) { return false; }
  };

  function handleBody(url, clone, ct) {
    const isStream = /stream/i.test(ct);
    // HTML trên URL search (trang SSR, error page) không phải dữ liệu API:
    // chặn ngay để phía Python không tạo item rác.
    if (/text\/html/i.test(ct || "") && !isStream) return;

    // 1. Thử đọc dạng stream (chunked / SSE) nếu có getReader
    if (clone.body && typeof clone.body.getReader === "function") {
      const reader = clone.body.getReader();
      const decoder = typeof TextDecoder !== "undefined"
        ? new TextDecoder()
        : { decode: (v) => (typeof v === "string" ? v : String(v)) };
      let total = "";

      function pump() {
        reader.read().then(({ done, value }) => {
          if (value && decoder) {
            const chunk = decoder.decode(value, { stream: !done });
            total += chunk;
          }
          if (!done) {
            pump();
          } else {
            // Khi toàn bộ body đã đọc xong: chỉ emit một lần bản đầy đủ nhất.
            // Không emit từng chunk cộng dồn giữa chừng để tránh normalize
            // trùng cùng video_id N+1 lần (upsert lặp, progress giật).
            if (total.length >= MIN_LEN) {
              try {
                emit("captured", url, JSON.parse(total));
              } catch (e) {
                const m = __dyMarker();
                if (SEARCH_RE.test(url) || __dyUrlOk(url) || (m && total.includes(m)) || isStream) {
                  emit("captured", url, total);
                }
              }
            }
          }
        }).catch(() => {});
      }
      pump();
      return;
    }

    // 2. Fallback nếu không có getReader
    clone.text().then((t) => {
      if (!t || t.length < MIN_LEN) return;
      try { emit("captured", url, JSON.parse(t)); }
      catch (e) {
        const mm = __dyMarker();
        if (SEARCH_RE.test(url) || (mm && t.includes(mm)) || isStream) emit("captured", url, t);
      }
    }).catch(() => {});
  }

  const _fetch = window.fetch;
  window.fetch = function (...args) {
    const p = _fetch.apply(this, args);
    try {
      const url = getUrl(args[0]);
      if (interesting(url)) {
        p.then((res) => {
          try {
            const ct = (res.headers && res.headers.get("content-type")) || "";
            if (/json/i.test(ct) || SEARCH_RE.test(url) || /stream/i.test(ct)) {
              handleBody(url, res.clone(), ct);
            }
          } catch (e) {}
        }).catch(() => {});
      }
    } catch (e) {}
    return p;
  };

  const _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    try {
      const u = getUrl(url);
      if (interesting(u)) {
        this.addEventListener("load", () => {
          try {
            // Trang đặt responseType="json": responseText rỗng, đọc this.response.
            if (this.responseType === "json" && this.response != null) {
              if (typeof this.response === "object") {
                emit("captured", u, this.response);
                return;
              }
              const rs = String(this.response);
              if (rs.length >= MIN_LEN) {
                try { emit("captured", u, JSON.parse(rs)); }
                catch (e) {
                  const mk0 = __dyMarker();
                  if (SEARCH_RE.test(u) || /data:\s*\{/i.test(rs) || (mk0 && rs.includes(mk0))) {
                    emit("captured", u, rs);
                  }
                }
              }
              return;
            }
            const t = this.responseType === "" || this.responseType === "text" ? this.responseText : "";
            if (t && t.length >= MIN_LEN) {
              try {
                emit("captured", u, JSON.parse(t));
              } catch (e) {
                const mk = __dyMarker();
                if (SEARCH_RE.test(u) || /data:\s*\{/i.test(t) || (mk && t.includes(mk))) {
                  emit("captured", u, t);
                }
              }
            }
          } catch (e) {}
        });
      }
    } catch (e) {}
    return _open.call(this, method, url, ...rest);
  };

  // Dữ liệu SSR của trang đầu (không đi qua fetch).
  // [VERIFY] ID SSR CHỈ nằm ở adapters (tiktok.SSR_ID, douyin.SSR_ID, xhs.SSR_KEY).
  // Không fallback hardcode ở đây (VFR003). P0: yêu cầu theo từng platform —
  // thiếu adapter nào thì chỉ bỏ SSR của platform đó, không tắt cả 3.
  const __ssrIds = function () {
    try {
      const a = globalThis.__vfrAdapters || {};
      return {
        tiktok: (a.tiktok && a.tiktok.SSR_ID) || null,
        douyin: (a.douyin && a.douyin.SSR_ID) || null,
        xhsKey: (a.xhs && a.xhs.SSR_KEY) || null,
      };
    } catch (e) { return { tiktok: null, douyin: null, xhsKey: null }; }
  };
  const readState = () => {
    try {
      const ids = __ssrIds();
      if (!ids) return;
      const host = location.hostname;
      if (host.includes("tiktok.com")) {
        if (!ids.tiktok) return;
        const el = document.getElementById(ids.tiktok);
        if (el && el.textContent) emit("state", location.href, JSON.parse(el.textContent));
      } else if (host.includes("douyin.com")) {
        if (!ids.douyin) return;
        const el = document.getElementById(ids.douyin);
        if (el && el.textContent) {
          // RENDER_DATA thường URI-encoded; fallback JSON thuần nếu decode lỗi
          // (desc chứa "%" làm decodeURIComponent ném URIError).
          try {
            emit("state", location.href, JSON.parse(decodeURIComponent(el.textContent)));
          } catch (e1) {
            try { emit("state", location.href, JSON.parse(el.textContent)); } catch (e2) {}
          }
        }
      } else if (host.includes("xiaohongshu.com")) {
        if (!ids.xhsKey) return;
        if (window[ids.xhsKey]) emit("state", location.href, JSON.parse(JSON.stringify(window[ids.xhsKey])));
      }
    } catch (e) {}
  };

  const seenDomIds = new Set();
  let lastDomSig = "";
  function scanDouyinDom() {
    try {
      const __ad = __dy();
      if (!__ad || !__ad.DOM || !__ad.HOST) return;
      const __dom = __ad.DOM;
      const __host = __ad.HOST;
      const __cardSel = __dom.searchCard;
      const __linkSel = __dom.videoLink;
      const __vidRe = __dom.videoIdRe;
      const __userSel = __dom.userLink;
      const __userRe = __dom.userIdRe;
      const __titleSel = __dom.titleSel;
      const __likeSel = __dom.likeSel;
      const __timeSel = __dom.timeSel;
      if (!__cardSel || !__linkSel || !__vidRe) return;
      if (!location.hostname.includes(__host)) return;
      if (typeof document === "undefined" || !document.querySelectorAll) return;
      // Chỉ card kết quả tìm kiếm — không quơ link video ở rail gợi ý/sidebar.
      const links = document.querySelectorAll(__cardSel + " " + __linkSel);
      if (!links || links.length === 0) return;

      const items = [];
      links.forEach((a) => {
        try {
          const href = a.getAttribute("href") || a.href || "";
          const m = href.match(__vidRe);
          if (!m) return;
          const vid = m[1];
          if (seenDomIds.has(vid)) return;

          let rawItem = null;
          const card = (a.closest && a.closest(__cardSel)) || a;
          const targetEl = card || a;

          for (const k of Object.keys(targetEl)) {
            if (k.startsWith("__reactFiber") || k.startsWith("__reactInternalInstance")) {
              let cur = targetEl[k];
              for (let i = 0; i < 20 && cur; i++) {
                const p = cur.memoizedProps || cur.props;
                if (p) {
                  const it = __ad ? __ad.pickFromProps(p) : null;
                  if (it) {
                    rawItem = it;
                    break;
                  }
                }
                cur = cur.return;
              }
              if (rawItem) break;
            }
          }

          if (rawItem) {
            seenDomIds.add(vid);
            items.push(rawItem);
            return;
          }

          const img = card ? card.querySelector("img") : a.querySelector("img");
          let cover = img ? (img.currentSrc || img.src || img.getAttribute("src") || "") : "";
          if (cover && cover.startsWith("//")) cover = "https:" + cover;

          const titleEl = card ? card.querySelector(__titleSel) : null;
          const desc = (titleEl ? titleEl.textContent : (img && img.alt ? img.alt : a.textContent || "")).trim();

          const authorA = card ? card.querySelector(__userSel) : null;
          const authorName = authorA ? authorA.textContent.trim() : "";
          const authorHref = authorA ? (authorA.getAttribute("href") || "") : "";
          const authorM = authorHref.match(__userRe);
          const authorId = authorM ? authorM[1] : "";

          const likeEl = card ? card.querySelector(__likeSel) : null;
          const likeText = likeEl ? likeEl.textContent.trim() : "";

          const timeEl = card ? card.querySelector(__timeSel) : null;
          let durationS = null;
          if (timeEl) {
            const parts = timeEl.textContent.trim().split(":");
            if (parts.length === 2) {
              durationS = parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
            }
          }

          seenDomIds.add(vid);
          // Stub tối thiểu dựng qua adapter (không hardcode tên trường ở đây).
          if (__ad && __ad.buildDomStub) {
            items.push(__ad.buildDomStub({
              vid: vid, desc: desc, authorName: authorName, authorId: authorId,
              cover: cover, likeText: likeText, durationMs: durationS ? durationS * 1000 : 0,
            }));
          }
        } catch (e) {}
      });

      if (items.length > 0) {
        const __idOf = function (it) {
          try {
            if (__ad && __ad.itemId) return __ad.itemId(it) || "";
          } catch (e) {}
          return "";
        };
        const sig = items.length + ":" + items.map(__idOf).join(",");
        if (sig === lastDomSig) return;   // batch y hệt lần trước -> không emit lại
        lastDomSig = sig;
        emit("captured", "dom://douyin/search", { data: items });
      }
    } catch (e) {}
  }

  window.addEventListener("message", (e) => {
    if (e.data && e.data.__vfr && e.data.action === "scan_dom") {
      scanDouyinDom();
    } else if (e.data && e.data.__vfr && e.data.action === "reset_dom") {
      // Task mới trên cùng trang: xóa dedupe DOM để video trùng với task
      // trước vẫn được emit lại (runner dedupe theo task riêng).
      seenDomIds.clear();
      lastDomSig = "";
    }
  });

  const schedule = () => setTimeout(readState, 1500);
  if (document.readyState === "complete") schedule();
  else window.addEventListener("load", schedule);
})();
