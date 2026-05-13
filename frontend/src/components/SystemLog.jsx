import React from "react";
import useGameStore from "../store/gameStore.js";

export default function SystemLog() {
  const log = useGameStore((s) => s.systemLog);
  return (
    <div style={{ background: "var(--bg-soft)", padding: 8, borderRadius: 8,
                  maxHeight: 160, overflowY: "auto", fontSize: 13 }}>
      <strong>系统</strong>
      {log.map((line, i) => (
        <div key={i} style={{ color: "var(--muted)" }}>{line}</div>
      ))}
    </div>
  );
}