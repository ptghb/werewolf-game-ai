import React, { useState } from "react";
import useGameStore from "../store/gameStore.js";
import { createWSClient } from "../ws/client.js";

export default function Lobby() {
  const [nickname, setNickname] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [mode, setMode] = useState("create");
  const [humanSlots, setHumanSlots] = useState(1);
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
      body: JSON.stringify({ nickname, human_slots: Number(humanSlots), ai_slots: 6 - Number(humanSlots) }),
    });
    const body = await r.json();
    attach(body.room_code, body.host_id, true);
  };

  const onJoin = async () => {
    const r = await fetch(`/api/rooms/${joinCode}/join`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ nickname }),
    });
    if (!r.ok) { alert("加入失败"); return; }
    const body = await r.json();
    attach(body.room_code, body.player_id, false);
  };

  return (
    <div style={{ padding: 40, maxWidth: 520, margin: "0 auto" }}>
      <h1>狼人杀 AI 陪练</h1>
      <label>昵称：<input value={nickname} onChange={(e) => setNickname(e.target.value)} /></label>
      <div style={{ margin: "16px 0" }}>
        <label><input type="radio" checked={mode === "create"} onChange={() => setMode("create")} /> 创建房间</label>
        <label style={{ marginLeft: 16 }}><input type="radio" checked={mode === "join"} onChange={() => setMode("join")} /> 加入房间</label>
      </div>
      {mode === "create" ? (
        <div>
          <label>真人位数：
            <select value={humanSlots} onChange={(e) => setHumanSlots(e.target.value)}>
              {[1,2,3,4,5,6].map(n => <option key={n} value={n}>{n} 人 ({6-n} AI)</option>)}
            </select>
          </label>
          <div><button onClick={onCreate} disabled={!nickname}>创建</button></div>
        </div>
      ) : (
        <div>
          <label>房间号：<input value={joinCode} onChange={(e) => setJoinCode(e.target.value.toUpperCase())} /></label>
          <div><button onClick={onJoin} disabled={!nickname || !joinCode}>加入</button></div>
        </div>
      )}
    </div>
  );
}