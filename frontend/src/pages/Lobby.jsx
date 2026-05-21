import React, { useState } from "react";
import useGameStore from "../store/gameStore.js";
import { createWSClient } from "../ws/client.js";

export default function Lobby() {
  const [nickname, setNickname] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [mode, setMode] = useState("create");
  const [gameMode, setGameMode] = useState("6");
  const setConnection = useGameStore((s) => s.setConnection);
  const handleEvent = useGameStore((s) => s.handleEvent);

  const attach = (roomCode, playerId, isHost) => {
    const ws = createWSClient({
      url: `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
      room: roomCode, playerId,
      onMessage: handleEvent,
    });
    setConnection({ ws, roomCode, playerId, isHost });
  };

  const onCreate = async () => {
    const r = await fetch("/api/rooms", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ nickname, mode: gameMode }),
    });
    const body = await r.json();
    attach(body.room_code, body.host_id, true);
  };

  const onJoin = async () => {
    const r = await fetch(`/api/rooms/${joinCode}/join`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ nickname }),
    });
    if (!r.ok) { alert("房间不存在或已满"); return; }
    const body = await r.json();
    attach(body.room_code, body.player_id, false);
  };

  const pageStyle = {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "radial-gradient(ellipse at 50% 30%, #14162e 0%, var(--bg-deep) 70%)",
    padding: 20,
    position: "relative",
    overflow: "hidden",
  };

  const blobStyle = (size, color, x, y, delay) => ({
    position: "absolute",
    width: size,
    height: size,
    borderRadius: "50%",
    background: color,
    filter: "blur(80px)",
    opacity: 0.15,
    top: y,
    left: x,
    animation: `blob-float 8s ease-in-out infinite ${delay}s`,
    pointerEvents: "none",
  });

  const cardStyle = {
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-xl)",
    padding: "40px 36px",
    width: "100%",
    maxWidth: 440,
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
    position: "relative",
    zIndex: 1,
  };

  const inputGroupStyle = {
    marginBottom: 16,
  };

  const labelStyle = {
    display: "block",
    fontSize: 13,
    fontWeight: 600,
    color: "var(--fg-secondary)",
    marginBottom: 6,
    letterSpacing: "0.3px",
  };

  return (
    <div style={pageStyle}>
      {/* 背景光晕 */}
      <div style={blobStyle("400px", "var(--accent)", "-5%", "-10%", "0")} />
      <div style={blobStyle("300px", "var(--gold)", "60%", "50%", "2")} />
      <div style={blobStyle("350px", "var(--danger)", "70%", "-5%", "4")} />

      <div style={cardStyle}>
        {/* Logo区域 */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 64, height: 64, borderRadius: "var(--radius-lg)",
            background: "linear-gradient(135deg, var(--accent), #a78bfa)",
            display: "flex", alignItems: "center", justifyContent: "center",
            margin: "0 auto 16px",
            boxShadow: "0 0 30px var(--accent-glow)",
            fontSize: 28, fontWeight: 800, color: "white",
          }}>狼</div>
          <h1 style={{
            fontSize: 24, fontWeight: 700,
            background: "linear-gradient(135deg, var(--fg-primary), var(--accent))",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: "-0.5px",
          }}>狼人杀 AI 陪练</h1>
          <p style={{ color: "var(--fg-muted)", fontSize: 13, marginTop: 4 }}>
            与 AI 一起体验烧脑推理
          </p>
        </div>

        {/* 昵称输入 */}
        <div style={inputGroupStyle}>
          <label style={labelStyle}>你的昵称</label>
          <input
            placeholder="输入昵称..."
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            maxLength={8}
          />
        </div>

        {/* 模式切换 */}
        <div style={{
          display: "flex", gap: 0, marginBottom: 20,
          background: "var(--bg-elevated)",
          borderRadius: "var(--radius-md)",
          padding: 3,
        }}>
          {[
            { key: "create", label: "创建房间" },
            { key: "join", label: "加入房间" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setMode(tab.key)}
              style={{
                flex: 1,
                background: mode === tab.key ? "var(--accent)" : "transparent",
                color: mode === tab.key ? "white" : "var(--fg-secondary)",
                boxShadow: mode === tab.key ? "0 0 15px var(--accent-glow)" : "none",
                borderRadius: "calc(var(--radius-md) - 2px)",
                fontWeight: 600,
                fontSize: 13,
              }}
            >{tab.label}</button>
          ))}
        </div>

        {/* 创建模式 */}
        {mode === "create" && (
          <div style={{ animation: "fade-in 200ms ease-out" }}>
            <div style={inputGroupStyle}>
              <label style={labelStyle}>选择模式</label>
              <div style={{ display: "flex", gap: 10 }}>
                <div
                  onClick={() => setGameMode("6")}
                  className="card"
                  style={{
                    flex: 1, padding: "16px", cursor: "pointer", textAlign: "center",
                    border: gameMode === "6" ? "1px solid var(--accent)" : undefined,
                    background: gameMode === "6" ? "rgba(124,92,252,0.08)" : undefined,
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 800, color: "var(--fg-primary)" }}>6</div>
                  <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>6人场</div>
                  <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>5 AI</div>
                </div>
                <div
                  onClick={() => setGameMode("9")}
                  className="card"
                  style={{
                    flex: 1, padding: "16px", cursor: "pointer", textAlign: "center",
                    border: gameMode === "9" ? "1px solid var(--accent)" : undefined,
                    background: gameMode === "9" ? "rgba(124,92,252,0.08)" : undefined,
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 800, color: "var(--fg-primary)" }}>9</div>
                  <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>9人场</div>
                  <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>8 AI</div>
                </div>
                <div
                  onClick={() => setGameMode("12")}
                  className="card"
                  style={{
                    flex: 1, padding: "16px", cursor: "pointer", textAlign: "center",
                    border: gameMode === "12" ? "1px solid var(--accent)" : undefined,
                    background: gameMode === "12" ? "rgba(124,92,252,0.08)" : undefined,
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 800, color: "var(--fg-primary)" }}>12</div>
                  <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>12人场</div>
                  <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>11 AI</div>
                </div>
              </div>
            </div>
            <button
              className="btn-primary"
              onClick={onCreate}
              disabled={!nickname}
              style={{ width: "100%", padding: "12px", fontSize: 15, marginTop: 8 }}
            >创建房间</button>
          </div>
        )}

        {/* 加入模式 */}
        {mode === "join" && (
          <div style={{ animation: "fade-in 200ms ease-out" }}>
            <div style={inputGroupStyle}>
              <label style={labelStyle}>房间号</label>
              <input
                placeholder="输入6位房间号..."
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                maxLength={6}
                style={{ letterSpacing: 3, fontSize: 18, textAlign: "center", fontWeight: 700 }}
              />
            </div>
            <button
              className="btn-primary"
              onClick={onJoin}
              disabled={!nickname || !joinCode}
              style={{ width: "100%", padding: "12px", fontSize: 15, marginTop: 8 }}
            >加入房间</button>
          </div>
        )}
      </div>
    </div>
  );
}