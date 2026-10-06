// Service worker: nối WS với app, mở cửa sổ cào, chuyển tiếp dữ liệu. Không parse nghiệp vụ.
const VERSION = "0.1.0";
const PROTOCOL = 1;
const HARD_LOGIN = {
  // [VERIFY] tên cookie phiên có thể đổi
  douyin: { url: "https://www.douyin.com/", names: ["sessionid", "sid_guard", "sessionid_ss"] },
  xhs: { url: "https://www.xiaohongshu.com/", names: ["web_session"] },
};

let ws = null;
let backoff = 1000;
const tasks = new Map();   // taskId -> { tabId, windowId, platform, cfg }
const tabToTask = new Map();

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
chrome.storage.onChanged.addListener(() => { if (ws) ws.close(); });
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
}

async function closeTask(taskId) {
  const info = tasks.get(taskId);
  if (!info) return;
  tasks.delete(taskId);
  tabToTask.delete(info.tabId);
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
      send({ type: "task_done", task_id: id, reason: "stopped", platform: info.platform });
    }
  }
});
