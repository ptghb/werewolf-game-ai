import React, { useEffect, useState } from "react";

const PHASE_LABELS = {
  lobby: "等待中", role_assign: "发牌中", night_start: "🌙 天黑请闭眼",
  wolf_kill: "🐺 狼人行动", seer_check: "🔮 预言家行动", witch_action: "🧪 女巫行动",
  day_announce: "☀️ 天亮公告", day_speech: "💬 白天发言", day_vote: "🗳️ 投票出局",
  hunter_shot: "🏹 猎人开枪", check_win: "⚖️ 判定胜负", game_over: "🏁 游戏结束",
};

export default function PhaseBanner({ phase, day, deadlineTs, winner }) {
  const [remaining, setRemaining] = useState(null);
  useEffect(() => {
    if (!deadlineTs) { setRemaining(null); return; }
    const iv = setInterval(() => {
      setRemaining(Math.max(0, Math.ceil(deadlineTs - Date.now() / 1000)));
    }, 500);
    return () => clearInterval(iv);
  }, [deadlineTs]);

  const isActive = phase !== "lobby" && phase !== "game_over";
  const phaseLabel = phase === "game_over" && winner
    ? (winner === "good" ? "🏆 好人阵营胜利" : "🐺 狼人阵营胜利")
    : (PHASE_LABELS[phase] || phase);

  return (
    <div className="card" style={{
      display: "flex", alignItems: "center", gap: 12,
      padding: "10px 14px",
      background: isActive ? "linear-gradient(135deg, var(--bg-card), rgba(124, 92, 252, 0.08))" : "var(--bg-card)",
      borderLeft: isActive ? "3px solid var(--accent)" : "3px solid var(--border)",
      flex: "1 1 auto",
      minWidth: 360,
    }}>
      {isActive && (
        <div style={{
          width: 6, height: 6, borderRadius: "50%",
          background: "var(--accent)",
          boxShadow: "0 0 8px var(--accent-glow)",
          flexShrink: 0,
          animation: "pulse-glow 2s ease-in-out infinite",
        }} />
      )}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 600 }}>
          {day > 0 && <span style={{ color: "var(--fg-muted)", fontWeight: 400 }}>第{day}天 · </span>}
          {phaseLabel}
        </div>
      </div>
      {remaining != null && (
        <div style={{
          fontSize: 12, fontWeight: 700, color: "var(--accent)",
          fontVariantNumeric: "tabular-nums",
          minWidth: 40, textAlign: "right",
        }}>
          {remaining}s
        </div>
      )}
    </div>
  );
}