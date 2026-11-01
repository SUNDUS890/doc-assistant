let sessionId = null;

const fileInput = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const statusEl = document.getElementById("status");
const chatEl = document.getElementById("chat");
const questionEl = document.getElementById("question");
const askBtn = document.getElementById("ask-btn");

function setStatus(text, type) {
  statusEl.textContent = text;
  statusEl.className = "status " + (type || "");
}

function addMessage(text, role) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function addSources(messageEl, sources) {
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Sources";
  details.appendChild(summary);
  sources.forEach(function (s) {
    const box = document.createElement("div");
    box.className = "source";
    const title = document.createElement("strong");
    title.textContent = "Page " + s.page;
    const body = document.createElement("div");
    body.textContent = s.text;
    box.appendChild(title);
    box.appendChild(body);
    details.appendChild(box);
  });
  messageEl.appendChild(details);
}

uploadBtn.addEventListener("click", async function () {
  const file = fileInput.files[0];
  if (!file) {
    setStatus("Please choose a PDF first.", "error");
    return;
  }
  setStatus("Reading and indexing your document...", "");
  uploadBtn.disabled = true;
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await response.json();
    if (!response.ok) {
      setStatus(data.detail || "Upload failed.", "error");
    } else {
      sessionId = data.session_id;
      setStatus("Indexed " + data.chunks + " chunks from " + data.filename + ".", "ok");
      questionEl.disabled = false;
      askBtn.disabled = false;
      chatEl.innerHTML = "";
    }
  } catch (err) {
    setStatus("Could not reach the server.", "error");
  }
  uploadBtn.disabled = false;
});

async function ask() {
  const question = questionEl.value.trim();
  if (!question || !sessionId) {
    return;
  }
  addMessage(question, "user");
  questionEl.value = "";
  askBtn.disabled = true;
  const thinking = addMessage("Thinking...", "bot");
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, question: question })
    });
    const data = await response.json();
    if (!response.ok) {
      thinking.textContent = data.detail || "Something went wrong.";
    } else {
      thinking.textContent = data.answer;
      addSources(thinking, data.sources);
    }
  } catch (err) {
    thinking.textContent = "Could not reach the server.";
  }
  askBtn.disabled = false;
}

askBtn.addEventListener("click", ask);
questionEl.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    ask();
  }
});