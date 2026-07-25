import api from "./api";

export async function sendMessage(message, conversationId = null, language = "en") {
  const payload = { message, language };
  if (conversationId) payload.conversation_id = conversationId;
  // Read demo mode flag from localStorage (set by DemoModeContext)
  try {
    const isDemo = localStorage.getItem("crimeai_demo_mode") === "true";
    if (isDemo) payload.demo_mode = true;
  } catch {
    // localStorage unavailable — ignore
  }
  const r = await api.post("/chat/message", payload);
  return r.data;
}

export async function listConversations(limit = 50, offset = 0) {
  const r = await api.get("/chat/conversations", { params: { limit, offset } });
  return r.data;
}

export async function getConversation(conversationId) {
  const r = await api.get(`/chat/conversations/${conversationId}`);
  return r.data;
}

export async function deleteConversation(conversationId) {
  const r = await api.delete(`/chat/conversations/${conversationId}`);
  return r.data;
}

export async function uploadFile(file, conversationId = 0, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("conversation_id", String(conversationId || 0));
  const r = await api.post("/chat/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: onProgress,
  });
  return r.data;
}

export async function sendFeedback(conversationId, messageId, rating, comment = "") {
  const r = await api.post("/chat/feedback", { conversation_id: conversationId, message_id: messageId, rating, comment });
  return r.data;
}

export async function searchConversations(query) {
  const r = await api.get("/chat/conversations/search", { params: { q: query } });
  return r.data;
}

export function exportConversationAsMarkdown(messages) {
  let md = "# CrimeAI Conversation\n\n";
  messages.forEach((m) => {
    const role = m.role === "user" ? "**Officer**" : "**CrimeAI**";
    md += `### ${role}\n${m.text}\n\n`;
  });
  const blob = new Blob([md], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `crimeai-chat-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

export function exportConversationAsText(messages) {
  let txt = "CrimeAI Conversation\n====================\n\n";
  messages.forEach((m) => {
    const role = m.role === "user" ? "Officer" : "CrimeAI";
    txt += `${role}:\n${m.text}\n\n`;
  });
  const blob = new Blob([txt], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `crimeai-chat-${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function exportPdf(conversationId) {
  const r = await api.get(`/chat/${conversationId}/export-pdf`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(r.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `crimeai-conversation-${conversationId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}

// ── Speech-to-Text ─────────────────────────────────────────────

export async function speechToText(audioBlob, language = "en") {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.webm");
  formData.append("language", language);
  const r = await api.post("/chat/speech-to-text", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 60000, // STT can take longer
  });
  return r.data;
}

// ── Text-to-Speech ─────────────────────────────────────────────

export async function textToSpeech(text, language = "en") {
  const r = await api.post(
    "/chat/text-to-speech",
    null,
    {
      params: { text, language },
      responseType: "blob",
      timeout: 30000,
    },
  );
  return r.data;
}
