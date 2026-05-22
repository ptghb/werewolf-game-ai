import React from "react";
import useGameStore from "../store/gameStore.js";
import { ROLE_LABEL } from "../constants.js";
const ROLE_COLORS = {
  werewolf: "var(--wolf)",
  witch: "var(--accent)",
  seer: "var(--gold)",
  villager: "var(--good)",
  hunter: "var(--danger)",
  idiot: "var(--good)",
};

export default function RoleBadge() {
  const { myRole, wolfTeammates, players } = useGameStore();
  if (!myRole) return null;

  const playerNameById = new Map(players.map((p) => [p.id, p.nickname]));
  const teammateNames = wolfTeammates.map((id) => playerNameById.get(id) || id);

  return (
    <div className="card" style={{
      display: "flex", alignItems: "center", gap: 12,
      padding: "10px 14px",
      borderLeft: `3px solid ${ROLE_COLORS[myRole] || "var(--fg-muted)"}`,
      flex: "1 1 auto",
      minWidth: 180,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: "var(--radius-md)",
        background: ROLE_COLORS[myRole] || "var(--surface)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 16, fontWeight: 700, color: "white",
        flexShrink: 0,
      }}>
        {myRole === "werewolf" ? "狼" : myRole === "witch" ? "巫" : myRole === "seer" ? "眼" : myRole === "hunter" ? "猎" : myRole === "idiot" ? "白" : "民"}
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600 }}>{ROLE_LABEL[myRole]}</div>
        {wolfTeammates?.length > 0 && (
          <div style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 2 }}>
            狼队友：{teammateNames.join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}