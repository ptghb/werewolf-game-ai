import React, { useState } from "react";
import useGameStore from "../store/gameStore.js";

export default function ChatPanel() {
  const { chat, sendChat, myRole } = useGameStore();
  const [tab, setTab] = useState("day");
  const [text, setText] = useState("");
  const tabs = ["day"];
  if (myRole === "werewolf") tabs.push("wolf");
  tabs.push("dead");
  const filtered = chat.filter((m) => m.channel === tab);
  return (
    <div style={{ background: "var(--bg-soft)", padding: 12, borderRadius: 8 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{ background: tab === t ? "var(--accent)" : "transparent",
                     color: tab === t ? "#111" : "var(--fg)", border: "1px solid var(--muted)" }}>
            {t === "day" ? "白天" : t === "wolf" ? "狼频道" : "死亡"}
          </button>
        ))}
      </div>
      <div style={{ height: 260, overflowY: "auto", fontSize: 14 }}>
        {filtered.map((m, i) => (
          <div key={i} style={{ marginBottom: 4, opacity: m.last_words ? 0.8 : 1 }}>
            <strong>{m.from}</strong>: {m.text}
            {m.last_words && <span style={{ color: "var(--danger)" }}> [遗言]</span>}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input style={{ flex: 1 }} value={text} onChange={(e) => setText(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter" && text) { sendChat(tab, text); setText(""); } }} />
        <button onClick={() => { if (text) { sendChat(tab, text); setText(""); } }}>发送</button>
      </div>
    </div>
  );
}