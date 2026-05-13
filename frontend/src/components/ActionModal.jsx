import React, { useState } from "react";
import useGameStore from "../store/gameStore.js";

const ACTION_LABELS = {
  wolf_vote: "选择今晚要杀的人", seer_check: "选择要查验的人",
  witch_action: "女巫行动（救/毒/跳）", day_vote: "投票出局",
  day_vote_pk: "PK 投票", speech: "发言", last_words: "遗言",
};

export default function ActionModal() {
  const prompt = useGameStore((s) => s.promptAction);
  const sendAction = useGameStore((s) => s.sendAction);
  const [target, setTarget] = useState("");
  const [text, setText] = useState("");
  if (!prompt) return null;
  const isSpeech = ["speech", "last_words"].includes(prompt.action);
  const isWitch = prompt.action === "witch_action";

  const submit = (action, extra = {}) => {
    sendAction({ action, target: extra.target ?? null, text: extra.text ?? null });
    setTarget(""); setText("");
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
                  display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "var(--bg-soft)", padding: 24, borderRadius: 12, minWidth: 360 }}>
        <h3>{ACTION_LABELS[prompt.action] || prompt.action}</h3>
        {prompt.hint && <p style={{ color: "var(--muted)" }}>{prompt.hint}</p>}
        {isSpeech ? (
          <>
            <textarea style={{ width: "100%", height: 80 }} value={text}
                      onChange={(e) => setText(e.target.value)} maxLength={80} />
            <button onClick={() => submit(prompt.action, { text })}>发言</button>
          </>
        ) : isWitch ? (
          <>
            <p>目标：
              <select value={target} onChange={(e) => setTarget(e.target.value)}>
                <option value="">-- 选择 --</option>
                {prompt.options.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </p>
            <div style={{ display: "flex", gap: 8 }}>
              <button disabled={!target} onClick={() => submit("witch_save", { target })}>救 {target}</button>
              <button disabled={!target} onClick={() => submit("witch_poison", { target })}>毒 {target}</button>
              <button onClick={() => submit("witch_skip")}>跳过</button>
            </div>
          </>
        ) : (
          <>
            <select value={target} onChange={(e) => setTarget(e.target.value)}>
              <option value="">-- 选择目标 --</option>
              {prompt.options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button disabled={!target} onClick={() => submit(prompt.action, { target })}>确认</button>
              {prompt.action === "seer_check" && (
                <button onClick={() => submit("seer_skip")}>跳过</button>
              )}
              {prompt.action === "day_vote" && (
                <button onClick={() => submit("day_abstain")}>弃票</button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}