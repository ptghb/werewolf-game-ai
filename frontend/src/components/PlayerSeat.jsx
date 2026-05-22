import React from "react";

const ROLE_ICONS = { werewolf: "🐺", witch: "🧪", seer: "🔮", villager: "👤", hunter: "🏹", idiot: "🗿" };

export default function PlayerSeat({ player, isMe }) {
  const alive = player.alive !== false;
  const isAI = player.is_ai;

  return (
    <div style={{
      position: "relative",
      animation: "fade-in 300ms ease-out",
      opacity: alive ? 1 : 0.3,
      transition: "opacity 0.4s ease",
    }}>
      {/* 座位圆圈 */}
      <div style={{
        width: 80, height: 80, borderRadius: "50%",
        background: isMe
          ? "linear-gradient(135deg, var(--accent), #9278ff)"
          : "var(--bg-card)",
        border: isMe
          ? "2px solid var(--accent)"
          : "1px solid var(--border)",
        boxShadow: isMe
          ? "0 0 20px var(--accent-glow)"
          : alive ? "var(--shadow-sm)" : "none",
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        transition: "all 250ms ease-out",
        position: "relative",
      }}>
        {/* 头像 */}
        <div style={{
          fontSize: isAI ? 18 : 20,
          fontWeight: isAI ? 400 : 700,
          color: isMe ? "white" : "var(--fg-primary)",
          lineHeight: 1,
        }}>
          {isAI ? "🤖" : player.nickname?.[0] || "?"}
        </div>

        {/* 存活标记 */}
        {!alive && (
          <div style={{
            position: "absolute", inset: 0,
            borderRadius: "50%",
            background: "rgba(0,0,0,0.5)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <span style={{ fontSize: 24 }}>💀</span>
          </div>
        )}
      </div>

      {/* 昵称 */}
      <div style={{
        textAlign: "center", marginTop: 6,
        fontSize: 11, fontWeight: isMe ? 700 : 500,
        color: isMe ? "var(--accent)" : "var(--fg-secondary)",
        maxWidth: 80, overflow: "hidden", textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}>
        {isMe ? "你" : player.nickname}
      </div>

      {/* AI 标签 */}
      {isAI && alive && (
        <div style={{
          position: "absolute", top: -4, right: -4,
          background: "var(--bg-elevated)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-full)",
          padding: "1px 6px",
          fontSize: 9,
          color: "var(--fg-muted)",
          fontWeight: 600,
        }}>
          AI
        </div>
      )}
    </div>
  );
}