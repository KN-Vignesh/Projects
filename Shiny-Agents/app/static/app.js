const state = {
  agent: "crewai",
  history: [],
  usage: null,
  // Keep BYOK memory-only; never persist a user secret in browser storage.
  personalKey: "",
};

const labels = { crewai: "CrewAI", "agents-sdk": "Agents SDK", langgraph: "LangGraph" };
const messages = document.querySelector("#messages");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const send = document.querySelector("#send-button");
const accessSummary = document.querySelector("#access-summary");
const accessPill = document.querySelector("#access-pill");
const trialUsage = document.querySelector("#trial-usage");
const agentStatus = document.querySelector("#agent-status");
const modal = document.querySelector("#key-modal");
const modalKeyInput = document.querySelector("#modal-api-key");
const toggleKeyVisibility = document.querySelector("#toggle-key-visibility");

function addMessage(role, text) {
  const element = document.createElement("div");
  element.className = `message ${role}`;
  element.textContent = text;
  messages.appendChild(element);
  messages.scrollTop = messages.scrollHeight;
}

function setAgentStatus(text) {
  agentStatus.textContent = text;
}

function updateUsage(data) {
  state.usage = data;
  const remaining = Math.max(0, Number(data.remaining ?? data.limit - data.uses ?? 0));
  const inTrial = data.has_default_key && remaining > 0;

  trialUsage.textContent = `${data.uses ?? 0} / ${data.limit ?? 3}`;
  accessPill.textContent = inTrial
    ? "Free trial active"
    : data.has_default_key
      ? "Trial exhausted"
      : "Gemini required";

  accessPill.classList.toggle("warning", !inTrial && data.has_default_key);
  accessPill.classList.toggle("danger", !data.has_default_key || remaining === 0);

  if (state.personalKey) {
    accessSummary.textContent = "Your personal Gemini API key is active. Trial limits are bypassed.";
  } else if (data.has_default_key) {
    accessSummary.textContent = remaining > 0
      ? `You have ${remaining} sponsored Gemini request${remaining === 1 ? "" : "s"} left.`
      : "You have used all 3 sponsored requests. Connect your Gemini API key to continue.";
  } else {
    accessSummary.textContent = "No active server key is configured. Connect your Gemini key to continue.";
  }
}

async function loadUsage() {
  try {
    const response = await fetch("/api/usage");
    if (!response.ok) throw new Error("Unable to load access status.");
    updateUsage(await response.json());
  } catch (error) {
    accessSummary.textContent = "The access system is unavailable right now. Please refresh and try again.";
    accessPill.textContent = "Unavailable";
    accessPill.classList.add("danger");
  }
}

function openKeyDialog() {
  modal.classList.remove("hidden");
  modalKeyInput.value = state.personalKey || "";
  modalKeyInput.focus();
}

function closeKeyDialog() {
  modal.classList.add("hidden");
  modalKeyInput.value = "";
}

async function savePersonalKey() {
  const key = (modalKeyInput.value || "").trim();
  if (!key) {
    setAgentStatus("Key required");
    addMessage("assistant", "Enter a Gemini API key before continuing.");
    return;
  }

  try {
    const response = await fetch("/api/validate-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Gemini key couldn't be validated.");

    state.personalKey = key;
    setAgentStatus("Upgrade ready");
    addMessage("assistant", "Your personal Gemini key is active. Trial limits are now bypassed.");
    closeKeyDialog();
    await loadUsage();
  } catch (error) {
    setAgentStatus("Invalid key");
    addMessage("assistant", error.message || "Gemini key couldn't be validated. Check the key and try again.");
  }
}

function clearStoredKey() {
  state.personalKey = "";
  modalKeyInput.value = "";
  setAgentStatus("Ready");
  addMessage("assistant", "Your personal Gemini key was cleared. The app will use the sponsored trial again.");
  loadUsage();
}

document.querySelectorAll(".agent").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelector(".agent.active")?.classList.remove("active");
    button.classList.add("active");
    state.agent = button.dataset.agent;
    document.querySelector("#agent-name").textContent = labels[state.agent];
    setAgentStatus("Ready");
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  const trialExhausted = !state.personalKey && state.usage && state.usage.has_default_key && Number(state.usage.remaining || 0) <= 0;
  if (trialExhausted) {
    addMessage("assistant", "You have used your 3 sponsored requests. Connect a Gemini API key to continue.");
    openKeyDialog();
    return;
  }

  addMessage("user", text);
  state.history.push({ role: "user", content: text });
  input.value = "";
  send.disabled = true;
  send.textContent = "Working…";
  setAgentStatus("Thinking");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent: state.agent,
        message: text,
        history: state.history,
        api_key: state.personalKey || null,
      }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = data.detail || "The agent could not complete that request.";
      throw new Error(detail);
    }

    addMessage("assistant", data.output);
    state.history.push({ role: "assistant", content: data.output });
    updateUsage({
      uses: data.uses ?? 0,
      limit: data.limit ?? 3,
      remaining: data.remaining ?? Math.max((data.limit ?? 3) - (data.uses ?? 0), 0),
      has_default_key: !state.personalKey,
    });
    setAgentStatus("Completed");
  } catch (error) {
    addMessage("assistant", error.message);
    setAgentStatus("Needs key");
    if (error.message.includes("Connect your Gemini API key") || error.message.includes("Gemini key couldn't be validated") || error.message.includes("Gemini connection required")) {
      openKeyDialog();
    }
  } finally {
    send.disabled = false;
    send.textContent = "Send";
    input.focus();
  }
});

document.querySelector("#connect-gemini").addEventListener("click", openKeyDialog);
document.querySelector("#key-trigger").addEventListener("click", openKeyDialog);
document.querySelector("#close-key-modal").addEventListener("click", closeKeyDialog);
document.querySelector("#validate-key").addEventListener("click", savePersonalKey);
document.querySelector("#clear-key").addEventListener("click", clearStoredKey);
toggleKeyVisibility.addEventListener("click", () => {
  const isHidden = modalKeyInput.type === "password";
  modalKeyInput.type = isHidden ? "text" : "password";
  toggleKeyVisibility.textContent = isHidden ? "Hide" : "Show";
});
document.querySelector("#portfolio-link").addEventListener("click", () => {
  window.location.href = "/";
});

modal.addEventListener("click", (event) => {
  if (event.target === modal) closeKeyDialog();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modal.classList.contains("hidden")) closeKeyDialog();
});

loadUsage();
setAgentStatus("Ready");
