const socketStatus = document.querySelector("#socketStatus");
const brainStatusEl = document.querySelector("#brainStatus");
const chatModeEl = document.querySelector("#chatMode");
const stateEl = document.querySelector("#state");
const scoreEl = document.querySelector("#score");
const selectedMessageEl = document.querySelector("#selectedMessage");
const reasonsEl = document.querySelector("#reasons");
const decisionReasonEl = document.querySelector("#decisionReason");
const speakEl = document.querySelector("#speak");
const emotionEl = document.querySelector("#emotion");
const gestureEl = document.querySelector("#gesture");
const obsActionEl = document.querySelector("#obsAction");
const outputSafetyEl = document.querySelector("#outputSafety");
const recentMessagesEl = document.querySelector("#recentMessages");
const safetyLogsEl = document.querySelector("#safetyLogs");
const memoryLogsEl = document.querySelector("#memoryLogs");
const testTextEl = document.querySelector("#testText");
const sendTestEl = document.querySelector("#sendTest");

let socket;

function connect() {
  socket = new WebSocket(`ws://${window.location.host}`);

  socket.addEventListener("open", () => {
    socketStatus.textContent = "已连接";
  });

  socket.addEventListener("close", () => {
    socketStatus.textContent = "已断开，重连中";
    setTimeout(connect, 1000);
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "snapshot") {
      render(data.payload);
    }
  });
}

function send(action, extra = {}) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }
  socket.send(JSON.stringify({ action, ...extra }));
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => send(button.dataset.action));
});

sendTestEl.addEventListener("click", () => {
  const text = testTextEl.value.trim();
  if (text) {
    send("send_test_message", { text });
  }
});

testTextEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendTestEl.click();
  }
});

function render(snapshot) {
  stateEl.textContent = snapshot.state;
  stateEl.dataset.state = snapshot.state;
  renderBrainStatus(snapshot.brain);
  renderChatMode(snapshot.chatMode);
  scoreEl.textContent = `score ${snapshot.selection?.score ?? 0}`;

  renderSelected(snapshot.selectedMessage);
  renderReasons(snapshot.selection?.reasons ?? []);
  decisionReasonEl.textContent = snapshot.decisionReason || "尚无决策";

  const output = snapshot.output;
  speakEl.textContent = output?.speak ?? "等待输出";
  emotionEl.textContent = `emotion: ${output?.emotion ?? "none"}`;
  gestureEl.textContent = `gesture: ${output?.gesture ?? "none"}`;
  obsActionEl.textContent = `obsAction: ${output?.obsAction ?? "none"}`;
  outputSafetyEl.textContent = `safety: ${output?.safety ?? "none"}`;

  renderMessages(snapshot.recentMessages ?? []);
  renderSafety(snapshot.safetyLogs ?? []);
  renderMemory(snapshot.memoryLogs ?? []);
}

function renderChatMode(chatMode) {
  chatModeEl.dataset.mode = chatMode ?? "manual";
  chatModeEl.textContent = chatMode === "mock_auto" ? "Mock auto chat" : "Manual chat";
}

function renderBrainStatus(brain) {
  if (!brain) {
    brainStatusEl.textContent = "LLM: unknown";
    brainStatusEl.dataset.mode = "unknown";
    return;
  }

  brainStatusEl.dataset.mode = brain.mode;
  if (brain.mode === "local_llm") {
    const ctx = brain.numCtx ? ` / ctx ${brain.numCtx}` : "";
    brainStatusEl.textContent = `Local LLM: ${brain.provider} / ${brain.model}${ctx}`;
    return;
  }

  if (brain.mode === "local_brain") {
    brainStatusEl.textContent = `Mika v3: ${brain.llm === "ollama" ? brain.model : "fast brain"}`;
    return;
  }

  brainStatusEl.textContent = `Brain: ${brain.model}`;
}

function renderSelected(message) {
  if (!message) {
    selectedMessageEl.className = "message-empty";
    selectedMessageEl.textContent = "暂无选中弹幕";
    return;
  }

  selectedMessageEl.className = "message selected";
  selectedMessageEl.innerHTML = `
    <div class="meta">
      <strong>${escapeHtml(message.username)}</strong>
      <span>${escapeHtml(message.type)}</span>
      ${message.amount ? `<span>${message.amount}</span>` : ""}
    </div>
    <p>${escapeHtml(message.text)}</p>
  `;
}

function renderReasons(reasons) {
  reasonsEl.innerHTML = reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("");
}

function renderMessages(messages) {
  recentMessagesEl.innerHTML = messages
    .map(
      (message) => `
        <div class="message ${escapeHtml(message.type)}">
          <div class="meta">
            <strong>${escapeHtml(message.username)}</strong>
            <span>${escapeHtml(message.type)}</span>
            <time>${formatTime(message.timestamp)}</time>
          </div>
          <p>${escapeHtml(message.text)}</p>
        </div>
      `
    )
    .join("");
}

function renderSafety(logs) {
  safetyLogsEl.innerHTML = logs
    .map(
      (entry) => `
        <div class="log ${entry.result.safe ? "ok" : "blocked"}">
          <div class="meta">
            <strong>${escapeHtml(entry.direction)}</strong>
            <span>${entry.result.safe ? "safe" : escapeHtml(entry.result.category || "blocked")}</span>
            <time>${formatTime(entry.timestamp)}</time>
          </div>
          <p>${escapeHtml(entry.text)}</p>
          <small>${escapeHtml(entry.result.reason || "通过")}</small>
        </div>
      `
    )
    .join("");
}

function renderMemory(logs) {
  memoryLogsEl.innerHTML = logs
    .map(
      (entry) => `
        <div class="log">
          <div class="meta">
            <strong>${escapeHtml(entry.action)}</strong>
            <time>${formatTime(entry.timestamp)}</time>
          </div>
          <p>${escapeHtml(entry.content)}</p>
        </div>
      `
    )
    .join("");
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString("zh-CN", { hour12: false });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

connect();
