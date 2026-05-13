import React, { useState, useEffect, useRef } from "react";
import useGameStore from "../store/gameStore.js";

const ACTION_LABELS = {
  wolf_vote: "选择击杀目标",
  seer_check: "选择查验对象",
  witch_action: "女巫行动",
  day_vote: "投出警徽",
  day_vote_pk: "PK 投票",
  speech: "你的发言",
  last_words: "遗言",
};

const ACTION_ICONS = {
  wolf_vote: "🐺",
  seer_check: "🔮",
  witch_action: "🧪",
  day_vote: "🗳️",
  day_vote_pk: "🗳️",
  speech: "💬",
  last_words: "💀",
};

function optionLabel(id, players) {
  const p = players.find((pl) => pl.id === id);
  return p ? `${p.nickname}` : id;
}

export default function ActionModal() {
  const prompt = useGameStore((s) => s.promptAction);
  const sendAction = useGameStore((s) => s.sendAction);
  const players = useGameStore((s) => s.players);
  const [target, setTarget] = useState("");
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const visible = !!prompt;

  useEffect(() => {
    if (visible) {
      setTarget("");
      setText("");
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [visible]);

  if (!prompt) return null;

  const isSpeech = ["speech", "last_words"].includes(prompt.action);
  const isWitch = prompt.action === "witch_action";

  const submit = (action, extra = {}) => {
    sendAction({ action, target: extra.target ?? null, text: extra.text ?? null });
  };

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "rgba(0, 0, 0, 0.6)",
      backdropFilter: "blur(4px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 20,
    }}>
      <div
        className="animate-fade-in-up"
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-xl)",
          padding: "28px 24px",
          width: "100%",
          maxWidth: 400,
          boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
        }}
      >
        {/* 标题 */}
        <div style={{
          display: "flex", alignItems: "center", gap: 10, marginBottom: 20,
        }}>
          <span style={{ fontSize: 24 }}>{ACTION_ICONS[prompt.action] || "🎯"}</span>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>
              {ACTION_LABELS[prompt.action] || prompt.action}
            </div>
            {prompt.hint && (
              <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 2 }}>
                {prompt.hint}
              </div>
            )}
          </div>
        </div>

        {/* 发言模式 */}
        {isSpeech ? (
          <div>
            <textarea
              ref={textareaRef}
              style={{
                width: "100%", height: 100,
                background: "var(--bg-elevated)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
                padding: 12, fontSize: 14,
                color: "var(--fg-primary)",
                resize: "none",
              }}
              placeholder={prompt.action === "last_words" ? "留下你的遗言..." : "输入你的发言..."}
              value={text}
              onChange={(e) => setText(e.target.value)}
              maxLength={80}
            />
            <div style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              marginTop: 8,
            }}>
              <span style={{ fontSize: 11, color: "var(--fg-muted)" }}>
                {text.length}/80
              </span>
              <button
                className="btn-primary"
                onClick={() => submit(prompt.action, { text })}
                disabled={!text.trim()}
              >
                {prompt.action === "last_words" ? "留下遗言" : "发言"}
              </button>
            </div>
          </div>
        ) : isWitch ? (
          <div>
            <p style={{ fontSize: 13, color: "var(--fg-secondary)", marginBottom: 12 }}>
              选择目标：
            </p>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              style={{ marginBottom: 12 }}
            >
              <option value="">-- 请选择 --</option>
              {prompt.options.map(o => (
                <option key={o} value={o}>{optionLabel(o, players)}</option>
              ))}
            </select>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                className="btn-primary"
                disabled={!target}
                onClick={() => submit("witch_save", { target })}
                style={{ flex: 1, fontSize: 12 }}
              >
                🩹 救
              </button>
              <button
                className="btn-danger"
                disabled={!target}
                onClick={() => submit("witch_poison", { target })}
                style={{ flex: 1, fontSize: 12 }}
              >
                ☠️ 毒
              </button>
              <button
                className="btn-secondary"
                onClick={() => submit("witch_skip")}
                style={{ flex: 1, fontSize: 12 }}
              >
                跳过
              </button>
            </div>
          </div>
        ) : (
          <div>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              style={{ marginBottom: 12 }}
            >
              <option value="">-- 请选择目标 --</option>
              {prompt.options.map(o => (
                <option key={o} value={o}>{optionLabel(o, players)}</option>
              ))}
            </select>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                className="btn-primary"
                disabled={!target}
                onClick={() => submit(prompt.action, { target })}
                style={{ flex: 1 }}
              >
                确认
              </button>
              {prompt.action === "seer_check" && (
                <button
                  className="btn-secondary"
                  onClick={() => submit("seer_skip")}
                  style={{ flex: 1 }}
                >
                  跳过
                </button>
              )}
              {prompt.action === "day_vote" && (
                <button
                  className="btn-secondary"
                  onClick={() => submit("day_abstain")}
                  style={{ flex: 1 }}
                >
                  弃票
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}