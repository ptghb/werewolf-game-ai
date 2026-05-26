import React, { useEffect, useState } from "react";
import useGameStore from "../store/gameStore.js";
import { createWSClient } from "../ws/client.js";

function LlmSettings({ userId, onClose }) {
  const [tokens, setTokens] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ base_url: "", api_key: "", model: "" });
  const [testing, setTesting] = useState(null);

  const load = () => {
    fetch(`/api/llm-tokens?user_id=${userId}`)
      .then((r) => r.json())
      .then(setTokens)
      .catch(() => {});
  };

  useEffect(() => { load(); }, [userId]);

  const resetForm = () => {
    setForm({ base_url: "", api_key: "", model: "" });
    setEditing(null);
    setShowForm(false);
  };

  const handleSave = async () => {
    if (editing) {
      await fetch(`/api/llm-tokens/${editing}?user_id=${userId}`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(form),
      });
    } else {
      await fetch(`/api/llm-tokens?user_id=${userId}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(form),
      });
    }
    resetForm();
    load();
  };

  const handleDelete = async (id) => {
    await fetch(`/api/llm-tokens/${id}?user_id=${userId}`, { method: "DELETE" });
    load();
  };

  const handleToggle = async (t) => {
    const newEnable = t.enable === 1 ? 0 : 1;
    await fetch(`/api/llm-tokens/${t.id}?user_id=${userId}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ enable: newEnable }),
    });
    load();
  };

  const handleTest = async (id) => {
    setTesting(id);
    try {
      const r = await fetch(`/api/llm-tokens/${id}/test?user_id=${userId}`, { method: "POST" });
      const body = await r.json();
      if (r.ok) {
        alert(`连接成功: ${(body.reply || "").slice(0, 100)}`);
      } else {
        alert(`连接失败: ${body.detail || "未知错误"}`);
      }
    } catch {
      alert("请求失败");
    } finally {
      setTesting(null);
    }
  };

  const startEdit = (t) => {
    setEditing(t.id);
    setForm({ base_url: t.base_url, api_key: t.api_key, model: t.model });
    setShowForm(true);
  };

  const overlayStyle = {
    position: "fixed", inset: 0, zIndex: 1000,
    background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)",
    display: "flex", alignItems: "center", justifyContent: "center",
    padding: 20,
  };

  const dialogStyle = {
    width: "100%", maxWidth: 640, maxHeight: "85dvh",
    background: "var(--bg-card)", border: "1px solid var(--border)",
    borderRadius: "var(--radius-xl)", padding: "28px 24px",
    display: "flex", flexDirection: "column",
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
  };

  const inputStyle = {
    width: "100%", padding: "8px 10px",
    background: "var(--bg-elevated)", border: "1px solid var(--border)",
    borderRadius: "var(--radius-md)", color: "var(--fg-primary)",
    fontSize: 13, outline: "none",
  };

  const labelStyle = {
    display: "block", fontSize: 12, fontWeight: 600,
    color: "var(--fg-secondary)", marginBottom: 4,
  };

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={dialogStyle} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>LLM 配置</div>
          <button className="btn-ghost btn-sm" onClick={onClose}>关闭</button>
        </div>

        {/* 已有列表 */}
        <div style={{ flex: 1, overflowY: "auto", marginBottom: 16, display: "flex", flexDirection: "column", gap: 8 }}>
          {tokens.length === 0 && (
            <div style={{ color: "var(--fg-muted)", fontSize: 13, textAlign: "center", padding: "30px 0" }}>
              暂无配置，点击下方按钮添加
            </div>
          )}
          {tokens.map((t) => (
            <div key={t.id} style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "10px 12px",
              background: "var(--bg-elevated)", borderRadius: "var(--radius-md)",
              fontSize: 13, opacity: t.enable ? 1 : 0.5,
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.model}
                </div>
                <div style={{ fontSize: 11, color: "var(--fg-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.base_url}
                </div>
              </div>
              <span style={{
                fontSize: 11, fontWeight: 600,
                color: t.enable ? "var(--good)" : "var(--fg-muted)",
                whiteSpace: "nowrap",
              }}>
                {t.enable ? "● 已启用" : "○ 未启用"}
              </span>
              <button className={`btn-sm ${t.enable ? "btn-ghost" : "btn-secondary"}`}
                      onClick={() => handleToggle(t)}
                      style={{ minWidth: 44, fontSize: 12 }}>
                {t.enable ? "禁用" : "启用"}
              </button>
              <button className="btn-ghost btn-sm" onClick={() => handleTest(t.id)} disabled={testing === t.id}
                      style={{ fontSize: 12 }}>
                {testing === t.id ? "测试中..." : "测试"}
              </button>
              <button className="btn-ghost btn-sm" onClick={() => startEdit(t)} style={{ fontSize: 12 }}>编辑</button>
              <button className="btn-ghost btn-sm" onClick={() => handleDelete(t.id)} style={{ fontSize: 12, color: "var(--danger)" }}>删除</button>
            </div>
          ))}
        </div>

        {/* 新增/编辑表单 */}
        {showForm && (
          <div style={{
            padding: 16, marginBottom: 12,
            background: "var(--bg-elevated)", borderRadius: "var(--radius-md)",
          }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div>
                <label style={labelStyle}>Base URL</label>
                <input style={inputStyle} placeholder="https://api.openai.com/v1"
                       value={form.base_url}
                       onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>API Key</label>
                <input style={inputStyle} placeholder="sk-..."
                       value={form.api_key}
                       onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>Model</label>
                <input style={inputStyle} placeholder="gpt-4o"
                       value={form.model}
                       onChange={(e) => setForm({ ...form, model: e.target.value })} />
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn-primary btn-sm" onClick={handleSave}>
                {editing ? "保存" : "添加"}
              </button>
              <button className="btn-ghost btn-sm" onClick={resetForm}>取消</button>
            </div>
          </div>
        )}

        {!showForm && (
          <button className="btn-secondary" onClick={() => { resetForm(); setShowForm(true); }}
                  style={{ width: "100%", padding: "10px", fontSize: 13 }}>
            + 添加配置
          </button>
        )}
      </div>
    </div>
  );
}

export default function Lobby() {
  const [gameMode, setGameMode] = React.useState("6");
  const [history, setHistory] = React.useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const preferredRole = useGameStore((s) => s.preferredRole);
  const setPreferredRole = useGameStore((s) => s.setPreferredRole);
  const godMode = useGameStore((s) => s.godMode);
  const setGodMode = useGameStore((s) => s.setGodMode);
  const setConnection = useGameStore((s) => s.setConnection);
  const handleEvent = useGameStore((s) => s.handleEvent);
  const user = useGameStore((s) => s.user);
  const logout = useGameStore((s) => s.logout);
  const setReview = useGameStore((s) => s.setReview);

  const [isNarrow, setIsNarrow] = useState(() => window.innerWidth < 900);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 899px)");
    const handler = (e) => setIsNarrow(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    fetch(`/api/auth/rooms/history?user_id=${user.id}`)
      .then((r) => r.json())
      .then(setHistory)
      .catch(() => {});
  }, [user.id]);

  const attach = (roomCode, playerId, isHost) => {
    const ws = createWSClient({
      url: `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
      room: roomCode, playerId, spectator: godMode,
      onMessage: handleEvent,
    });
    setConnection({ ws, roomCode, playerId, isHost });
  };

  const onCreate = async () => {
    const r = await fetch("/api/rooms", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ user_id: user.id, nickname: user.nickname, mode: gameMode, god_mode: godMode }),
    });
    const body = await r.json();
    if (!r.ok) {
      alert(body.detail || "创建房间失败");
      return;
    }
    attach(body.room_code, body.host_id, true);
  };

  const onGodMode = async () => {
    const r = await fetch("/api/rooms", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ user_id: user.id, nickname: user.nickname, mode: gameMode, god_mode: true }),
    });
    const body = await r.json();
    if (!r.ok) { alert(body.detail || "创建失败"); return; }
    const wsClient = createWSClient({
      url: `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`,
      room: body.room_code, playerId: body.host_id, spectator: true,
      onMessage: handleEvent,
    });
    setConnection({ ws: wsClient, roomCode: body.room_code, playerId: body.host_id, isHost: true });
    setTimeout(() => {
      wsClient.send("start_game", { preferred_role: preferredRole || undefined });
    }, 2000);
  };

  const onReview = (roomId) => {
    fetch(`/api/auth/rooms/history/${roomId}`)
      .then((r) => r.json())
      .then((data) => setReview(data))
      .catch(() => alert("获取复盘数据失败"));
  };

  const [showLlmSettings, setShowLlmSettings] = useState(false);

  const pageStyle = {
    height: "100dvh",
    display: "flex",
    flexDirection: "column",
    background: "radial-gradient(ellipse at 50% 30%, #14162e 0%, var(--bg-deep) 70%)",
    padding: 20,
    position: "relative",
    overflow: "hidden",
  };

  const blobStyle = (size, color, x, y, delay) => ({
    position: "fixed",
    width: size, height: size,
    borderRadius: "50%",
    background: color,
    filter: "blur(80px)",
    opacity: 0.15,
    top: y, left: x,
    animation: `blob-float 8s ease-in-out infinite ${delay}s`,
    pointerEvents: "none",
  });

  const cardStyle = {
    background: "var(--bg-card)",
    border: "1px solid var(--border)",
    borderRadius: "var(--radius-xl)",
    padding: "40px 36px",
    flex: 1,
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
    position: "relative",
    zIndex: 1,
  };

  const inputGroupStyle = { marginBottom: 16 };

  const labelStyle = {
    display: "block", fontSize: 13, fontWeight: 600,
    color: "var(--fg-secondary)", marginBottom: 6, letterSpacing: "0.3px",
  };

  return (
    <div style={pageStyle}>
      <div style={blobStyle("400px", "var(--accent)", "-5%", "-10%", "0")} />
      <div style={blobStyle("300px", "var(--gold)", "60%", "50%", "2")} />
      <div style={blobStyle("350px", "var(--danger)", "70%", "-5%", "4")} />

      <div className="lobby-layout" style={{
        position: "relative", zIndex: 1,
      }}>
        {/* 左栏：创建/加入房间 */}
        <div style={cardStyle}>
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

          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "8px 12px", marginBottom: 20,
            background: "var(--bg-elevated)",
            borderRadius: "var(--radius-md)", fontSize: 13,
          }}>
            <span style={{ color: "var(--fg-secondary)" }}>
              {user.nickname}
              <span style={{ marginLeft: 8, color: "var(--fg-muted)", fontSize: 12 }}>
                Lv.{user.level}
              </span>
            </span>
            <button className="btn-ghost btn-sm" onClick={logout}>退出</button>
          </div>

          <div style={inputGroupStyle}>
            <label style={labelStyle}>选择模式</label>
            <div style={{ display: "flex", gap: 10 }}>
              {["6", "9", "12"].map((m) => (
                <div key={m}
                  onClick={() => setGameMode(m)}
                  className="card"
                  style={{
                    flex: 1, padding: "16px", cursor: "pointer", textAlign: "center",
                    border: gameMode === m ? "1px solid var(--accent)" : undefined,
                    background: gameMode === m ? "rgba(124,92,252,0.08)" : undefined,
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ fontSize: 28, fontWeight: 800, color: "var(--fg-primary)" }}>{m}</div>
                  <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>{m}人场</div>
                  <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>{Number(m) - 1} AI</div>
                </div>
              ))}
            </div>
          </div>

          
          {user.vip > 1 && (
            <div style={{ marginTop: 8 }}>
              <label style={labelStyle}>选择角色（VIP特权）</label>
              <select
                value={preferredRole}
                onChange={(e) => setPreferredRole(e.target.value)}
              >
                <option value="">随机分配</option>
                {gameMode === "6" && (
                  <>
                    <option value="werewolf">狼人</option>
                    <option value="witch">女巫</option>
                    <option value="seer">预言家</option>
                    <option value="villager">平民</option>
                  </>
                )}
                {gameMode === "9" && (
                  <>
                    <option value="werewolf">狼人</option>
                    <option value="witch">女巫</option>
                    <option value="seer">预言家</option>
                    <option value="hunter">猎人</option>
                    <option value="villager">平民</option>
                  </>
                )}
                {gameMode === "12" && (
                  <>
                    <option value="werewolf">狼人</option>
                    <option value="witch">女巫</option>
                    <option value="seer">预言家</option>
                    <option value="hunter">猎人</option>
                    <option value="idiot">白痴</option>
                    <option value="villager">平民</option>
                  </>
                )}
              </select>
            </div>
          )}
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button
              className="btn-primary"
              onClick={onCreate}
              style={{ flex: 1, padding: "12px", fontSize: 15 }}
            >创建房间</button>
            {user.vip > 2 && (
              <button
                className="btn-gold"
                onClick={onGodMode}
                style={{ flex: 1, padding: "12px", fontSize: 13 }}
              >
                上帝视角
              </button>
            )}
            {isNarrow && (
              <button
                className="btn-secondary"
                onClick={() => setShowHistory(true)}
                style={{ padding: "12px 16px", fontSize: 13, marginTop: 8, whiteSpace: "nowrap" }}
              >我的战绩</button>
            )}
          </div>
          <button
            className="btn-secondary"
            onClick={() => setShowLlmSettings(true)}
            style={{ width: "100%", padding: "10px", fontSize: 13, marginTop: 8 }}
          >LLM 设置</button>
        </div>

        {/* 右栏：历史战绩（仅横屏） */}
        {!isNarrow && (
          <div className="card" style={{
            flex: 1, padding: "24px 20px",
            boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
            zIndex: 1,
            display: "flex", flexDirection: "column",
            minHeight: 0, overflow: "hidden",
          }}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 16, flexShrink: 0 }}>我的战绩</div>
            {history.length === 0 ? (
              <div style={{ color: "var(--fg-muted)", fontSize: 13, padding: "40px 0", textAlign: "center" }}>
                暂无已结束的游戏
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, overflowY: "auto", flex: 1, minHeight: 0 }}>
                {history.map((r) => (
                  <div key={r.id} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "10px 12px",
                    background: "var(--bg-elevated)",
                    borderRadius: "var(--radius-md)",
                  }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{r.room_code}</div>
                      <div style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 2 }}>
                        {r.result === "good" ? <span style={{ color: "var(--good)" }}>好人胜</span> :
                         r.result === "werewolf" ? <span style={{ color: "var(--wolf)" }}>狼人胜</span> :
                         <span>进行中</span>}
                        <span style={{ marginLeft: 8 }}>{r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}</span>
                      </div>
                    </div>
                    <button className="btn-secondary btn-sm" onClick={() => onReview(r.id)}>复盘</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 竖屏：我的战绩弹窗 */}
      {showHistory && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 1000,
          background: "rgba(0, 0, 0, 0.6)",
          backdropFilter: "blur(4px)",
          display: "flex", alignItems: "center", justifyContent: "center",
          padding: 20,
        }} onClick={() => setShowHistory(false)}>
          <div className="card animate-fade-in-up" style={{
            width: "100%", maxWidth: 500, maxHeight: "80dvh",
            padding: "24px 20px",
            display: "flex", flexDirection: "column",
            overflow: "hidden",
          }} onClick={(e) => e.stopPropagation()}>
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              marginBottom: 16,
            }}>
              <div style={{ fontSize: 16, fontWeight: 700 }}>我的战绩</div>
              <button className="btn-ghost btn-sm" onClick={() => setShowHistory(false)}>关闭</button>
            </div>
            {history.length === 0 ? (
              <div style={{ color: "var(--fg-muted)", fontSize: 13, padding: "40px 0", textAlign: "center" }}>
                暂无已结束的游戏
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, overflowY: "auto", flex: 1 }}>
                {history.map((r) => (
                  <div key={r.id} style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    padding: "10px 12px",
                    background: "var(--bg-elevated)",
                    borderRadius: "var(--radius-md)",
                  }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{r.room_code}</div>
                      <div style={{ fontSize: 11, color: "var(--fg-muted)", marginTop: 2 }}>
                        {r.result === "good" ? <span style={{ color: "var(--good)" }}>好人胜</span> :
                         r.result === "werewolf" ? <span style={{ color: "var(--wolf)" }}>狼人胜</span> :
                         <span>进行中</span>}
                        <span style={{ marginLeft: 8 }}>{r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}</span>
                      </div>
                    </div>
                    <button className="btn-secondary btn-sm" onClick={() => onReview(r.id)}>复盘</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* LLM 设置弹窗 */}
      {showLlmSettings && (
        <LlmSettings userId={user.id} onClose={() => setShowLlmSettings(false)} />
      )}
    </div>
  );
}
