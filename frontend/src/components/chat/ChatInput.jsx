import { useRef, useEffect } from "react";
import { T } from "../../styles/theme";

export default function ChatInput({ value, onChange, onSend, onFileSelect, loading, uploadProgress, language = "en", onLanguageChange, placeholder = "Ask CrimeAI...", onVoiceRecord, isRecording, }) {
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); onSend(); }
  };

  return (
    <div style={{ padding: "14px 16px", borderTop: `1px solid ${T.cardBorder}`, background: T.card, borderRadius: "0 0 16px 16px", flexShrink: 0 }}>
      {/* ── Language Selector ── */}
      <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 8 }}>
        <button
          onClick={() => onLanguageChange?.("en")}
          title="English"
          style={{
            padding: "4px 12px",
            borderRadius: 6,
            background: language === "en" ? `linear-gradient(135deg, ${T.accent}, ${T.purple})` : T.inputBg,
            border: `1px solid ${language === "en" ? "transparent" : T.inputBorder}`,
            color: language === "en" ? "#fff" : T.textSecondary,
            fontSize: 11,
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.15s",
            lineHeight: 1.4,
          }}
        >
          🇬🇧 English
        </button>
        <button
          onClick={() => onLanguageChange?.("kn")}
          title="Kannada"
          style={{
            padding: "4px 12px",
            borderRadius: 6,
            background: language === "kn" ? `linear-gradient(135deg, ${T.accent}, ${T.purple})` : T.inputBg,
            border: `1px solid ${language === "kn" ? "transparent" : T.inputBorder}`,
            color: language === "kn" ? "#fff" : T.textSecondary,
            fontSize: 11,
            fontWeight: 600,
            cursor: "pointer",
            transition: "all 0.15s",
            lineHeight: 1.4,
          }}
        >
          🇮🇳 ಕನ್ನಡ
        </button>
        {language === "kn" && (
          <span style={{ color: T.textMuted, fontSize: 9, marginLeft: 4 }}>
            ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ
          </span>
        )}
      </div>

      {uploadProgress !== null && (
        <div style={{ marginBottom: 8, padding: "8px 12px", background: T.inputBg, borderRadius: 8, display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 16 }}>📤</span>
          <div style={{ flex: 1 }}>
            <div style={{ height: 4, background: T.cardBorder, borderRadius: 2, overflow: "hidden" }}>
              <div style={{ width: `${uploadProgress}%`, height: "100%", background: `linear-gradient(90deg, ${T.accent}, ${T.purple})`, borderRadius: 2, transition: "width 0.3s ease" }} />
            </div>
          </div>
          <span style={{ color: T.textMuted, fontSize: 11 }}>{uploadProgress}%</span>
        </div>
      )}
      <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
        <button onClick={() => fileInputRef.current?.click()} disabled={loading} title="Attach file"
          style={{ padding: "10px 10px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textMuted, cursor: loading ? "not-allowed" : "pointer", fontSize: 16, lineHeight: 1, transition: "all 0.15s", flexShrink: 0 }}
          onMouseEnter={(e) => { if (!loading) e.currentTarget.style.borderColor = T.accent + "44"; }}
          onMouseLeave={(e) => { if (!loading) e.currentTarget.style.borderColor = T.inputBorder; }}>
          📎
        </button>
        <input ref={fileInputRef} type="file" onChange={(e) => { if (e.target.files[0]) onFileSelect?.(e.target.files); e.target.value = ""; }} accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.csv" style={{ display: "none" }} />

        {/* Microphone Button */}
        <button
          onClick={() => onVoiceRecord?.()}
          disabled={loading}
          title={isRecording ? "Stop recording" : "Record voice"}
          style={{
            padding: "10px 10px",
            background: isRecording ? "rgba(239,68,68,0.15)" : T.inputBg,
            border: `1px solid ${isRecording ? "rgba(239,68,68,0.4)" : T.inputBorder}`,
            borderRadius: 10,
            color: isRecording ? "#EF4444" : T.textMuted,
            cursor: loading ? "not-allowed" : "pointer",
            fontSize: 16,
            lineHeight: 1,
            transition: "all 0.15s",
            flexShrink: 0,
            animation: isRecording ? "pulse 1s ease-in-out infinite" : "none",
          }}
        >
          {isRecording ? "⏹" : "🎤"}
        </button>
        <div style={{ flex: 1, display: "flex", flexDirection: "column", position: "relative" }}>
          <textarea ref={textareaRef} value={value} onChange={(e) => onChange(e.target.value)} onKeyDown={handleKeyDown} disabled={loading} placeholder={placeholder} rows={1}
            style={{ width: "100%", padding: "10px 14px", background: T.inputBg, border: `1px solid ${T.inputBorder}`, borderRadius: 10, color: T.textPrimary, fontSize: 13, outline: "none", resize: "none", fontFamily: "inherit", lineHeight: 1.5, boxSizing: "border-box", minHeight: 42, maxHeight: 120 }} />
          {!value && !loading && (
            <div style={{ position: "absolute", bottom: -18, left: 4, display: "flex", gap: 12, color: T.textMuted, fontSize: 9 }}>
              <span>Enter Send</span>
              <span>Shift+Enter New line</span>
            </div>
          )}
        </div>
        <button onClick={() => onSend()} disabled={loading || !value.trim()} title="Send message"
          style={{ padding: "10px 18px", borderRadius: 10, background: loading || !value.trim() ? T.accentHover : `linear-gradient(135deg, ${T.accent}, ${T.purple})`, color: "#fff", border: "none", fontSize: 13, fontWeight: 600, cursor: loading || !value.trim() ? "not-allowed" : "pointer", opacity: loading || !value.trim() ? 0.5 : 1, transition: "all 0.15s", display: "flex", alignItems: "center", gap: 4, flexShrink: 0, lineHeight: 1 }}
          onMouseEnter={(e) => { if (!loading && value.trim()) { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = `0 4px 12px ${T.accent}44`; } }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}>
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}
