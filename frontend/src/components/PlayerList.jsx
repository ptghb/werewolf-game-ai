import React from "react";

export default function PlayerList({ players, myId, revealedRoles = {} }) {
  return (
    <div className="card" style={{
      flex: 1,
      minHeight: 0,
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
      padding: 0,
    }}>
      <div style={{
        overflowY: "auto",
        flex: 1,
        padding: "8px 10px",
      }}>
        {players.map((p) => {
          const alive = p.alive !== false;
          const isMe = p.id === myId;
          const isAI = p.is_ai;
          return (
            <div key={p.id} style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "8px 10px",
              borderRadius: "var(--radius-md)",
              background: isMe ? "rgba(124,92,252,0.08)" : "transparent",
              border: isMe ? "1px solid rgba(124,92,252,0.2)" : "1px solid transparent",
              opacity: alive ? 1 : 0.4,
              marginBottom: 4,
              transition: "all 0.2s ease",
            }}>
              {/* 头像 */}
              <div style={{
                width: 40, height: 40, borderRadius: "50%",
                background: isMe
                  ? "linear-gradient(135deg, var(--accent), #9278ff)"
                  : "var(--bg-card)",
                border: isMe
                  ? "2px solid var(--accent)"
                  : "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
                position: "relative",
              }}>
                <span style={{
                  fontSize: isAI ? 14 : 16,
                  fontWeight: 700,
                  color: isMe ? "white" : "var(--fg-primary)",
                  lineHeight: 1,
                }}>
                  {isAI ? "🤖" : (p.nickname?.[0] || "?")}
                </span>
                {!alive && (
                  <div style={{
                    position: "absolute", inset: 0,
                    borderRadius: "50%",
                    background: "rgba(0,0,0,0.5)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}>
                    <span style={{ fontSize: 18 }}>💀</span>
                  </div>
                )}
              </div>

              {/* 信息 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 13,
                  fontWeight: isMe ? 700 : 500,
                  color: isMe ? "var(--accent)" : "var(--fg-primary)",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                }}>
                  {isMe ? "你" : p.nickname}
                </div>
                {revealedRoles[p.id] && (
                  <div style={{
                    fontSize: 10, fontWeight: 600,
                    color: "var(--accent)",
                    marginTop: 1,
                  }}>
                    {revealedRoles[p.id]}
                  </div>
                )}
              </div>

              {/* 标签 */}
              {isAI && alive && (
                <span className="tag tag-accent" style={{ fontSize: 10, flexShrink: 0 }}>AI</span>
              )}
              {!alive && (
                <span style={{
                  fontSize: 11, color: "var(--fg-muted)", flexShrink: 0,
                  fontWeight: 600,
                }}>已死亡</span>
              )}
              {alive && (
                <span style={{
                  width: 6, height: 6, borderRadius: "50%",
                  background: "var(--success)",
                  flexShrink: 0,
                }} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
