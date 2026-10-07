// node --test tests/ext
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function loadJs(ctx, rel) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../../extension", rel), "utf8"), ctx);
}

function boot(host, ct = "application/json", text = null) {
  const posted = [];
  const body = text ?? JSON.stringify({ data: [{ item: { id: "1" } }], pad: "x".repeat(300) });
  const win = {
    postMessage: (m) => posted.push(m),
    fetch: async () => new Response(body, { headers: { "content-type": ct } }),
    addEventListener: () => {},
  };
  const XHR = function () {}; XHR.prototype.open = function () {}; XHR.prototype.addEventListener = function (e, f) { this._l = f; };
  const ctx = { window: win, location: { hostname: host, href: "https://" + host + "/x" }, document: { readyState: "loading", getElementById: () => null, querySelectorAll: () => [] },
    XMLHttpRequest: XHR, setTimeout, Response, TextDecoder, JSON, console };
  win.window = win;
  ctx.window = win;
  vm.createContext(ctx);
  // Nạp adapters trước inject.js, đúng thứ tự manifest.json.
  // Adapters và inject.js chung vm global nên globalThis.__vfrAdapters dùng chung được.
  for (const f of ["adapters/common.js", "adapters/douyin.js", "adapters/tiktok.js", "adapters/xhs.js"]) {
    loadJs(ctx, f);
  }
  loadJs(ctx, "inject.js");
  return { win, posted, XHR, ctx };
}

test("hook fetch: chuyển JSON API, bỏ URL không phải API", async () => {
  const { win, posted } = boot("www.tiktok.com");
  await win.fetch("https://www.tiktok.com/api/search/general/full/?q=a");
  await win.fetch("https://www.tiktok.com/static/app.js");
  await new Promise((r) => setTimeout(r, 20));
  assert.equal(posted.length, 1);
  assert.equal(posted[0].kind, "captured");
  assert.equal(posted[0].data.data[0].item.id, "1");
});

test("hook XHR: bắt response JSON", () => {
  const { XHR, posted } = boot("www.douyin.com");
  const x = new XHR();
  x.open("GET", "https://www.douyin.com/aweme/v1/web/general/search/single/");
  x.responseType = ""; x.responseText = JSON.stringify({ a: "y".repeat(300) });
  x._l();
  assert.equal(posted.length, 1);
});

test("không gắn hook hai lần", () => {
  const { win } = boot("www.tiktok.com");
  assert.equal(win.__vfrInjected, true);
});

test("hook fetch: search dạng stream gửi nguyên văn bản", async () => {
  const text = "data: " + JSON.stringify({ a: "y".repeat(300) }) + "\n\ndata: {}";
  const { win, posted } = boot("www.douyin.com", "text/event-stream", text);
  await win.fetch("https://www.douyin.com/aweme/v1/web/general/search/stream/?keyword=a");
  await new Promise((r) => setTimeout(r, 20));
  assert.equal(posted.length, 1);
  assert.equal(typeof posted[0].data, "string");
});
