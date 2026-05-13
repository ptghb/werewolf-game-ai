import React from "react";
import useGameStore from "../store/gameStore.js";
import RoundTable from "../components/RoundTable.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import PhaseBanner from "../components/PhaseBanner.jsx";
import ActionModal from "../components/ActionModal.jsx";
import RoleBadge from "../components/RoleBadge.jsx";
import SystemLog from "../components/SystemLog.jsx";

export default function Game() {
  const { roomCode, players, playerId, phase, day, deadlineTs,
          isHost, startGame, gameOver } = useGameStore();
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 16, padding: 16 }}>
      <div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <h2>房间 {roomCode}</h2>
          {isHost && phase === "lobby" && (
            <button onClick={startGame} disabled={players.length < 6}>开始游戏</button>
          )}
        </div>
        <RoleBadge />
        <PhaseBanner phase={phase} day={day} deadlineTs={deadlineTs} />
        <RoundTable players={players} myId={playerId} />
        {gameOver && (
          <div style={{ marginTop: 16, padding: 12, background: "var(--bg-soft)", borderRadius: 8 }}>
            <h3>游戏结束 — {gameOver.winner === "good" ? "好人胜利" : "狼人胜利"}</h3>
            <pre>{JSON.stringify(gameOver.roles, null, 2)}</pre>
          </div>
        )}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <SystemLog />
        <ChatPanel />
      </div>
      <ActionModal />
    </div>
  );
}