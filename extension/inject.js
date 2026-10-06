// Chạy trong MAIN world. Chỉ làm 1 việc: chuyển mọi response JSON "giống API" lên content.js.
// KHÔNG parse nghiệp vụ ở đây (parse nằm ở Python).
(() => {
  if (window.__vfrInjected) return;
  window.__vfrInjected = true;
  const API_RE = /(\/api\/|\/aweme\/|\/web\/api\/|\/sns\/web\/)/;
  const MIN_LEN = 200;
  const SEARCH_RE = /\/search\//;

  const emit = (kind, url, data) => {
    try { window.postMessage({ __vfr: 1, kind, url: String(url), data }, "*"); } catch (e) {}
  };
  const interesting = (url) => { try { return API_RE.test(String(url)); } catch (e) { return false; } };

  const _fetch = window.fetch;
  window.fetch = async function (...args) {
    const res = await _fetch.apply(this, args);
    try {
      const url = typeof args[0] === "string" ? args[0] : (args[0] && args[0].url) || "";
      const ct = (res.headers && res.headers.get("content-type")) || "";
      if (interesting(url) && (/json/i.test(ct) || SEARCH_RE.test(url))) {
        res.clone().text().then((t) => {
          if (t.length < MIN_LEN) return;
          try { emit("captured", url, JSON.parse(t)); }
          catch (e) { if (SEARCH_RE.test(url)) emit("captured", url, t); }  // stream: Python tách
        }).catch(() => {});
      }
    } catch (e) {}
    return res;
  };

  const _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    try {
      if (interesting(url)) {
        this.addEventListener("load", () => {
          try {
            const t = this.responseType === "" || this.responseType === "text" ? this.responseText : "";
            if (t && t.length >= MIN_LEN && /^\s*[\[{]/.test(t)) emit("captured", url, JSON.parse(t));
          } catch (e) {}
        });
      }
    } catch (e) {}
    return _open.call(this, method, url, ...rest);
  };

  // Dữ liệu SSR của trang đầu (không đi qua fetch).
  const readState = () => {
    try {
      const host = location.hostname;
      if (host.includes("tiktok.com")) {
        const el = document.getElementById("__UNIVERSAL_DATA_FOR_REHYDRATION__");
        if (el && el.textContent) emit("state", location.href, JSON.parse(el.textContent));
      } else if (host.includes("douyin.com")) {
        const el = document.getElementById("RENDER_DATA");
        if (el && el.textContent) emit("state", location.href, JSON.parse(decodeURIComponent(el.textContent)));
      } else if (host.includes("xiaohongshu.com")) {
        if (window.__INITIAL_STATE__) emit("state", location.href, JSON.parse(JSON.stringify(window.__INITIAL_STATE__)));
      }
    } catch (e) {}
  };
  const schedule = () => setTimeout(readState, 1500);
  if (document.readyState === "complete") schedule();
  else window.addEventListener("load", schedule);
})();
