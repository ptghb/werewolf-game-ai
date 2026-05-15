import React, { useState, useEffect, useRef } from "react";
import useGameStore from "../store/gameStore.js";

export default function ChatPanel() {
  const { chat, sendChat, myRole } = useGameStore();
  const [tab, setTab] = useState("day");
  const [text, setText] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const tabs = ["day"];
  if (myRole === "werewolf") tabs.push("wolf");
  tabs.push("dead");

  const filtered = chat.filter((m) => m.channel === tab);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [filtered.length]);

  const TAB_LABELS = { day: "💬 白天", wolf: "🐺 狼队", dead: "💀 亡灵" };

  const handleSend = () => {
    if (text.trim()) {
      sendChat(tab, text.trim());
      setText("");
      inputRef.current?.focus();
    }
  };

  return (
    <div className="card" style={{
      display: "flex", flexDirection: "column", height: 380, padding: 0, overflow: "hidden",
    }}>
      {/* Tab 切换 */}
      <div style={{
        display: "flex", gap: 0, padding: "8px 8px 0",
        borderBottom: "1px solid var(--border)",
      }}>
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              flex: 1,
              background: "transparent",
              color: tab === t ? "var(--fg-primary)" : "var(--fg-muted)",
              padding: "6px 8px",
              fontSize: 11,
              fontWeight: tab === t ? 600 : 400,
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              borderRadius: 0,
            }}
          >{TAB_LABELS[t] || t}</button>
        ))}
      </div>

      {/* 消息列表 */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "8px 10px",
        display: "flex", flexDirection: "column", gap: 4,
      }}>
        {filtered.length === 0 && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: "100%",
            color: "var(--fg-muted)", fontSize: 12, opacity: 0.5,
          }}>
            暂无消息
          </div>
        )}
        {filtered.map((m, i) => (
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
          style={{ flex: 1, padding: "8px 10px", fontSize: 12 }}
          placeholder="输入消息..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
          maxLength={80}
        />
        <button
          className="btn-primary btn-sm"
          onClick={handleSend}
          disabled={!text.trim()}
          style={{ whiteSpace: "nowrap" }}
        >
          发送
        </button>
      </div>
    </div>
  );
}