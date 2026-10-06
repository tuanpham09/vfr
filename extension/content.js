// Isolated world: cầu nối + auto-scroll + phát hiện đăng nhập/captcha. Không có logic nghiệp vụ.
(() => {
  const host = location.hostname;
  const PLATFORM = host.includes("tiktok.com") ? "tiktok" : host.includes("douyin.com") ? "douyin" : "xhs";

  // [VERIFY] selector có thể đổi — chỉnh tại đây.
  const ADAPTER = {
    tiktok: { captcha: ['#captcha_container', '.captcha-verify-container', '[id*="captcha-verify"]'],
              login: [], loadMore: /load more|tải thêm|xem thêm/i },
    douyin: { captcha: ['#captcha_container', '.captcha_verify_container', '[class*="captcha_verify"]'],
              login: ['#login-pannel', '[id*="login-panel"]', '[class*="login-panel"]'], loadMore: null },
    xhs:    { captcha: ['.red-captcha', '[class*="captcha"]'],
              login: ['.login-container', '[class*="login-modal"]', '.login-box'], loadMore: null },
  }[PLATFORM];

  let capturedTotal = 0;
  let run = null;

  window.addEventListener("message", (e) => {
    if (e.source !== window || !e.data || !e.data.__vfr) return;
    capturedTotal++;
    if (run) run.newSinceStep++;
    chrome.runtime.sendMessage({ type: "CAPTURED", kind: e.data.kind, url: e.data.url, data: e.data.data });
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
    if (run.steps % 3 === 2) clickLoadMore();
    run.steps++;
    if (run.steps % 4 === 0) chrome.runtime.sendMessage({ type: "PROGRESS", scrolls: run.steps, idle: run.idle });
    const pause = Math.random() < 0.15 ? rnd(3000, 8000) : rnd(1500, 4000);
    run.timer = setTimeout(step, pause);
  }

  function start(cfg) {
    if (run) clearTimeout(run.timer);
    run = { cfg: { max_scrolls: 40, idle_limit: 3, ...cfg }, steps: 0, idle: 0, newSinceStep: 0, timer: null, el: null };
    // chờ trang tải + nhận dữ liệu SSR trước khi cuộn
    run.timer = setTimeout(step, rnd(3000, 5000));
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "START") start(msg.cfg || {});
    else if (msg.type === "STOP") { if (run) { clearTimeout(run.timer); run = null; } }
  });

  chrome.runtime.sendMessage({ type: "READY", platform: PLATFORM });
})();
