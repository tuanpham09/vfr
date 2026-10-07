// Isolated world: cầu nối + auto-scroll + phát hiện đăng nhập/captcha. Không có logic nghiệp vụ.
// VFR003: tên trường nghiệp vụ nằm ở extension/adapters/; file này chỉ dùng qua globalThis.__vfrAdapters.
(() => {
  const __adapters = (() => {
    try { return globalThis.__vfrAdapters || {}; } catch (e) { return {}; }
  })();
  const host = location.hostname;
  // Host nền tảng lấy từ adapters (HOST); fallback giữ hành vi cũ khi adapters thiếu.
  const PLATFORM = (() => {
    try {
      for (const k of ["tiktok", "douyin", "xhs"]) {
        const a = __adapters[k];
        if (a && a.HOST && host.includes(a.HOST)) return k;
      }
    } catch (e) {}
    return host.includes("tiktok.com") ? "tiktok" : host.includes("douyin.com") ? "douyin" : "xhs";
  })();

  // [VERIFY] selector là single source ở extension/adapters/*.js (SELECTORS).
  // Không fallback hardcode ở đây (VFR003 + quy tắc 6). Manifest nạp adapters trước
  // content.js; thiếu adapters thì dùng bộ rỗng (không chặn, không phát hiện login/captcha).
  const ADAPTER = (() => {
    try {
      const a = __adapters[PLATFORM];
      if (a && a.SELECTORS) {
        const s = a.SELECTORS;
        const loadMore = s.loadMoreRe ? new RegExp(s.loadMoreRe, "i")
          : (s.loadMore ? new RegExp(s.loadMore, "i") : null);
        return { captcha: s.captcha || [], login: s.login || [], loadMore: loadMore };
      }
    } catch (e) {}
    return { captcha: [], login: [], loadMore: null };
  })();

  let capturedTotal = 0;
  let run = null;

  window.addEventListener("message", (e) => {
    if (e.source !== window || !e.data || !e.data.__vfr) return;
    if (!e.data.url) return;   // trigger nội bộ (scan_dom): không phải dữ liệu, không đếm idle
    // Chặn page script giả mạo: chỉ nhận kind/url/data đúng shape.
    const kind = e.data.kind;
    const url = String(e.data.url || "");
    if (kind !== "captured" && kind !== "state") return;
    if (!/^(https?:\/\/|dom:\/\/)/i.test(url)) return;
    const payload = e.data.data;
    if (payload === null || (typeof payload !== "object" && typeof payload !== "string")) return;
    capturedTotal++;
    if (run) run.newSinceStep++;
    chrome.runtime.sendMessage({ type: "CAPTURED", kind: kind, url: url, data: payload });
  });

  const visible = (el) => !!(el && el.offsetParent !== null && el.getBoundingClientRect().height > 0);
  const anyVisible = (sels) => sels.some((s) => { try { return visible(document.querySelector(s)); } catch (e) { return false; } });
  const rnd = (a, b) => a + Math.random() * (b - a);

  function scroller() {
    let best = document.scrollingElement || document.documentElement;
    let bestH = best.scrollHeight - best.clientHeight;
    for (const el of document.querySelectorAll("div,main,section")) {
      const cs = getComputedStyle(el);
      if ((cs.overflowY === "auto" || cs.overflowY === "scroll") && el.clientHeight > 300) {
        const h = el.scrollHeight - el.clientHeight;
        if (h > bestH) { best = el; bestH = h; }
      }
    }
    return best;
  }

  function clickLoadMore() {
    if (!ADAPTER.loadMore) return;
    for (const b of document.querySelectorAll("button")) {
      if (visible(b) && ADAPTER.loadMore.test(b.textContent || "")) { b.click(); return; }
    }
  }

  function finish(reason) {
    if (!run) return;
    clearTimeout(run.timer);
    run = null;
    chrome.runtime.sendMessage({ type: "DONE", reason });
  }

  function step() {
    if (!run) return;
    if (anyVisible(ADAPTER.captcha)) return finish("captcha");

    // Chỉ quét DOM dự phòng nếu mạng không trả dữ liệu sau 2 bước cuộn,
    // tối đa 1 lần/20s để không bắn trùng batch.
    // Chỉ nhờ MAIN world (inject.js) quét — không chạy scanDomFallback() local
    // song song để tránh bắn 2 batch dom://douyin/search trùng nhau.
    if (PLATFORM === "douyin" && run.idle >= 2
        && (!run.lastDomScan || Date.now() - run.lastDomScan > 20000)) {
      run.lastDomScan = Date.now();
      window.postMessage({ __vfr: 1, action: "scan_dom" }, "*");
    }

    if (run.steps > 0) run.idle = run.newSinceStep === 0 ? run.idle + 1 : 0;
    run.newSinceStep = 0;
    if (run.idle >= run.cfg.idle_limit) {
      if (capturedTotal === 0 && anyVisible(ADAPTER.login)) return finish("login_required");
      return finish("idle");
    }
    if (run.steps >= run.cfg.max_scrolls) return finish("max_scroll");

    if (run.steps % 5 === 0) run.el = scroller();
    const el = run.el || scroller();
    const dy = rnd(600, 1400);
    el.scrollBy({ top: Math.random() < 0.1 ? -dy / 3 : dy, behavior: "smooth" });
    window.scrollBy({ top: dy, behavior: "smooth" });
    if (run.steps % 3 === 2) clickLoadMore();
    run.steps++;
    if (run.steps % 4 === 0) chrome.runtime.sendMessage({ type: "PROGRESS", scrolls: run.steps, idle: run.idle });
    const pause = Math.random() < 0.15 ? rnd(3000, 8000) : rnd(1500, 4000);
    run.timer = setTimeout(step, pause);
  }

  function start(cfg) {
    if (run) clearTimeout(run.timer);
    run = { cfg: { max_scrolls: 40, idle_limit: 5, ...cfg }, steps: 0, idle: 0, newSinceStep: 0, timer: null, el: null };
    capturedTotal = 0;
    // Task mới trên cùng trang: nhờ MAIN world reset dedupe DOM để video
    // trùng task trước vẫn được emit lại (runner dedupe theo task riêng).
    try { window.postMessage({ __vfr: 1, action: "reset_dom" }, "*"); } catch (e) {}
    // chờ trang tải + nhận dữ liệu mạng trước khi cuộn
    run.timer = setTimeout(step, rnd(3000, 5000));
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "START") start(msg.cfg || {});
    else if (msg.type === "STOP") { if (run) { clearTimeout(run.timer); run = null; } }
  });

  chrome.runtime.sendMessage({ type: "READY", platform: PLATFORM });
})();
