chrome.storage.local.get({ port: 8765, token: "" }).then((v) => {
  document.getElementById("port").value = v.port;
  document.getElementById("token").value = v.token;
});
document.getElementById("save").onclick = async () => {
  await chrome.storage.local.set({
    port: Number(document.getElementById("port").value) || 8765,
    token: document.getElementById("token").value.trim(),
  });
  document.getElementById("ok").textContent = "Đã lưu ✔";
};
