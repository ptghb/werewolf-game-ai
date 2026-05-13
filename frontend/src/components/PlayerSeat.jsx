import React from "react";
export default function PlayerSeat({ player, isMe }) {
  const opacity = player.alive === false ? 0.35 : 1;
  return (
    <div style={{
      width: 90, height: 90, borderRadius: "50%",
      background: isMe ? "var(--accent)" : "var(--bg-soft)",
      color: isMe ? "#111" : "var(--fg)",
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      boxShadow: "var(--shadow)", opacity, textAlign: "center", fontSize: 13,
    }}>
      <div>{player.nickname}</div>
      <div style={{ fontSize: 10, opacity: 0.7 }}>
        {player.is_ai ? "AI" : "玩家"} · 座{player.seat + 1}
      </div>
    </div>
  );
}