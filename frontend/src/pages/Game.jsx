import React, { useState, useEffect } from "react";
import useGameStore from "../store/gameStore.js";
import RoundTable from "../components/RoundTable.jsx";
import PlayerList from "../components/PlayerList.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import PhaseBanner from "../components/PhaseBanner.jsx";
import { ROLE_LABEL } from "../constants.js";

export default function Game() {
  const { roomCode, players, playerId, phase, day, deadlineTs,
          isHost, startGame, gameOver, returnToLobby, myRole, seerResults, revealedRoles, wolfTeammates } = useGameStore();
  const user = useGameStore((s) => s.user);
  const preferredRole = useGameStore((s) => s.preferredRole);

  const [isNarrow, setIsNarrow] = useState(() => window.innerWidth < 900);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 899px)");
    const handler = (e) => setIsNarrow(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  const playerNameById = new Map(players.map((p) => [p.id, p.nickname]));
  const displayName = (id) => playerNameById.get(id) || id;

  // 把自己的角色也合并到公开角色中，在圆桌上展示
  const allRevealed = { ...revealedRoles };
  if (myRole) {
    allRevealed[playerId] = ROLE_LABEL[myRole] || myRole;
  }
  if (myRole === "werewolf" && wolfTeammates) {
    for (const id of wolfTeammates) {
      allRevealed[id] = "狼人";
    }
  }

  const pageStyle = {
    height: "100dvh",
    display: "flex",
    flexDirection: "column",
    background: "radial-gradient(ellipse at 50% 20%, #14162e 0%, var(--bg-deep) 70%)",
    position: "relative",
    overflow: "hidden",
  };

  const blobStyle = (size, color, x, y) => ({
    position: "fixed",
    width: size, height: size,
    borderRadius: "50%",
    background: color,
    filter: "blur(120px)",
    opacity: 0.1,
    top: y, left: x,
    pointerEvents: "none",
    zIndex: 0,
  });

  return (
    <div style={pageStyle}>
      <div style={blobStyle("500px", "var(--accent)", "-10%", "-10%")} />
      <div style={blobStyle("400px", "var(--gold)", "70%", "60%")} />
      <div style={blobStyle("300px", "var(--danger)", "50%", "-5%")} />

      {/* 顶部栏 */}
      <header style={{
        position: "relative", zIndex: 1,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 24px",
        background: "rgba(12, 13, 23, 0.8)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--border)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: "var(--radius-sm)",
            background: "linear-gradient(135deg, var(--accent), #a78bfa)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 14, fontWeight: 800, color: "white",
          }}>狼</div>
          <span style={{ fontSize: 13, color: "var(--fg-muted)" }}>
            房间 <strong style={{ color: "var(--fg-primary)", letterSpacing: 1 }}>{roomCode}</strong>
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {gameOver ? (
            <button
              className="btn-primary"
              onClick={returnToLobby}
              style={{ fontSize: 13, padding: "8px 20px" }}
            >
              返回大厅
            </button>
          ) : isHost && phase === "lobby" && (
            <button
              className="btn-gold"
              onClick={() => startGame(preferredRole || undefined)}
              disabled={players.length < 6}
              style={{ fontSize: 13, padding: "8px 20px" }}
            >
              {players.length < 6 ? `等待玩家 (${players.length}/6)` : "开始游戏"}
            </button>
          )}
                  </div>
      </header>

      {/* 信息条 - 顶部居中 */}
      <div style={{
        display: "flex", gap: 12, alignItems: "stretch", justifyContent: "center",
        flexWrap: "wrap",
        padding: "12px 24px 0",
        position: "relative", zIndex: 1,
      }}>
        <PhaseBanner phase={phase} day={day} deadlineTs={deadlineTs} winner={gameOver?.winner} />
      </div>

      {/* 主内容区 - 响应式网格 */}
      <div className="game-layout" style={{
        padding: "16px 24px 24px",
        position: "relative",
        zIndex: 1,
        flex: 1,
        minHeight: 0,
      }}>
        {/* 左侧 - 游戏主区域（圆桌等） */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12, minHeight: 0 }}>

          {/* 预言家查验结果 */}
          {myRole === "seer" && seerResults.length > 0 && (
            <div className="card animate-fade-in" style={{
              borderLeft: "3px solid var(--accent)",
              padding: "10px 14px",
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--accent)", marginBottom: 6 }}>
                查验记录
              </div>
              {seerResults.map((r, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 8, fontSize: 13,
                  padding: "3px 0",
                }}>
                  <span className={`tag ${r.is_wolf ? "tag-wolf" : "tag-good"}`}>
                    {r.is_wolf ? "狼人" : "好人"}
                  </span>
                  <span>{displayName(r.target_id)}</span>
                </div>
              ))}
            </div>
          )}

          {/* 圆桌（横屏）/ 玩家列表（竖屏） */}
          {isNarrow ? (
            <PlayerList players={players} myId={playerId} revealedRoles={allRevealed} />
          ) : (
            <RoundTable players={players} myId={playerId} revealedRoles={allRevealed} />
          )}

        </div>

        {/* 右侧 - 聊天面板 */}
        <div style={{ height: "100%", minHeight: 0 }}>
          <ChatPanel />
        </div>
      </div>
    </div>
  );
}