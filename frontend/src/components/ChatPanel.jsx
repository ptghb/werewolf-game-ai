import React, { useState, useEffect, useRef } from "react";
import useGameStore from "../store/gameStore.js";

const SPEECH_PHASES = new Set(["speech", "last_words"]);

export default function ChatPanel() {
  const { messageLog, sendChat, promptAction } = useGameStore();
  const speaking = promptAction && SPEECH_PHASES.has(promptAction.action);
  const [text, setText] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messageLog.length]);

  const handleSend = () => {
    if (text.trim()) {
      sendChat("day", text.trim());
      setText("");
      inputRef.current?.focus();
    }
  };

  return (
    <div className="card" style={{
      display: "flex", flexDirection: "column", height: "100%", padding: 0, overflow: "hidden",
    }}>
      {/* 标题 */}
      <div style={{
        padding: "10px 12px 8px",
        borderBottom: "1px solid var(--border)",
        fontSize: 11, fontWeight: 600, color: "var(--fg-muted)",
      }}>
        消息
      </div>

      {/* 消息列表 */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "8px 10px",
        display: "flex", flexDirection: "column", gap: 4,
      }}>
        {messageLog.length === 0 && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: "100%",
            color: "var(--fg-muted)", fontSize: 12, opacity: 0.5,
          }}>
            暂无消息
          </div>
        )}
        {messageLog.map((m, i) => (
          m.type === "system" ? (
            <div key={i} style={{
              fontSize: 12, lineHeight: 1.5,
              color: "var(--fg-muted)",
              padding: "4px 8px",
              borderLeft: "2px solid var(--border)",
              background: "var(--surface)",
              borderRadius: "var(--radius-sm)",
            }}>
              📢 {m.text}
            </div>
          ) : (
            <div key={i} style={{
              fontSize: 12, lineHeight: 1.5,
              opacity: m.last_words ? 0.6 : 1,
              padding: "4px 6px",
              borderRadius: "var(--radius-sm)",
              background: m.last_words ? "var(--surface)" : "transparent",
            }}>
              <span style={{ fontWeight: 600, color: "var(--accent)" }}>
                {m.from_name || m.from}
              </span>
              <span style={{ color: "var(--fg-secondary)", marginLeft: 4 }}>
                {m.text}
              </span>
              {m.last_words && (
                <span style={{ color: "var(--danger)", fontSize: 10, marginLeft: 4 }}>
                  [遗言]
                </span>
              )}
            </div>
          )
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 发送区 */}
      <div style={{
        display: "flex", gap: 6, padding: "8px 10px",
        borderTop: "1px solid var(--border)",
        background: "var(--surface)",
      }}>
        <input
          ref={inputRef}
          style={{
            flex: 1, padding: "8px 10px", fontSize: 12,
            opacity: speaking ? 0.4 : 1,
          }}
          placeholder={speaking ? "请在上方弹窗中发言..." : "输入消息..."}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
          maxLength={80}
          disabled={speaking}
        />
        <button
          className="btn-primary btn-sm"
          onClick={handleSend}
          disabled={!text.trim() || speaking}
          style={{ whiteSpace: "nowrap", opacity: speaking ? 0.4 : 1 }}
        >
          发送
        </button>
      </div>
    </div>
  );
}