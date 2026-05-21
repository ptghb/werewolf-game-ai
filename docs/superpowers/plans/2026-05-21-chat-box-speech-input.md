# Chat Box Speech Input Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the human speech modal with the bottom-right chat input, keeping chat muted by default and enabling it only during the player's speech or last-words prompt.

**Architecture:** Keep the backend protocol unchanged. `ActionModal` will stop rendering `speech` and `last_words` prompts, while `ChatPanel` will treat those prompts as the only unmuted input state and submit through `sendAction`, which already clears `promptAction` immediately after sending.

**Tech Stack:** React 19, Zustand store, Vite frontend, existing WebSocket action protocol.

---

## File Structure

- Modify `frontend/src/components/ChatPanel.jsx`: change chat input state logic so it is disabled by default, enabled only for `speech`/`last_words`, and submits `sendAction({ action, text })` instead of `sendChat` during those prompts.
- Modify `frontend/src/components/ActionModal.jsx`: return `null` for `speech`/`last_words` prompts so no modal appears for human speech.
- No backend changes: `backend/app/players/human.py` and phase code already accept `action` payloads with `text`.
- No permanent test framework exists in `frontend/package.json`; verification uses focused Node source assertions plus `npm --prefix frontend run build`.

---

### Task 1: Add failing source assertions for speech UI routing

**Files:**
- Test via one-off command against `frontend/src/components/ChatPanel.jsx`
- Test via one-off command against `frontend/src/components/ActionModal.jsx`

- [ ] **Step 1: Run failing assertion for ChatPanel behavior**

Run:

```bash
node - <<'NODE'
const fs = require('fs');
const s = fs.readFileSync('frontend/src/components/ChatPanel.jsx', 'utf8');
const required = [
  'const muted = !speechPrompt;',
  'sendAction({ action: speechPrompt.action, target: null, text: trimmed });',
  'disabled={muted}',
  'disabled={!text.trim() || muted}',
  'placeholder={speechPrompt ? (speechPrompt.action === "last_words" ? "留下你的遗言..." : "输入你的发言...") : "等待你的发言回合..."}'
];
for (const token of required) {
  if (!s.includes(token)) throw new Error(`Missing ChatPanel token: ${token}`);
}
NODE
```

Expected: FAIL with at least one `Missing ChatPanel token` error because `ChatPanel` currently disables input while speaking and sends ordinary chat.

- [ ] **Step 2: Run failing assertion for ActionModal speech suppression**

Run:

```bash
node - <<'NODE'
const fs = require('fs');
const s = fs.readFileSync('frontend/src/components/ActionModal.jsx', 'utf8');
const required = [
  'const isSpeech = ["speech", "last_words"].includes(prompt.action);',
  'if (isSpeech) return null;',
];
for (const token of required) {
  if (!s.includes(token)) throw new Error(`Missing ActionModal token: ${token}`);
}
if (s.includes('{isSpeech ? (')) throw new Error('ActionModal still renders the speech branch');
NODE
```

Expected: FAIL because `ActionModal` currently renders a speech textarea branch.

---

### Task 2: Implement chat-box speech submission

**Files:**
- Modify: `frontend/src/components/ChatPanel.jsx:1-120`

- [ ] **Step 1: Update store selectors and speech state**

Replace the top of `ChatPanel` state setup with:

```jsx
const SPEECH_PHASES = new Set(["speech", "last_words"]);

export default function ChatPanel() {
  const { messageLog, promptAction, sendAction } = useGameStore();
  const speechPrompt = promptAction && SPEECH_PHASES.has(promptAction.action) ? promptAction : null;
  const muted = !speechPrompt;
  const [text, setText] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
```

- [ ] **Step 2: Focus and clear input only when speech becomes available**

Add this effect after the scroll effect:

```jsx
  useEffect(() => {
    if (speechPrompt) {
      setText("");
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [speechPrompt]);
```

- [ ] **Step 3: Replace `handleSend` with action submission**

Replace the existing `handleSend` function with:

```jsx
  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || !speechPrompt) return;
    sendAction({ action: speechPrompt.action, target: null, text: trimmed });
    setText("");
  };
```

- [ ] **Step 4: Replace input disabled and placeholder logic**

In the `<input>` props, use:

```jsx
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
```

- [ ] **Step 5: Replace send button disabled and label logic**

In the `<button>` props/body, use:

```jsx
          onClick={handleSend}
          disabled={!text.trim() || muted}
          style={{ whiteSpace: "nowrap", opacity: muted ? 0.4 : 1 }}
        >
          {speechPrompt?.action === "last_words" ? "遗言" : "发言"}
```

- [ ] **Step 6: Run ChatPanel assertion and build**

Run:

```bash
node - <<'NODE'
const fs = require('fs');
const s = fs.readFileSync('frontend/src/components/ChatPanel.jsx', 'utf8');
const required = [
  'const muted = !speechPrompt;',
  'sendAction({ action: speechPrompt.action, target: null, text: trimmed });',
  'disabled={muted}',
  'disabled={!text.trim() || muted}',
  'placeholder={speechPrompt ? (speechPrompt.action === "last_words" ? "留下你的遗言..." : "输入你的发言...") : "等待你的发言回合..."}'
];
for (const token of required) {
  if (!s.includes(token)) throw new Error(`Missing ChatPanel token: ${token}`);
}
NODE
npm --prefix frontend run build
```

Expected: assertion exits 0 and Vite build exits 0.

---

### Task 3: Suppress speech modal while preserving other action modals

**Files:**
- Modify: `frontend/src/components/ActionModal.jsx:31-132`

- [ ] **Step 1: Move speech check before modal rendering**

Keep this existing line after the `if (!prompt) return null;` guard:

```jsx
  const isSpeech = ["speech", "last_words"].includes(prompt.action);
```

Then add:

```jsx
  if (isSpeech) return null;
```

- [ ] **Step 2: Remove speech textarea render branch**

Replace:

```jsx
        {isSpeech ? (
          <div>
            ...speech textarea branch...
          </div>
        ) : isWitchSave ? (
```

with:

```jsx
        {isWitchSave ? (
```

Leave the witch, vote, and other non-speech branches unchanged.

- [ ] **Step 3: Remove speech-only local state and ref if unused**

If `text`, `setText`, and `textareaRef` are no longer referenced after removing the speech branch, change:

```jsx
  const [text, setText] = useState("");
  const textareaRef = useRef(null);
```

and the effect body:

```jsx
      setText("");
      setTimeout(() => textareaRef.current?.focus(), 100);
```

so the component only resets target for visible non-speech modals:

```jsx
  useEffect(() => {
    if (visible) {
      setTarget("");
    }
  }, [visible]);
```

- [ ] **Step 4: Remove unused imports**

If `useRef` is no longer used, change the import to:

```jsx
import React, { useState, useEffect } from "react";
```

- [ ] **Step 5: Run ActionModal assertion and build**

Run:

```bash
node - <<'NODE'
const fs = require('fs');
const s = fs.readFileSync('frontend/src/components/ActionModal.jsx', 'utf8');
const required = [
  'const isSpeech = ["speech", "last_words"].includes(prompt.action);',
  'if (isSpeech) return null;',
];
for (const token of required) {
  if (!s.includes(token)) throw new Error(`Missing ActionModal token: ${token}`);
}
if (s.includes('{isSpeech ? (')) throw new Error('ActionModal still renders the speech branch');
NODE
npm --prefix frontend run build
```

Expected: assertion exits 0 and Vite build exits 0.

---

### Task 4: Final verification

**Files:**
- Verify: `frontend/src/components/ChatPanel.jsx`
- Verify: `frontend/src/components/ActionModal.jsx`

- [ ] **Step 1: Run combined source assertions**

Run:

```bash
node - <<'NODE'
const fs = require('fs');
const chat = fs.readFileSync('frontend/src/components/ChatPanel.jsx', 'utf8');
const modal = fs.readFileSync('frontend/src/components/ActionModal.jsx', 'utf8');
for (const token of [
  'const muted = !speechPrompt;',
  'sendAction({ action: speechPrompt.action, target: null, text: trimmed });',
  'disabled={muted}',
  'disabled={!text.trim() || muted}',
  '等待你的发言回合...',
  '输入你的发言...',
  '留下你的遗言...'
]) {
  if (!chat.includes(token)) throw new Error(`Missing ChatPanel token: ${token}`);
}
for (const token of [
  'const isSpeech = ["speech", "last_words"].includes(prompt.action);',
  'if (isSpeech) return null;'
]) {
  if (!modal.includes(token)) throw new Error(`Missing ActionModal token: ${token}`);
}
if (modal.includes('{isSpeech ? (')) throw new Error('ActionModal still renders the speech branch');
NODE
```

Expected: exits 0.

- [ ] **Step 2: Build frontend**

Run:

```bash
npm --prefix frontend run build
```

Expected: Vite reports `✓ built` and exits 0.

- [ ] **Step 3: Manual UI check**

Run:

```bash
npm --prefix frontend run dev -- --host 127.0.0.1
```

Expected checks in browser:
- Before the player's speech prompt, the bottom-right chat input is disabled and shows `等待你的发言回合...`.
- During a `speech` prompt, no speech modal appears, the chat input is enabled, and the button label is `发言`.
- After submitting speech, the input clears and becomes disabled immediately.
- During a `last_words` prompt, no speech modal appears, the chat input is enabled, and the button label is `遗言`.
- Non-speech actions still use `ActionModal`.

Stop the dev server after checking.

---

## Self-Review

- Spec coverage: default muted chat, speech/last_words chat enablement, action submission parity, immediate mute after send, and non-speech modal preservation are all covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `promptAction`, `sendAction`, `action`, `target`, and `text` match the existing Zustand store and WebSocket action payload shape.
- Commit note: do not commit unless the user explicitly asks for a commit.
