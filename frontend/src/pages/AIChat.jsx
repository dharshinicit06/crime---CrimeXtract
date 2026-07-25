import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { T } from "../styles/theme";
import {
  sendMessage, listConversations, getConversation, deleteConversation,
  uploadFile, sendFeedback, searchConversations, exportPdf,
  speechToText,
} from "../services/chatService";
import PageShell from "../components/PageShell";
import ChatLayout from "../components/chat/ChatLayout";
import ChatHeader from "../components/chat/ChatHeader";
import ChatHistory from "../components/chat/ChatHistory";
import ChatMessage from "../components/chat/ChatMessage";
import ChatInput from "../components/chat/ChatInput";
import TypingIndicator from "../components/chat/TypingIndicator";
import PromptSuggestions from "../components/chat/PromptSuggestions";
import ToolPanel from "../components/chat/ToolPanel";

// ─── Global animations ───────────────────────────────────────
const ANIM_STYLES = `
  @keyframes msgIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  @keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); } 40% { transform: scale(1); } }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
  @keyframes recordingPulse { 0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 70% { box-shadow: 0 0 0 8px rgba(239,68,68,0); } 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); } }
`;

export default function AIChat({ user }) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [convsLoading, setConvsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showTools, setShowTools] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(null);
  const [searchQ, setSearchQ] = useState("");
  const [hasSentFirst, setHasSentFirst] = useState(false);
  const [currentCase, setCurrentCase] = useState(null);
  const [language, setLanguage] = useState("en");
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const messagesContainerRef = useRef(null);

  const firstName = user?.name?.split(" ")[0] || "Officer";
  const userInitial = user?.name?.[0] || "U";

  // ── Load conversations ───────────────────────────────────────
  const loadCons = useCallback(async () => {
    setConvsLoading(true);
    try {
      const d = await listConversations();
      if (d?.items) setConversations(d.items);
    } catch { /* ignore */ }
    setConvsLoading(false);
  }, []);

  useEffect(() => { loadCons(); }, [loadCons]);

  // ── Auto scroll ──────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // ── Load conversation ────────────────────────────────────────
  const loadConversation = useCallback(async (id) => {
    try {
      const d = await getConversation(id);
      setConversationId(String(d.id));
      const msgs = (d.messages || []).map((m) => ({
        role: m.role,
        text: m.message,
        time: new Date(m.created_at),
      }));
      setMessages(msgs);
      setHasSentFirst(msgs.length > 0);
    } catch { /* ignore */ }
  }, []);

  // ── Delete conversation ──────────────────────────────────────
  const handleDelete = useCallback(async (id) => {
    if (!window.confirm("Delete this investigation?")) return;
    await deleteConversation(id).catch(() => {});
    loadCons();
    if (String(id) === conversationId) {
      setConversationId(null);
      setMessages([]);
      setHasSentFirst(false);
    }
  }, [conversationId, loadCons]);

  // ── Rename conversation ──────────────────────────────────────
  const handleRename = useCallback(async (id, title) => {
    // Update locally; backend rename can be added later
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, title } : c))
    );
  }, []);

  // ── Send message ─────────────────────────────────────────────
  const handleSend = useCallback(async (text) => {
    const msg = text || input;
    if (!msg.trim() || loading) return;

    const userMsg = { role: "user", text: msg, time: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setHasSentFirst(true);

    try {
      const d = await sendMessage(msg, conversationId, language);
      if (d.conversation_id) setConversationId(d.conversation_id);

      // Check if intent is CRIME_PREDICTION for dashboard integration
      const openDashboardIntent = d.intent === "CRIME_PREDICTION";

      const aiMsg = {
        role: "assistant",
        text: d.response,
        time: new Date(d.timestamp || Date.now()),
        followUps: d.follow_ups,
        messageId: d.message_id,
        showPredictionDashboard: openDashboardIntent,
        explanation: d.explanation || null,
        timeline: d.timeline || [],
        recommendations: d.recommendations || [],
        confidence: d.data?.confidence,
      };

      // Auto-play TTS if enabled
      if (ttsEnabled && aiMsg.text) {
        setTimeout(() => speakResponse(aiMsg.text), 500);
      }
      setMessages((prev) => [...prev, aiMsg]);
      loadCons();
    } catch (err) {
      const status = err?.response?.status;
      let errorText = "⚠️ An error occurred. ";
      if (status === 401) errorText += "Session expired. Please refresh.";
      else if (status === 429) errorText += "Too many requests. Please wait.";
      else if (status === 503) errorText += "AI service temporarily unavailable.";
      else errorText += err?.response?.data?.detail || err?.message || "";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: errorText, time: new Date() },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, conversationId, loadCons, language]);

  // ── TTS Playback ────────────────────────────────────────────
  const speakResponse = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === "kn" ? "kn-IN" : "en-US";
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    const voices = window.speechSynthesis.getVoices();
    const langVoice = voices.find((v) => v.lang.startsWith(language));
    if (langVoice) utterance.voice = langVoice;
    window.speechSynthesis.speak(utterance);
  }, [language]);

  // ── Voice Recording ─────────────────────────────────────────
  const handleVoiceRecord = useCallback(async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
          ? "audio/webm;codecs=opus"
          : "audio/webm",
      });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());

        if (audioChunksRef.current.length === 0) return;

        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setIsTranscribing(true);

        try {
          const result = await speechToText(audioBlob, language);
          if (result.text) {
            setInput(result.text);
            setTimeout(() => handleSend(result.text), 300);
          }
        } catch (err) {
          console.error("STT failed:", err);
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "⚠️ Microphone access denied. Please allow microphone permissions in your browser settings.",
          time: new Date(),
        },
      ]);
    }
  }, [isRecording, language, handleSend, setInput]);

  // ── Regenerate last response ─────────────────────────────────
  const handleRegenerate = useCallback(() => {
    setMessages((prev) => prev.slice(0, -1));
    const lastUserMsg = [...messages].reverse().find((m) => m.role === "user");
    if (lastUserMsg) handleSend(lastUserMsg.text);
  }, [messages, handleSend]);

  // ── Upload file ──────────────────────────────────────────────
  const handleUpload = useCallback(async (files) => {
    const f = files?.[0];
    if (!f || loading) return;
    const allowed = [
      "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "text/plain", "image/png", "image/jpeg", "text/csv",
    ];
    if (!allowed.includes(f.type)) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `⚠️ Unsupported file type: ${f.type}`, time: new Date() },
      ]);
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ File exceeds 20MB limit.", time: new Date() },
      ]);
      return;
    }
    setUploadProgress(0);
    try {
      const d = await uploadFile(f, conversationId ? Number(conversationId) : 0, (e) => {
        if (e.total) setUploadProgress(Math.round((e.loaded / e.total) * 100));
      });
      setUploadProgress(null);
      if (d.conversation_id) setConversationId(String(d.conversation_id));
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `**${d.filename}** uploaded successfully. Ask questions about this document.`,
          time: new Date(),
          attachment: { name: d.filename, mime: d.mime_type, size: d.file_size },
        },
      ]);
    } catch (err) {
      setUploadProgress(null);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `⚠️ Upload failed: ${err?.response?.data?.detail || err?.message}`,
          time: new Date(),
        },
      ]);
    }
  }, [loading, conversationId]);

  // ── Send feedback ────────────────────────────────────────────
  const handleFeedback = useCallback(
    async (rating, messageId) => {
      if (!conversationId) return;
      try {
        await sendFeedback(Number(conversationId), messageId || 0, rating);
      } catch { /* ignore */ }
    },
    [conversationId]
  );

  // ── Tool selection ───────────────────────────────────────────
  const handleToolSelect = useCallback((tool) => {
    const prompts = {
      summarize: "Summarize the current case with key details and findings.",
      timeline: "Generate a chronological timeline of events for this case.",
      profile: "Generate a criminal profile based on available evidence and patterns.",
      similar: "Find FIRs similar to the current case with matching modus operandi.",
      evidence: "Correlate evidence items across all linked FIRs and suspects.",
      network: "Analyze criminal network connections and relationships.",
      heatmap: "Show crime heatmap for the current district and time period.",
      predict: "Predict next likely crime locations and times based on patterns.",
      export: "Export a comprehensive investigation report in PDF format.",
    };
    const prompt = prompts[tool.action];
    if (prompt) {
      setInput(prompt);
      setTimeout(() => handleSend(prompt), 100);
    }
  }, [handleSend]);

  // ── Export conversation ──────────────────────────────────────
  const handleExport = useCallback(
    (format, msgs) => {
      if (format === "md") {
        let md = "# CrimeAI Investigation Report\n\n";
        msgs.forEach((m) => {
          md += `### ${m.role === "user" ? "Officer" : "CrimeAI"}\n${m.text}\n\n`;
        });
        const blob = new Blob([md], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `crimeai-report-${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
      } else if (format === "txt") {
        let txt = "CrimeAI Investigation Report\n============================\n\n";
        msgs.forEach((m) => {
          txt += `${m.role === "user" ? "Officer" : "CrimeAI"}:\n${m.text}\n\n`;
        });
        const blob = new Blob([txt], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `crimeai-report-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
      }
    },
    []
  );

  // ── New chat ─────────────────────────────────────────────────
  const clearChat = () => {
    setConversationId(null);
    setMessages([]);
    setHasSentFirst(false);
    setCurrentCase(null);
  };

  // ── Prompt suggestion clicked ────────────────────────────────
  const handlePromptSelect = (text) => {
    setInput(text);
    // Auto-send after a short delay
    setTimeout(() => handleSend(text), 100);
  };

  // ── Render ───────────────────────────────────────────────────
  return (
    <PageShell title="AI Investigation Assistant" user={user}>
      <style>{ANIM_STYLES}</style>

      <ChatLayout
        showSidebar={showSidebar}
        showTools={showTools}
        sidebar={
          <ChatHistory
            conversations={conversations}
            activeId={conversationId}
            onSelect={loadConversation}
            onDelete={handleDelete}
            onRename={handleRename}
            onNew={clearChat}
            searchQuery={searchQ}
            onSearchChange={setSearchQ}
            loading={convsLoading}
          />
        }
        main={
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              background: T.card,
              border: `1px solid ${T.cardBorder}`,
              borderRadius: 16,
              overflow: "hidden",
            }}
          >
            {/* Header */}
            <ChatHeader
              user={user}
              onToggleSidebar={() => setShowSidebar(!showSidebar)}
              onToggleTools={() => setShowTools(!showTools)}
              showSidebar={showSidebar}
              showTools={showTools}
              currentCase={currentCase}
              onExportPdf={conversationId ? () => exportPdf(conversationId) : null}
              hasMessages={messages.length > 0}
            />

            {/* Messages Area */}
            <div
              ref={messagesContainerRef}
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "16px 20px",
                display: "flex",
                flexDirection: "column",
                gap: 12,
              }}
            >
              {!hasSentFirst ? (
                <PromptSuggestions
                  onSelect={handlePromptSelect}
                  visible={!hasSentFirst}
                />
              ) : (
                messages.map((m, i) => (
                  <ChatMessage
                    key={m._id || i}
                    message={m}
                    userInitial={userInitial}
                    // ChatMessage handles clipboard write internally
                    onRegenerate={handleRegenerate}
                    onFeedback={handleFeedback}
                  />
                ))
              )}

              {/* Typing Indicator */}
              <TypingIndicator loading={loading} />

              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={() => handleSend()}
              onFileSelect={handleUpload}
              loading={loading}
              uploadProgress={uploadProgress}
              language={language}
              onLanguageChange={setLanguage}
              onVoiceRecord={handleVoiceRecord}
              isRecording={isRecording}
              placeholder={language === "kn" ? "CrimeAI ನಲ್ಲಿ ಪ್ರಕರಣಗಳು, ಸಾಕ್ಷ್ಯಗಳು, ಶಂಕಿತರ ಬಗ್ಗೆ ಕೇಳಿ..." : "Ask CrimeAI about cases, evidence, suspects..."}
            />
          </div>
        }
        tools={
          <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%", overflow: "hidden", flex: 1 }}>
            {/* TTS Toggle */}
            <div style={{
              padding: "12px 14px",
              background: `${T.cardBorder}30`,
              borderRadius: 12,
              border: `1px solid ${T.cardBorder}`,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 16 }}>🔊</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: T.textPrimary, fontSize: 12, fontWeight: 600 }}>Voice Output</div>
                  <div style={{ color: T.textMuted, fontSize: 10 }}>Play responses aloud</div>
                </div>
                <button
                  onClick={() => setTtsEnabled(!ttsEnabled)}
                  style={{
                    width: 36, height: 22, borderRadius: 11, border: "none", cursor: "pointer",
                    background: ttsEnabled ? T.accent : T.inputBorder,
                    position: "relative", transition: "background 0.2s", flexShrink: 0,
                  }}
                >
                  <div style={{
                    width: 18, height: 18, borderRadius: "50%", background: "#fff",
                    position: "absolute", top: 2,
                    left: ttsEnabled ? 16 : 2, transition: "left 0.2s",
                    boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
                  }} />
                </button>
              </div>
              {isTranscribing && (
                <div style={{ color: T.textMuted, fontSize: 11, marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: "50%", background: T.accent,
                    animation: "pulse 1s ease-in-out infinite",
                  }} />
                  Transcribing audio...
                </div>
              )}
            </div>

            <ToolPanel
              onToolSelect={handleToolSelect}
              currentCase={currentCase}
            />
          </div>
        }
      />
    </PageShell>
  );
}
