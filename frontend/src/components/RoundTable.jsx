import React from "react";
import PlayerSeat from "./PlayerSeat.jsx";

export default function RoundTable({ players, myId }) {
  const radius = 180;
  const cx = 240, cy = 240;
  return (
    <div style={{ position: "relative", width: 480, height: 480, margin: "0 auto" }}>
      <div style={{
        position: "absolute", left: cx - 120, top: cy - 120,
        width: 240, height: 240, borderRadius: "50%",
        background: "radial-gradient(circle, #1c2230 0%, #0b0d14 100%)",
        boxShadow: "var(--shadow)",
      }} />
      {players.map((p, i) => {
        const angle = (i / players.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + radius * Math.cos(angle) - 45;
        const y = cy + radius * Math.sin(angle) - 45;
        return (
          <div key={p.id} style={{ position: "absolute", left: x, top: y }}>
            <PlayerSeat player={p} isMe={p.id === myId} />
          </div>
        );
      })}
    </div>
  );
}