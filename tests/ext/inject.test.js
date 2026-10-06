// node --test tests/ext
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function boot(host) {
  const posted = [];
  const body = JSON.stringify({ data: [{ item: { id: "1" } }], pad: "x".repeat(300) });
  const win = {
    postMessage: (m) => posted.push(m),
    fetch: async (url) => new Response(body, { headers: { "content-type": "application/json" } }),
    addEventListener: () => {},
  };
  const XHR = function () {}; XHR.prototype.open = function () {}; XHR.prototype.addEventListener = function (e, f) { this._l = f; };
  const ctx = { window: win, location: { hostname: host, href: "https://" + host + "/x" }, document: { readyState: "loading", getElementById: () => null },
    XMLHttpRequest: XHR, setTimeout, Response, JSON, console };
  win.window = win;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../../extension/inject.js"), "utf8"), ctx);
  return { win, posted, XHR };
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
