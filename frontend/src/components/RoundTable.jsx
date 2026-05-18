import React from "react";
import PlayerSeat from "./PlayerSeat.jsx";

export default function RoundTable({ players, myId }) {
  const radius = 230;
  const cx = 290;
  const cy = 290;
  const size = 600;

  return (
    <div className="card" style={{
      position: "relative",
      width: "100%",
      maxWidth: "100%",
      height: size,
      margin: "0 auto",
      overflow: "hidden",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}>
      {/* 桌子 - 发光圆环 */}
      <div style={{
        position: "absolute",
        width: 200, height: 200,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(124,92,252,0.08) 0%, rgba(12,13,23,0.6) 60%, transparent 100%)",
        border: "1px solid var(--border)",
        boxShadow: "inset 0 0 60px rgba(124,92,252,0.06)",
        top: "50%", left: "50%",
        transform: "translate(-50%, -50%)",
        zIndex: 0,
      }} />

      {/* 中心文字 */}
      <div style={{
        position: "absolute",
        top: "50%", left: "50%",
        transform: "translate(-50%, -50%)",
        zIndex: 0,
        textAlign: "center",
        pointerEvents: "none",
      }}>
        <div style={{ fontSize: 18, opacity: 0.15, fontWeight: 700, letterSpacing: 2 }}>
          狼人杀
        </div>
      </div>

      {/* 座位 */}
      {players.map((p, i) => {
        const angle = (i / players.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + radius * Math.cos(angle) - 40;
        const y = cy + radius * Math.sin(angle) - 40;
        return (
          <div
            key={p.id}
            style={{
              position: "absolute",
              left: x, top: y,
              zIndex: 1,
              transition: "all 0.3s ease",
            }}
          >
            <PlayerSeat player={p} isMe={p.id === myId} />
          </div>
        );
      })}
    </div>
  );
}