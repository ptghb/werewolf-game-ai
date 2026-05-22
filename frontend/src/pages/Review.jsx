import React from "react";
import useGameStore from "../store/gameStore.js";
import { translateRole } from "../constants.js";

function renderLogEntry(m, i) {
  const displayText = m.text && m.text.replace(/=(\w+)/g, (_, role) => `=${translateRole(role)}`);
  if (m.type === "system") {
    return (
      <div key={i} style={{
        fontSize: 13, lineHeight: 1.5, padding: "6px 10px",
        color: "var(--fg-primary)",
        borderLeft: "2px solid var(--accent)",
        background: "rgba(124,92,252,0.06)",
        borderRadius: "var(--radius-sm)",
      }}>📢 {displayText}</div>
    );
  }
  return (
    <div key={i} style={{
      fontSize: 13, lineHeight: 1.5, padding: "6px 8px",
      borderRadius: "var(--radius-sm)",
      background: i % 2 === 0 ? "transparent" : "var(--surface)",
    }}>
      <span style={{ fontWeight: 600, color: "var(--accent)" }}>{m.from_name || m.from}</span>
      <span style={{ color: "var(--fg-primary)", marginLeft: 6 }}>{m.text}</span>
    </div>
  );
}

export default function Review() {
  const reviewRoom = useGameStore((s) => s.reviewRoom);
  const clearReview = useGameStore((s) => s.clearReview);

  if (!reviewRoom) return null;

  const { room_code, result, game_log } = reviewRoom;

  const pageStyle = {
    minHeight: "100vh",
    background: "radial-gradient(ellipse at 50% 30%, #14162e 0%, var(--bg-deep) 70%)",
    padding: 24,
    position: "relative",
    overflow: "auto",
  };

  const cardStyle = {
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-xl)",
    padding: "28px 24px",
    maxWidth: 640,
    margin: "0 auto",
    position: "relative",
    zIndex: 1,
  };

  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        {/* 头部 */}
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <div style={{ fontSize: 48, marginBottom: 8 }}>
            {result === "good" ? "🏆" : "🐺"}
          </div>
          <div style={{ fontSize: 22, fontWeight: 700 }}>
            {result === "good" ? "好人阵营胜利" : "狼人阵营胜利"}
          </div>
          <div style={{ color: "var(--fg-muted)", fontSize: 13, marginTop: 4 }}>
            房间 {room_code}
          </div>
        </div>

        {/* 聊天记录 */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>游戏记录</div>
          {game_log && game_log.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 400, overflowY: "auto" }}>
              {(game_log || []).map(renderLogEntry)}
            </div>
          ) : (
            <div style={{ color: "var(--fg-muted)", fontSize: 13, textAlign: "center", padding: 20 }}>
              暂无聊天记录
            </div>
          )}
        </div>

        {/* 返回按钮 */}
        <button
          className="btn-primary"
          onClick={clearReview}
          style={{ width: "100%", padding: "12px", fontSize: 15 }}
        >返回大厅</button>
      </div>
    </div>
  );
}