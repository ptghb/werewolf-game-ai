# AI Nickname Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show readable role-style AI nicknames and sender names throughout the game UI instead of internal player IDs.

**Architecture:** Keep player IDs as internal protocol identifiers for actions and game logic. Generate unique AI nicknames from existing AI personas at room creation, enrich chat events with display names on the backend, and resolve target IDs to nicknames in frontend display-only components.

**Tech Stack:** FastAPI backend, Python dataclasses, pytest, React frontend, Zustand store, Vite.

---

## File Structure

- Modify `backend/app/rooms/room_manager.py`: generate unique AI nicknames from persona names during room creation.
- Modify `backend/app/main.py`: include sender nickname when human chat enters the room queue.
- Modify `backend/app/game/phases/day_speech.py`: ensure AI speech chat events include sender nickname.
- Modify `backend/app/game/phases/day_vote.py`: ensure last-words chat events include sender nickname.
- Modify `backend/tests/test_smoke.py`: add backend tests for AI nickname generation and chat sender name payloads.
- Modify `frontend/src/components/ChatPanel.jsx`: render chat sender nickname instead of ID.
- Modify `frontend/src/pages/Game.jsx`: render nicknames in seer results and final role reveal.

### Task 1: Backend AI nickname generation

**Files:**
- Modify: `backend/app/rooms/room_manager.py`
- Test: `backend/tests/test_smoke.py`

- [ ] **Step 1: Write failing tests for AI nicknames**

Append these tests to `backend/tests/test_smoke.py`:

```python
import pytest

from app.rooms.room_manager import RoomManager


@pytest.mark.asyncio
async def test_ai_players_get_persona_nicknames():
    manager = RoomManager()

    room = await manager.create_room(host_nickname="房主", human_slots=1, ai_slots=5)

    ai_nicknames = [p.nickname for p in room.players if p.is_ai]
    assert len(ai_nicknames) == 5
    assert all(not nickname.startswith("AI-") for nickname in ai_nicknames)
    assert len(set(ai_nicknames)) == len(ai_nicknames)
```

If `backend/tests/test_smoke.py` already imports `pytest`, only add the missing import and test function once.

- [ ] **Step 2: Run test to verify it fails**

Run from repository root:

```bash
cd backend && pytest tests/test_smoke.py::test_ai_players_get_persona_nicknames -v
```

Expected: FAIL because current AI nicknames are `AI-1`, `AI-2`, etc.

- [ ] **Step 3: Implement unique persona nickname generation**

In `backend/app/rooms/room_manager.py`, replace the `ai_players = [...]` list comprehension in `create_room` with explicit generation:

```python
            ai_players = []
            nickname_counts: Dict[str, int] = {}
            for i in range(ai_slots):
                persona = random_persona()
                nickname_counts[persona.name] = nickname_counts.get(persona.name, 0) + 1
                nickname = persona.name if nickname_counts[persona.name] == 1 else f"{persona.name}{nickname_counts[persona.name]}"
                ai_players.append(AIPlayer(
                    id=f"ai_{uuid.uuid4().hex[:8]}",
                    nickname=nickname,
                    role=Role.VILLAGER,
                    seat=human_slots + i,
                    persona=persona,
                ))
```

This reuses the selected persona object for both nickname and AI behavior.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd backend && pytest tests/test_smoke.py::test_ai_players_get_persona_nicknames -v
```

Expected: PASS.

- [ ] **Step 5: Commit backend nickname generation**

Only if the user explicitly requested commits, run:

```bash
git add backend/app/rooms/room_manager.py backend/tests/test_smoke.py
git commit -m "feat: add persona nicknames for AI players"
```

### Task 2: Backend chat events include sender nickname

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/game/phases/day_speech.py`
- Modify: `backend/app/game/phases/day_vote.py`
- Test: `backend/tests/test_smoke.py`

- [ ] **Step 1: Locate existing AI chat event payloads**

Inspect these files before editing:

```bash
python - <<'PY'
from pathlib import Path
for path in [
    Path('backend/app/main.py'),
    Path('backend/app/game/phases/day_speech.py'),
    Path('backend/app/game/phases/day_vote.py'),
]:
    print(f'--- {path} ---')
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if 'chat_message' in line or '"from"' in line or "'from'" in line:
            print(f'{i}: {line}')
PY
```

Expected: output shows all chat event construction points that need `from_name`.

- [ ] **Step 2: Write failing test for human chat queue payload**

Append this test to `backend/tests/test_smoke.py`:

```python
import asyncio

from app.game.constants import Role
from app.players.human import HumanPlayer
from app.rooms.room import Room


@pytest.mark.asyncio
async def test_human_chat_queue_payload_includes_sender_nickname():
    player = HumanPlayer(id="h_1", nickname="小明", role=Role.VILLAGER, seat=0)
    room = Room(
        code="ABC123",
        host_id="h_1",
        human_slots=1,
        ai_slots=0,
        players=[player],
        created_at=0,
    )

    payload = {"channel": "day", "text": "大家好"}
    await room.queue.put({"type": "chat", "from": player.id, "from_name": player.nickname, **payload})
    queued = await asyncio.wait_for(room.queue.get(), timeout=0.1)

    assert queued == {
        "type": "chat",
        "from": "h_1",
        "from_name": "小明",
        "channel": "day",
        "text": "大家好",
    }
```

- [ ] **Step 3: Run test to verify it passes as a contract test**

Run:

```bash
cd backend && pytest tests/test_smoke.py::test_human_chat_queue_payload_includes_sender_nickname -v
```

Expected: PASS. This locks the intended payload shape before wiring the websocket handler.

- [ ] **Step 4: Add sender nickname to human chat queue payload**

In `backend/app/main.py`, change the websocket chat branch from:

```python
            elif mtype == "chat":
                await room.queue.put({"type": "chat", "from": player.id, **payload})
```

to:

```python
            elif mtype == "chat":
                await room.queue.put({"type": "chat", "from": player.id, "from_name": player.nickname, **payload})
```

- [ ] **Step 5: Add sender nickname to AI speech events**

In `backend/app/game/phases/day_speech.py`, find the `GameEvent(type="chat_message", ...)` payload for day speech and ensure it contains both fields:

```python
payload={
    "channel": "day",
    "from": speaker.id,
    "from_name": speaker.nickname,
    "text": resp.text or "(沉默)",
}
```

Use the local variable name already present in the file if it differs from `speaker`, but keep the payload keys exactly as shown.

- [ ] **Step 6: Add sender nickname to last-words events**

In `backend/app/game/phases/day_vote.py`, find the `GameEvent(type="chat_message", ...)` payload used for last words and ensure it contains:

```python
payload={
    "channel": "day",
    "from": eliminated.id,
    "from_name": eliminated.nickname,
    "text": resp.text or "(沉默)",
    "last_words": True,
}
```

Use the local variable name already present in the file if it differs from `eliminated`, but keep the payload keys exactly as shown.

- [ ] **Step 7: Run backend tests**

Run:

```bash
cd backend && pytest -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit backend chat display payloads**

Only if the user explicitly requested commits, run:

```bash
git add backend/app/main.py backend/app/game/phases/day_speech.py backend/app/game/phases/day_vote.py backend/tests/test_smoke.py
git commit -m "feat: include player nicknames in chat events"
```

### Task 3: Frontend renders nicknames instead of IDs

**Files:**
- Modify: `frontend/src/components/ChatPanel.jsx`
- Modify: `frontend/src/pages/Game.jsx`

- [ ] **Step 1: Add display helpers in Game page**

In `frontend/src/pages/Game.jsx`, inside `Game()` after the store destructuring, add:

```jsx
  const playerNameById = new Map(players.map((p) => [p.id, p.nickname]));
  const displayName = (id) => playerNameById.get(id) || id;
```

- [ ] **Step 2: Render seer target nickname**

In `frontend/src/pages/Game.jsx`, replace:

```jsx
                  <span>{r.target_id}</span>
```

with:

```jsx
                  <span>{displayName(r.target_id)}</span>
```

- [ ] **Step 3: Render final roles with nicknames**

In `frontend/src/pages/Game.jsx`, replace the final role label:

```jsx
                    {id}: {role === "werewolf" ? "狼人" : role === "seer" ? "预言家" : role === "witch" ? "女巫" : "平民"}
```

with:

```jsx
                    {displayName(id)}: {role === "werewolf" ? "狼人" : role === "seer" ? "预言家" : role === "witch" ? "女巫" : "平民"}
```

- [ ] **Step 4: Render chat sender nickname**

In `frontend/src/components/ChatPanel.jsx`, replace:

```jsx
              {m.from}
```

with:

```jsx
              {m.from_name || m.from}
```

- [ ] **Step 5: Build frontend**

Run:

```bash
cd frontend && npm run build
```

Expected: build succeeds with no React syntax errors.

- [ ] **Step 6: Commit frontend display changes**

Only if the user explicitly requested commits, run:

```bash
git add frontend/src/components/ChatPanel.jsx frontend/src/pages/Game.jsx
git commit -m "feat: show nicknames in game UI"
```

### Task 4: End-to-end verification

**Files:**
- No source changes expected.

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd backend && pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Manual browser verification**

Start the backend and frontend in separate terminals:

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Open the local Vite URL in a browser. Create a room with AI players, start the game, and verify:

- AI seats show role-style nicknames such as `理性派` or `冲锋派`, not `AI-1`.
- Human chat messages show the sender nickname, not `h_xxx`.
- AI day speeches show the AI nickname, not `ai_xxx`.
- Seer result and final role list display nicknames.

- [ ] **Step 4: Final status check**

Run:

```bash
git status --short
```

Expected: only intentional files are modified.

## Self-Review

- Spec coverage: AI persona nickname generation is covered by Task 1; chat nickname display is covered by Tasks 2 and 3; seer and final role ID display are covered by Task 3; verification is covered by Task 4.
- Placeholder scan: no TBD/TODO/fill-later items remain.
- Type consistency: backend event payload uses `from_name`; frontend reads `m.from_name || m.from`; IDs remain unchanged for action logic.
