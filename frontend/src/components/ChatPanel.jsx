import React, { useState, useEffect, useRef } from "react";
import useGameStore from "../store/gameStore.js";

const SPEECH_PHASES = new Set(["speech", "last_words"]);

const ACTION_LABELS = {
  wolf_vote: "选择击杀目标",
  seer_check: "选择查验对象",
  witch_save: "女巫救药",
  witch_poison: "女巫毒药",
  day_vote: "投票放逐",
  day_vote_pk: "PK 投票",
};

const ACTION_ICONS = {
  wolf_vote: "🐺",
  seer_check: "🔮",
  witch_save: "🧪",
  witch_poison: "🧪",
  day_vote: "🗳️",
  day_vote_pk: "🗳️",
};

function optionLabel(id, players) {
  const p = players.find((pl) => pl.id === id);
  return p ? p.nickname : id;
}

export default function ChatPanel() {
  const { messageLog, promptAction, sendAction, players, godMode } = useGameStore();
  const speechPrompt = promptAction && SPEECH_PHASES.has(promptAction.action) ? promptAction : null;
  const actionPrompt = promptAction && !SPEECH_PHASES.has(promptAction.action) ? promptAction : null;
  const muted = !speechPrompt;
  const [text, setText] = useState("");
  const [target, setTarget] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messageLog.length]);

  useEffect(() => {
    if (speechPrompt) {
      setText("");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [speechPrompt]);

  useEffect(() => {
    if (actionPrompt) {
      setTarget("");
    }
  }, [actionPrompt]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || !speechPrompt) return;
    sendAction({ action: speechPrompt.action, target: null, text: trimmed });
    setText("");
  };

  const submitAction = (action, extra = {}) => {
    sendAction({ action, target: extra.target ?? null, text: extra.text ?? null });
  };

  const renderActionArea = () => {
    if (!actionPrompt) return null;

    const isWitchSave = actionPrompt.action === "witch_save";
    const isWitchPoison = actionPrompt.action === "witch_poison";

    return (
      <div style={{
        padding: "10px 12px",
        borderTop: "1px solid var(--border-accent)",
        background: "rgba(124,92,252,0.04)",
      }}>
        {/* 标题 */}
        <div style={{
          display: "flex", alignItems: "center", gap: 8, marginBottom: 10,
        }}>
          <span style={{ fontSize: 18 }}>{ACTION_ICONS[actionPrompt.action] || "🎯"}</span>
          <div style={{ fontSize: 13, fontWeight: 700 }}>
            {ACTION_LABELS[actionPrompt.action] || actionPrompt.action}
          </div>
        </div>

        {/* 提示 */}
        {actionPrompt.hint && (
          <div style={{ fontSize: 11, color: "var(--fg-muted)", marginBottom: 8 }}>
            {actionPrompt.hint}
          </div>
        )}

        {isWitchSave ? (
          <div>
            <p style={{ fontSize: 12, color: "var(--fg-secondary)", marginBottom: 8 }}>
              今晚被狼人杀死的是{" "}
              <strong style={{ color: "var(--fg-primary)" }}>
                {optionLabel(actionPrompt.options[0], players)}
              </strong>
            </p>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                className="btn-primary"
                onClick={() => submitAction("witch_save", { target: actionPrompt.options[0] })}
                style={{ flex: 1, fontSize: 12 }}
              >
                救人
              </button>
              <button
                className="btn-secondary"
                onClick={() => submitAction("witch_skip")}
                style={{ flex: 1, fontSize: 12 }}
              >
                不救
              </button>
            </div>
          </div>
        ) : isWitchPoison ? (
          <div>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              style={{ marginBottom: 8, fontSize: 13 }}
            >
              <option value="">-- 请选择毒杀目标 --</option>
              {actionPrompt.options.map(o => (
                <option key={o} value={o}>{optionLabel(o, players)}</option>
              ))}
            </select>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                className="btn-danger"
                disabled={!target}
                onClick={() => submitAction("witch_poison", { target })}
                style={{ flex: 1, fontSize: 12 }}
              >
                毒杀
              </button>
              <button
                className="btn-secondary"
                onClick={() => submitAction("witch_skip")}
                style={{ flex: 1, fontSize: 12 }}
              >
                不用毒药
              </button>
            </div>
          </div>
        ) : (
          <div>
            <select
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              style={{ marginBottom: 8, fontSize: 13 }}
            >
              <option value="">-- 请选择目标 --</option>
              {actionPrompt.options.map(o => (
                <option key={o} value={o}>{optionLabel(o, players)}</option>
              ))}
            </select>
            <div style={{ display: "flex", gap: 6 }}>
              <button
                className="btn-primary"
                disabled={!target}
                onClick={() => submitAction(actionPrompt.action, { target })}
                style={{ flex: 1, fontSize: 12 }}
              >
                确认
              </button>
              {actionPrompt.action === "seer_check" && (
                <button
                  className="btn-secondary"
                  onClick={() => submitAction("seer_skip")}
                  style={{ flex: 1, fontSize: 12 }}
                >
                  跳过
                </button>
              )}
              {(actionPrompt.action === "day_vote" || actionPrompt.action === "day_vote_pk") && (
                <button
                  className="btn-secondary"
                  onClick={() => submitAction("day_abstain")}
                  style={{ flex: 1, fontSize: 12 }}
                >
                  弃票
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="card" style={{
      display: "flex", flexDirection: "column", height: "100%", padding: 0, overflow: "hidden",
    }}>
      {/* 标题 */}
      <div style={{
        padding: "10px 12px 8px",
        borderBottom: "1px solid var(--border)",
        fontSize: 11, fontWeight: 600, color: "var(--fg-muted)",
      }}>
        消息
      </div>

      {/* 消息列表 */}
      <div style={{
        flex: 1, overflowY: "auto", padding: "8px 10px",
        display: "flex", flexDirection: "column", gap: 4,
      }}>
        {messageLog.length === 0 && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center",
            height: "100%",
            color: "var(--fg-muted)", fontSize: 12, opacity: 0.5,
          }}>
            暂无消息
          </div>
        )}
        {messageLog.map((m, i) => (
          m.type === "system" ? (
            <div key={i} style={{
              fontSize: 12, lineHeight: 1.5,
              color: "var(--fg-primary)",
              opacity: 0.7,
              padding: "4px 8px",
              borderLeft: "2px solid var(--border)",
              background: "var(--surface)",
              borderRadius: "var(--radius-sm)",
            }}>
              📢 {m.text}
            </div>
          ) : (
            <div key={i} style={{
              fontSize: 12, lineHeight: 1.5,
              opacity: m.last_words ? 0.85 : 1,
              padding: "4px 6px",
              borderRadius: "var(--radius-sm)",
              background: m.last_words ? "var(--surface)" : "transparent",
            }}>
              <span style={{ fontWeight: 600, color: "var(--accent)" }}>
                {m.from_name || m.from}
              </span>
              <span style={{ color: "var(--fg-primary)", marginLeft: 4 }}>
                {m.text}
              </span>
              {m.last_words && (
                <span style={{ color: "var(--danger)", fontSize: 10, marginLeft: 4 }}>
                  [遗言]
                </span>
              )}
            </div>
          )
        ))}
        <div ref={bottomRef} />
      </div>

      {/* 动作区 / 发送区 */}
      {!godMode && actionPrompt ? (
        renderActionArea()
      ) : (
        <div style={{
          display: "flex", gap: 6, padding: "8px 10px",
          borderTop: "1px solid var(--border)",
          background: "var(--surface)",
        }}>
          <input
            ref={inputRef}
            style={{
              flex: 1, padding: "8px 10px", fontSize: 12,
              opacity: muted ? 0.4 : 1,
            }}
            placeholder={speechPrompt ? (speechPrompt.action === "last_words" ? "留下你的遗言..." : "输入你的发言...") : "等待你的发言回合..."}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
            maxLength={80}
            disabled={muted}
          />
          <button
            className="btn-primary btn-sm"
            onClick={handleSend}
            disabled={!text.trim() || muted}
            style={{ whiteSpace: "nowrap", opacity: muted ? 0.4 : 1 }}
          >
            {speechPrompt?.action === "last_words" ? "遗言" : "发言"}
          </button>
        </div>
      )}
    </div>
  );
}
