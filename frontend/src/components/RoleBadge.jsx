import React from "react";
import useGameStore from "../store/gameStore.js";

const ROLE_LABELS = { werewolf: "狼人", witch: "女巫", seer: "预言家", villager: "平民" };

export default function RoleBadge() {
  const { myRole, wolfTeammates } = useGameStore();
  if (!myRole) return null;
  return (
    <div style={{ padding: 8, background: "var(--bg-soft)", borderRadius: 8, marginBottom: 12 }}>
      <strong>我的身份：</strong>{ROLE_LABELS[myRole]}
      {wolfTeammates?.length > 0 && (
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          狼队友：{wolfTeammates.join(", ")}
        </div>
      )}
    </div>
  );
}