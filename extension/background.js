// Service worker: nối WS với app, mở cửa sổ cào, chuyển tiếp dữ liệu. Không parse nghiệp vụ.
// VFR003 + quy tắc 6: tên cookie phiên CHỈ nằm ở extension/adapters/ (single source of truth,
// không fallback hardcode ở đây). Thiếu adapters thì không chặn login (hành vi như TikTok).
try { importScripts("adapters/common.js", "adapters/douyin.js", "adapters/tiktok.js", "adapters/xhs.js"); } catch (e) {}
const VERSION = "0.1.1";
const PROTOCOL = 1;
const HARD_LOGIN = (() => {
  try {
    const a = globalThis.__vfrAdapters || {};
    const out = {};
    if (a.douyin && a.douyin.LOGIN_COOKIES) out.douyin = a.douyin.LOGIN_COOKIES;
    if (a.xhs && a.xhs.LOGIN_COOKIES) out.xhs = a.xhs.LOGIN_COOKIES;
    return out;
  } catch (e) { return {}; }
})();

let ws = null;
let backoff = 1000;
const tasks = new Map();   // taskId -> { tabId, windowId, platform, cfg }
const tabToTask = new Map();

// MV3 có thể kill service worker bất cứ lúc nào (mất Map trong RAM -> tab mồ côi).
// Lưu vào chrome.storage.session (sống qua SW restart, mất khi tắt Chrome — đúng semantics).
async function persistTasks() {
  try {
    await chrome.storage.session.set({ vfrTasks: [...tasks], vfrTabToTask: [...tabToTask] });
  } catch (e) {}
}
async function restoreTasks() {
  try {
    const { vfrTasks = [], vfrTabToTask = [] } = await chrome.storage.session.get({ vfrTasks: [], vfrTabToTask: [] });
    for (const [k, v] of vfrTasks) tasks.set(k, v);
    for (const [k, v] of vfrTabToTask) tabToTask.set(k, v);
  } catch (e) {}
}
restoreTasks();

const cfg = () => chrome.storage.local.get({ port: 8765, token: "" });
const send = (obj) => { if (ws && ws.readyState === 1) ws.send(JSON.stringify(obj)); };

async function connect() {
  if (ws && (ws.readyState === 0 || ws.readyState === 1)) return;
  const { port, token } = await cfg();
  try { ws = new WebSocket(`ws://127.0.0.1:${port}`); } catch (e) { return retry(); }
  ws.onopen = () => {
    backoff = 1000;
    send({ type: "hello", v: PROTOCOL, ver: VERSION, token, browser: "chrome" });
  };
  ws.onmessage = (ev) => { try { onApp(JSON.parse(ev.data)); } catch (e) { console.error(e); } };
  ws.onclose = () => { ws = null; retry(); };
  ws.onerror = () => {};
}
function retry() { setTimeout(connect, backoff); backoff = Math.min(backoff * 2, 10000); }

setInterval(() => send({ type: "ping", ts: Date.now() }), 20000);   // giữ service worker sống
chrome.alarms.create("keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(() => connect());
chrome.runtime.onStartup.addListener(connect);
chrome.runtime.onInstalled.addListener(connect);
chrome.storage.onChanged.addListener((changes, area) => {
  // Chỉ reconnect khi port/token (chrome.storage.local) đổi.
  // Bỏ qua chrome.storage.session do persistTasks() ghi — nếu không openTask
  // tự gây ws.close() -> reconnect loop, rớt message capture đang bay.
  if (area !== "local") return;
  if (!changes || (!changes.port && !changes.token)) return;
  if (ws) ws.close();
});
connect();

async function hasLogin(platform) {
  const rule = HARD_LOGIN[platform];
  if (!rule) return true;                       // TikTok: cảnh báo mềm, không chặn
  for (const name of rule.names) {
    const c = await chrome.cookies.get({ url: rule.url, name });
    if (c && c.value) return true;
  }
  return false;
}

async function openTask(t) {
  const win = await chrome.windows.create({
    url: t.url, focused: false, type: "popup", width: 640, height: 860, left: 20, top: 20,
  });
  const tab = win.tabs[0];
  tasks.set(t.task_id, { tabId: tab.id, windowId: win.id, platform: t.platform, cfg: {
    max_scrolls: t.max_scrolls, idle_limit: t.idle_limit } });
  tabToTask.set(tab.id, t.task_id);
  persistTasks();
}

async function closeTask(taskId) {
  const info = tasks.get(taskId);
  if (!info) return;
  tasks.delete(taskId);
  tabToTask.delete(info.tabId);
  persistTasks();
  try { await chrome.windows.remove(info.windowId); } catch (e) {}
}

async function onApp(msg) {
  if (msg.type === "task") {
    if (!(await hasLogin(msg.platform))) {
      return send({ type: "task_done", task_id: msg.task_id, reason: "login_required", platform: msg.platform });
    }
    await openTask(msg);
  } else if (msg.type === "resume") {
    await closeTask(msg.task_id);
    if (!(await hasLogin(msg.platform || guessPlatform(msg.url)))) {
      return send({ type: "task_done", task_id: msg.task_id, reason: "login_required" });
    }
    await openTask({ ...msg, platform: guessPlatform(msg.url) });
  } else if (msg.type === "stop") {
    const info = tasks.get(msg.task_id);
    if (info) { try { chrome.tabs.sendMessage(info.tabId, { type: "STOP" }); } catch (e) {} }
    await closeTask(msg.task_id);
  }
}
const guessPlatform = (u = "") => u.includes("tiktok.com") ? "tiktok" : u.includes("douyin.com") ? "douyin" : "xhs";

chrome.runtime.onMessage.addListener((msg, sender) => {
  const tabId = sender.tab && sender.tab.id;
  const taskId = tabToTask.get(tabId);
  if (!taskId) return;
  const info = tasks.get(taskId);
  if (msg.type === "READY") {
    chrome.tabs.sendMessage(tabId, { type: "START", cfg: info.cfg });
  } else if (msg.type === "CAPTURED") {
    send({ type: msg.kind === "state" ? "state" : "captured", task_id: taskId, platform: info.platform,
           api: msg.url, payload: msg.data, ts: Date.now() });
  } else if (msg.type === "PROGRESS") {
    send({ type: "progress", task_id: taskId, scrolls: msg.scrolls, idle_count: msg.idle });
  } else if (msg.type === "DONE") {
    send({ type: "task_done", task_id: taskId, reason: msg.reason, platform: info.platform });
    closeTask(taskId);
  }
});

chrome.windows.onRemoved.addListener((windowId) => {
  for (const [id, info] of tasks) {
    if (info.windowId === windowId) {           // người dùng tự đóng cửa sổ
      tasks.delete(id); tabToTask.delete(info.tabId);
      persistTasks();
      send({ type: "task_done", task_id: id, reason: "stopped", platform: info.platform });
    }
  }
});
