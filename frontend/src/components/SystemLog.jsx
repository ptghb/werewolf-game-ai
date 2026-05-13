import React, { useEffect, useRef } from "react";
import useGameStore from "../store/gameStore.js";

export default function SystemLog() {
  const log = useGameStore((s) => s.systemLog);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log.length]);

  return (
    <div className="card" style={{
      padding: "10px 12px",
      maxHeight: 140,
      overflowY: "auto",
      display: "flex",
      flexDirection: "column",
      gap: 3,
    }}>
      <div style={{ fontSize: 11, fontWeight: 600, color: "var(--fg-muted)", marginBottom: 2 }}>
        系统消息
      </div>
      {log.length === 0 ? (
        <div style={{ fontSize: 12, color: "var(--fg-muted)", opacity: 0.5 }}>
          暂无消息
        </div>
      ) : (
        log.map((line, i) => (
          <div key={i} style={{
            fontSize: 12,
            color: "var(--fg-secondary)",
            padding: "2px 0",
            borderBottom: i < log.length - 1 ? "1px solid var(--border)" : "none",
          }}>
            {line}
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}