import React, { useEffect, useState } from "react";

const PHASE_LABELS = {
  lobby: "等待开始", role_assign: "发牌", night_start: "天黑请闭眼",
  wolf_kill: "狼人行动", seer_check: "预言家行动", witch_action: "女巫行动",
  day_announce: "天亮公告", day_speech: "白天发言", day_vote: "白天投票",
  check_win: "判定胜负", game_over: "游戏结束",
};

export default function PhaseBanner({ phase, day, deadlineTs }) {
  const [remaining, setRemaining] = useState(null);
  useEffect(() => {
    if (!deadlineTs) { setRemaining(null); return; }
    const iv = setInterval(() => {
      setRemaining(Math.max(0, Math.ceil(deadlineTs - Date.now() / 1000)));
    }, 500);
    return () => clearInterval(iv);
  }, [deadlineTs]);
  return (
    <div style={{ padding: 12, background: "var(--bg-soft)", borderRadius: 8, marginBottom: 12 }}>
      <strong>第 {day || 0} 天</strong> — {PHASE_LABELS[phase] || phase}
      {remaining != null && <span style={{ marginLeft: 12, color: "var(--muted)" }}>⏱ {remaining}s</span>}
    </div>
  );
}