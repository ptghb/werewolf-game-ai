import React, { useState } from "react";
import useGameStore from "../store/gameStore.js";

export default function AuthPage() {
  const [mode, setMode] = useState("login"); // login | register
  const [nickname, setNickname] = useState("");
  const [phone, setPhone] = useState("");
  const [account, setAccount] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const setAuth = useGameStore((s) => s.setAuth);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (mode === "register" && !nickname) { setError("请填写昵称"); return; }
    if (mode === "register" && !phone) { setError("请填写手机号"); return; }
    if (!account) { setError("请填写账号"); return; }
    if (!password) { setError("请填写密码"); return; }
    setLoading(true);
    try {
      const url = mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const body = mode === "register"
        ? { nickname, phone, account, password }
        : { account, password };
      const r = await fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const msg = (await r.json()).detail || "请求失败";
        setError(msg);
        return;
      }
      const data = await r.json();
      setAuth(data.user, data.token);
    } catch {
      setError("网络错误，请检查后端是否启动");
    } finally {
      setLoading(false);
    }
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
    width: "100%",
    maxWidth: 440,
    boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
    position: "relative",
    zIndex: 1,
  };

  const inputGroupStyle = { marginBottom: 16 };

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
      <div style={blobStyle("400px", "var(--accent)", "-5%", "-10%", "0")} />
      <div style={blobStyle("300px", "var(--gold)", "60%", "50%", "2")} />
      <div style={blobStyle("350px", "var(--danger)", "70%", "-5%", "4")} />

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
        </div>

        {/* 登录/注册切换 */}
        <div style={{
          display: "flex", gap: 0, marginBottom: 24,
          background: "var(--bg-elevated)",
          borderRadius: "var(--radius-md)",
          padding: 3,
        }}>
          {[
            { key: "login", label: "登录" },
            { key: "register", label: "注册" },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => { setMode(tab.key); setError(""); }}
              style={{
                flex: 1,
                background: mode === tab.key ? "var(--accent)" : "transparent",
                color: mode === tab.key ? "white" : "var(--fg-secondary)",
                boxShadow: mode === tab.key ? "0 0 15px var(--accent-glow)" : "none",
                borderRadius: "calc(var(--radius-md) - 2px)",
                fontWeight: 600, fontSize: 14,
              }}
            >{tab.label}</button>
          ))}
        </div>

        {error && (
          <div style={{
            padding: "8px 12px", marginBottom: 16,
            background: "var(--wolf-soft)",
            border: "1px solid var(--wolf)",
            borderRadius: "var(--radius-md)",
            color: "var(--wolf)", fontSize: 13,
          }}>{error}</div>
        )}

        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <>
              <div style={inputGroupStyle}>
                <label style={labelStyle}>昵称</label>
                <input
                  placeholder="输入昵称..."
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  maxLength={50}
                />
              </div>
              <div style={inputGroupStyle}>
                <label style={labelStyle}>手机号</label>
                <input
                  placeholder="输入手机号..."
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  maxLength={20}
                />
              </div>
            </>
          )}
          <div style={inputGroupStyle}>
            <label style={labelStyle}>账号</label>
            <input
              placeholder="输入账号..."
              value={account}
              onChange={(e) => setAccount(e.target.value)}
              maxLength={50}
            />
          </div>
          <div style={inputGroupStyle}>
            <label style={labelStyle}>密码</label>
            <input
              type="password"
              placeholder="输入密码..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              maxLength={128}
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading}
            style={{ width: "100%", padding: "12px", fontSize: 15, marginTop: 8 }}
          >
            {loading ? "处理中..." : mode === "register" ? "注册并登录" : "登录"}
          </button>
        </form>
      </div>
    </div>
  );
}