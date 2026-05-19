import React from "react";
import useGameStore from "../store/gameStore.js";
import RoundTable from "../components/RoundTable.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import PhaseBanner from "../components/PhaseBanner.jsx";
import ActionModal from "../components/ActionModal.jsx";
import RoleBadge from "../components/RoleBadge.jsx";

export default function Game() {
  const { roomCode, players, playerId, phase, day, deadlineTs,
          isHost, startGame, gameOver, myRole, seerResults } = useGameStore();
  const playerNameById = new Map(players.map((p) => [p.id, p.nickname]));
  const displayName = (id) => playerNameById.get(id) || id;

  const pageStyle = {
    minHeight: "100vh",
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
          {isHost && phase === "lobby" && (
            <button
              className="btn-gold"
              onClick={startGame}
              disabled={players.length < 6}
              style={{ fontSize: 13, padding: "8px 20px" }}
            >
              {players.length < 6 ? `等待玩家 (${players.length}/6)` : "开始游戏"}
            </button>
          )}
          {gameOver && (
            <button className="btn-secondary btn-sm" onClick={() => window.location.reload()}>
              返回大厅
            </button>
          )}
        </div>
      </header>

      {/* 主内容区 - 响应式网格 */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "50% 1fr",
        gap: 16,
        padding: "16px 24px 24px",
        maxWidth: 1400,
        margin: "0 auto",
        position: "relative",
        zIndex: 1,
      }}>
        {/* 左侧 - 游戏主区域（信息条 + 圆桌等） */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* 信息条 */}
          <div style={{
            display: "flex", gap: 12, alignItems: "stretch",
            flexWrap: "wrap",
          }}>
            <RoleBadge />
            <PhaseBanner phase={phase} day={day} deadlineTs={deadlineTs} />
          </div>

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

          {/* 圆桌 */}
          <RoundTable players={players} myId={playerId} />

          {/* 游戏结束 */}
          {gameOver && (
            <div className="card animate-fade-in-up" style={{
              border: "1px solid var(--gold)",
              textAlign: "center",
              padding: "24px",
            }}>
              <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
                {gameOver.winner === "good" ? "🏆 好人阵营胜利！" : "🐺 狼人阵营胜利！"}
              </div>
              <p style={{ color: "var(--fg-secondary)", fontSize: 13, marginBottom: 12 }}>
                最终角色身份
              </p>
              <div style={{ display: "flex", gap: 6, justifyContent: "center", flexWrap: "wrap" }}>
                {Object.entries(gameOver.roles || {}).map(([id, role]) => (
                  <span key={id} className={`tag ${role === "werewolf" ? "tag-wolf" : "tag-good"}`}>
                    {displayName(id)}: {role === "werewolf" ? "狼人" : role === "seer" ? "预言家" : role === "witch" ? "女巫" : role === "hunter" ? "猎人" : "平民"}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 右侧 - 聊天面板 */}
        <div style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
          <ChatPanel />
        </div>
      </div>

      <ActionModal />
    </div>
  );
}