# 9人狼人杀 + 猎人角色 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 9-player mode with hunter role, update room creation UI to select game mode instead of human slot count.

**Architecture:** Refactor the room creation flow (frontend + backend) to accept a `mode` parameter ("6"/"9") instead of `human_slots`/`ai_slots`. Add `HUNTER` role enum, 9-player role pool, hunter shot phase (triggered on wolf-kill or vote elimination), and update AI prompts/tools. All existing 6-player behavior remains unchanged.

**Tech Stack:** Python 3.11+, FastAPI, Zustand (frontend state), React

---

### Task 1: constants.py — Add HUNTER role, NINE_PLAYER_ROLES, new Phase and timeout

**Files:**
- Modify: `backend/app/game/constants.py`

- [ ] **Step 1: Load the file**

- [ ] **Step 2: Add HUNTER to Role enum, HUNTER_SHOT to Phase enum, add NINE_PLAYER_ROLES and HUNTER_SHOT_TIMEOUT**

```python
class Role(str, Enum):
    WEREWOLF = "werewolf"
    WITCH = "witch"
    SEER = "seer"
    VILLAGER = "villager"
    HUNTER = "hunter"


class Phase(str, Enum):
    LOBBY = "lobby"
    ROLE_ASSIGN = "role_assign"
    NIGHT_START = "night_start"
    WOLF_KILL = "wolf_kill"
    SEER_CHECK = "seer_check"
    WITCH_ACTION = "witch_action"
    DAY_ANNOUNCE = "day_announce"
    DAY_SPEECH = "day_speech"
    DAY_VOTE = "day_vote"
    HUNTER_SHOT = "hunter_shot"
    CHECK_WIN = "check_win"
    GAME_OVER = "game_over"
```

And after `SIX_PLAYER_ROLES`:

```python
NINE_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
    Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
    Role.SEER, Role.WITCH, Role.HUNTER,
]
```

And after existing timeouts:

```python
HUNTER_SHOT_TIMEOUT = 30
```

- [ ] **Step 3: Run existing tests**

Run: `python3 -m pytest backend/tests/test_constants.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/game/constants.py
git commit -m "feat: add HUNTER role, NINE_PLAYER_ROLES, HUNTER_SHOT phase"
```

---

### Task 2: assign.py — Support 9 players

**Files:**
- Modify: `backend/app/game/assign.py`
- Test: `backend/tests/test_assign.py`

- [ ] **Step 1: Update assign_roles to accept n=9**

```python
from app.game.constants import Role, SIX_PLAYER_ROLES, NINE_PLAYER_ROLES


def assign_roles(n: int, rng: random.Random | None = None) -> list[Role]:
    if n not in (6, 9):
        raise ValueError(f"Only 6 or 9-player games supported, got {n}")
    rng = rng or random.Random()
    pool = list(NINE_PLAYER_ROLES if n == 9 else SIX_PLAYER_ROLES)
    rng.shuffle(pool)
    return pool
```

- [ ] **Step 2: Add test for 9-player assignment**

In `backend/tests/test_assign.py`:

```python
def test_assign_roles_9_players():
    roles = assign_roles(9)
    assert len(roles) == 9
    assert roles.count(Role.WEREWOLF) == 3
    assert roles.count(Role.VILLAGER) == 3
    assert roles.count(Role.SEER) == 1
    assert roles.count(Role.WITCH) == 1
    assert roles.count(Role.HUNTER) == 1


def test_assign_roles_rejects_invalid():
    with pytest.raises(ValueError):
        assign_roles(5)
```

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest backend/tests/test_assign.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/game/assign.py backend/tests/test_assign.py
git commit -m "feat: assign_roles supports 9 players"
```

---

### Task 3: state.py — Add hunter tracking fields

**Files:**
- Modify: `backend/app/game/state.py`

- [ ] **Step 1: Add hunter fields to GameState**

```python
@dataclass
class GameState:
    room_code: str
    players: list[PlayerState]
    phase: Phase
    host_id: str = ""
    day_number: int = 0
    tonight_killed_by_wolves: str | None = None
    tonight_poisoned_by_witch: str | None = None
    tonight_saved_by_witch: bool = False
    witch: WitchPotions = field(default_factory=WitchPotions)
    last_vote_tally: dict[str, str] = field(default_factory=dict)
    hunter_can_shoot: bool = True
    hunter_just_died: bool = False
    last_death_reason: str | None = None
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: 105+ PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/game/state.py
git commit -m "feat: add hunter_can_shoot, hunter_just_died, last_death_reason to GameState"
```

---

### Task 4: room_manager.py — Support mode parameter

**Files:**
- Modify: `backend/app/rooms/room_manager.py`

- [ ] **Step 1: Update create_room to accept mode**

Change the method signature and logic:

```python
async def create_room(
    self,
    host_nickname: str,
    mode: str = "6",
) -> Room:
    if mode == "6":
        total = 6
        ai_slots = 5
    elif mode == "9":
        total = 9
        ai_slots = 8
    else:
        raise ValueError(f"Invalid mode: {mode}")

    async with self._lock:
        code = self._new_code()
        host = HumanPlayer(
            id=f"h_{uuid.uuid4().hex[:8]}",
            nickname=host_nickname,
            role=Role.VILLAGER,
            seat=0,
        )
        ai_players = []
        used_names: set[str] = set()
        for i in range(ai_slots):
            persona = random_persona()
            name = persona.name
            while name in used_names:
                name = persona.name + str(random.randint(2, 99))
            used_names.add(name)
            ai = AIPlayer(
                id=f"ai_{uuid.uuid4().hex[:8]}",
                nickname=name,
                role=Role.VILLAGER,
                seat=1 + i,
                persona=persona,
            )
            ai_players.append(ai)
        room = Room(
            code=code,
            host_id=host.id,
            human_slots=1,
            ai_slots=ai_slots,
            players=[host] + ai_players,
            queue=asyncio.Queue(),
            created_at=time.time(),
        )
        self._rooms[code] = room
        return room
```

- [ ] **Step 2: Remove the old total == 6 validation that used human_slots + ai_slots**

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/rooms/room_manager.py
git commit -m "feat: room_manager.create_room accepts mode param (6/9)"
```

---

### Task 5: main.py — Update CreateRoomBody and create_room endpoint

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Update CreateRoomBody and create_room**

```python
class CreateRoomBody(BaseModel):
    nickname: str
    mode: str = "6"
```

```python
@app.post("/api/rooms")
async def create_room(body: CreateRoomBody):
    try:
        room = await manager.create_room(
            host_nickname=body.nickname,
            mode=body.mode,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"room_code": room.code, "host_id": room.host_id}
```

- [ ] **Step 2: Update _run_game to pass correct player count**

Find the line `roles = assign_roles(6)` and change to use the room's player count:

```python
roles = assign_roles(len(room.players))
```

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: create_room endpoint uses mode, dynamic player count in _run_game"
```

---

### Task 6: Create phases/hunter_shot.py

**Files:**
- Create: `backend/app/game/phases/hunter_shot.py`

- [ ] **Step 1: Create the hunter_shot phase module**

```python
from __future__ import annotations

import logging
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


logger = logging.getLogger("werewolf.game.phase")


async def run_hunter_shot(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> str | None:
    """Hunter shoots after being killed by wolves or voted out.

    Only triggers if the hunter hasn't used their shot yet.
    Does NOT trigger if the hunter was poisoned by the witch.
    Returns the ID of the shot target, or None if skipped.
    """
    if not state.hunter_can_shoot or not state.hunter_just_died:
        return None

    # Find the hunter player (they are now dead)
    hunter = None
    for p in state.alive_players():
        if p.role == Role.HUNTER:
            hunter = p
            break
    if hunter is not None:
        # Hunter is still alive, not actually dead — should not shoot
        return None

    # Hunter is among dead players — find them by role
    hunter_state = None
    for p in state.players:
        if p.role == Role.HUNTER:
            hunter_state = p
            break
    if hunter_state is None:
        return None

    logger.info("阶段开始 | 猎人开枪 | day=%d | hunter=%s", state.day_number, hunter_state.id)
    state.phase = Phase.HUNTER_SHOT
    await broadcaster.broadcast(GameEvent(
        type="phase_change",
        payload={"phase": "hunter_shot", "deadline_ts": deadline_ts},
    ))

    player_lookup = {p.id: p for p in players}
    hunter_player = player_lookup.get(hunter_state.id)
    if hunter_player is None:
        return None

    options = [p.id for p in state.alive_players()]
    nickname_map = {p.id: p.nickname for p in state.players}
    resp = await hunter_player.request(ActionPrompt(
        action="hunter_shot",
        options=options,
        deadline_ts=deadline_ts,
        hint="You are the hunter and you've been eliminated. You may shoot one player or skip.",
        nickname_map=nickname_map,
    ))

    if resp.action == "hunter_skip" or resp.target is None:
        logger.info("猎人放弃开枪 | hunter=%s", hunter_state.id)
        state.hunter_can_shoot = False
        state.hunter_just_died = False
        return None

    if resp.target not in options:
        logger.warning("猎人开枪目标无效 | target=%s", resp.target)
        state.hunter_can_shoot = False
        state.hunter_just_died = False
        return None

    # Hunter shoots
    target_state = state.get_player(resp.target)
    if target_state:
        target_state.alive = False
    logger.info("猎人开枪 | hunter=%s | target=%s(%s)",
                hunter_state.id, resp.target, target_state.nickname if target_state else "?")
    state.hunter_can_shoot = False
    state.hunter_just_died = False

    await broadcaster.broadcast(GameEvent(
        type="death_announce",
        payload={"dead": [resp.target], "reason": "hunter_shot"},
    ))

    return resp.target


__all__ = ["run_hunter_shot"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/game/phases/hunter_shot.py
git commit -m "feat: add hunter_shot phase module"
```

---

### Task 7: engine.py — Wire hunter_shot into game loop

**Files:**
- Modify: `backend/app/game/engine.py`

- [ ] **Step 1: Import hunter_shot and add timeout**

```python
from app.game.phases.hunter_shot import run_hunter_shot
```

Add to `DEFAULT_TIMEOUTS`:

```python
DEFAULT_TIMEOUTS = {
    "wolf_kill": 45,
    "seer_check": 20,
    "witch_action": 25,
    "day_announce": 5,
    "day_speech": 60,
    "day_vote": 30,
    "last_words": 30,
    "hunter_shot": 30,
}
```

- [ ] **Step 2: Add hunter tracking in day_announce aftermath and after day_vote**

In `run_one_round`, after `run_day_announce`:

```python
        await run_day_announce(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("day_announce"),
        )

        # Check if hunter was killed by wolves (not poisoned)
        if self.state.tonight_killed_by_wolves:
            killed_player = self.state.get_player(self.state.tonight_killed_by_wolves)
            if killed_player and killed_player.role == Role.HUNTER:
                self.state.hunter_just_died = True
                self.state.last_death_reason = "wolf"
        await run_hunter_shot(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("hunter_shot"),
        )
        self.state.hunter_just_died = False

        if self._resolve_winner():
            return
```

After `run_day_vote`:

```python
        result = await run_day_vote(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("day_vote"),
        )
        if result.get("eliminated"):
            eliminated_player = self.state.get_player(result["eliminated"])
            if eliminated_player and eliminated_player.role == Role.HUNTER:
                self.state.hunter_just_died = True
                self.state.last_death_reason = "vote"
            await run_hunter_shot(
                self.state,
                self.players,
                broadcaster=self.broadcaster,
                deadline_ts=self._deadline("hunter_shot"),
            )
            self.state.hunter_just_died = False
        self._resolve_winner()
```

Note: You'll need to capture the return value of `run_day_vote`. Change the existing call from:

```python
        await run_day_vote(
            self.state,
            self.players,
            broadcaster=self.broadcaster,
            deadline_ts=self._deadline("day_vote"),
        )
        self._resolve_winner()
```

to capture the result dict.

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/game/engine.py
git commit -m "feat: wire hunter_shot into game loop after wolf-kill death and vote elimination"
```

---

### Task 8: prompts.py — Add hunter description and 9-player rules

**Files:**
- Modify: `backend/app/ai/prompts.py`

- [ ] **Step 1: Add HUNTER role description and update RULES_SUMMARY**

```python
ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.WEREWOLF: "你是狼人。夜间你和狼队友一起决定击杀目标；白天要伪装好人，避免被投出。",
    Role.SEER: "你是预言家（好人阵营）。夜间每晚查验一名玩家的身份；白天要利用信息引导好人投票。",
    Role.WITCH: "你是女巫（好人阵营）。你有救药和毒药各 1 瓶（全局计数），同一夜不能同时使用两瓶。",
    Role.VILLAGER: "你是平民（好人阵营）。你无特殊技能，依靠推理和发言引导投票。",
    Role.HUNTER: "你是猎人（好人阵营）。当你被狼人杀死或被投票放逐时，可以开枪带走任意一名玩家。被女巫毒死不能开枪。",
}

RULES_SUMMARY = """
游戏规则（6 人局）：2 狼人 + 1 女巫 + 1 预言家 + 2 平民。
游戏规则（9 人局）：3 狼人 + 1 女巫 + 1 预言家 + 3 平民 + 1 猎人。
夜间：狼人共刀 → 预言家查验 → 女巫决定救/毒/跳。
白天：公布死讯 → 轮流发言 → 全员投票（平票则 PK，再平无人出局）。
猎人：被狼刀或公投出局时可开枪带走一人；被毒不能开枪。
胜负：所有狼人死 → 好人胜；好人全死 → 狼人胜。
""".strip()
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/ai/prompts.py
git commit -m "feat: add hunter role description and 9-player rules"
```

---

### Task 9: tools.py — Add hunter_shot action tools

**Files:**
- Modify: `backend/app/ai/tools.py`

- [ ] **Step 1: Add hunter_shot to tools_for_action**

Before the `return []` at the end:

```python
if action == "hunter_shot":
    return [
        _mk("hunter_shot", "Shoot a player and take them down with you." + opts_hint, TargetInput),
        _mk("hunter_skip", "Choose not to shoot.", NoInput),
    ]
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/ai/tools.py
git commit -m "feat: add hunter_shot and hunter_skip tools"
```

---

### Task 10: ai.py — Add hunter_shot support in AIPlayer

**Files:**
- Modify: `backend/app/players/ai.py`

- [ ] **Step 1: Add hunter_shot handling in _is_valid, fallback, and _log_decision**

In `_is_valid`, after the `witch_action` block:

```python
if prompt.action == "hunter_shot":
    if resp.action == "hunter_skip":
        return True
    return resp.target in prompt.options
```

In `_log_decision`, add after the `day_vote_pk` log block:

```python
elif action == "hunter_shot":
    logger.info("猎人开枪 | %s | target=%s", player_info, resp.target or "跳过")
elif action == "hunter_skip":
    logger.info("猎人放弃开枪 | %s", player_info)
```

In the fallback section (after `day_vote` fallback, before the final `_default_target`):

```python
if prompt.action == "hunter_shot":
    resp = ActionResponse(action="hunter_skip")
    await self._log_decision(prompt, resp)
    return resp
```

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/players/ai.py
git commit -m "feat: add hunter_shot support in AIPlayer validation, logging, and fallback"
```

---

### Task 11: Frontend Lobby.jsx — Mode selection UI

**Files:**
- Modify: `frontend/src/pages/Lobby.jsx`

- [ ] **Step 1: Replace human_slots selector with mode selector**

Replace the human slots button group with two mode buttons. The relevant section currently renders buttons 1-6. Replace with:

```jsx
{/* 游戏模式选择 */}
<div style={{ marginBottom: 16 }}>
  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--fg-secondary)", marginBottom: 8 }}>
    选择模式
  </div>
  <div style={{ display: "flex", gap: 10 }}>
    <div
      onClick={() => setMode("6")}
      className="card"
      style={{
        flex: 1, padding: "16px", cursor: "pointer", textAlign: "center",
        border: mode === "6" ? "1px solid var(--accent)" : undefined,
        background: mode === "6" ? "rgba(124,92,252,0.08)" : undefined,
        transition: "all 0.2s",
      }}
    >
      <div style={{ fontSize: 28, fontWeight: 800, color: "var(--fg-primary)" }}>6</div>
      <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>6人场</div>
      <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>5 AI</div>
    </div>
    <div
      onClick={() => setMode("9")}
      className="card"
      style={{
        flex: 1, padding: "16px", cursor: "pointer", textAlign: "center",
        border: mode === "9" ? "1px solid var(--accent)" : undefined,
        background: mode === "9" ? "rgba(124,92,252,0.08)" : undefined,
        transition: "all 0.2s",
      }}
    >
      <div style={{ fontSize: 28, fontWeight: 800, color: "var(--fg-primary)" }}>9</div>
      <div style={{ fontSize: 12, color: "var(--fg-muted)", marginTop: 4 }}>9人场</div>
      <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>8 AI</div>
    </div>
  </div>
</div>
```

- [ ] **Step 2: Update state and onCreate**

Replace `const [humanSlots, setHumanSlots] = useState(1);` with:

```jsx
const [mode, setMode] = useState("6");
```

Update `onCreate`:

```jsx
const onCreate = async () => {
    const r = await fetch("/api/rooms", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ nickname, mode }),
    });
    const body = await r.json();
    attach(body.room_code, body.host_id, true);
};
```

Remove the `human_slots` / `ai_slots` variable and its import.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Lobby.jsx
git commit -m "feat: replace human_slots selector with 6/9 mode selector in Lobby"
```

---

### Task 12: Add tests for hunter_shot

**Files:**
- Create: `backend/tests/test_hunter_shot.py`

- [ ] **Step 1: Write hunter_shot tests**

```python
import pytest

from app.game.constants import Role, Phase
from app.game.events import GameEvent
from app.game.phases.hunter_shot import run_hunter_shot
from app.game.state import GameState, PlayerState
from app.players.base import ActionPrompt, ActionResponse
from tests.fakes import FakeAIPlayer


@pytest.fixture
def state():
    players = [
        PlayerState(id="hunter", nickname="猎人", role=Role.HUNTER, is_ai=True, seat=0, alive=False),
        PlayerState(id="wolf1", nickname="狼1", role=Role.WEREWOLF, is_ai=True, seat=1, alive=True),
        PlayerState(id="villager", nickname="村民", role=Role.VILLAGER, is_ai=True, seat=2, alive=True),
    ]
    return GameState(room_code="TEST", players=players, phase=Phase.HUNTER_SHOT,
                     hunter_can_shoot=True, hunter_just_died=True)


@pytest.fixture
def hunter_player():
    return FakeAIPlayer(id="hunter", nickname="猎人", role=Role.HUNTER, seat=0)


async def test_hunter_shoots_target(state, hunter_player):
    hunter_player.response = ActionResponse(action="hunter_shot", target="wolf1")
    target = await run_hunter_shot(state, [hunter_player], broadcaster=...)
    assert target == "wolf1"
    assert not state.hunter_can_shoot
    assert not state.hunter_just_died
    assert not state.get_player("wolf1").alive


async def test_hunter_skips(state, hunter_player):
    hunter_player.response = ActionResponse(action="hunter_skip")
    target = await run_hunter_shot(state, [hunter_player], broadcaster=...)
    assert target is None
    assert not state.hunter_can_shoot


async def test_hunter_no_shot_if_alive(state):
    state.get_player("hunter").alive = True
    hunter_player = FakeAIPlayer(id="hunter", nickname="猎人", role=Role.HUNTER, seat=0, alive=True)
    target = await run_hunter_shot(state, [hunter_player], broadcaster=...)
    assert target is None


async def test_hunter_no_shot_if_cannot_shoot(state):
    state.hunter_can_shoot = False
    hunter_player = FakeAIPlayer(id="hunter", nickname="猎人", role=Role.HUNTER, seat=0)
    target = await run_hunter_shot(state, [hunter_player], broadcaster=...)
    assert target is None
```

- [ ] **Step 2: Check if fakes.py needs a broadcaster mock**

Read `backend/tests/fakes.py` to see if there's already a broadcaster mock pattern.

- [ ] **Step 3: Run tests**

Run: `python3 -m pytest backend/tests/test_hunter_shot.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_hunter_shot.py
git commit -m "test: add hunter_shot phase tests"
```

---

### Task 13: Integration — Verify full game runs for 6 and 9 players

**Files:**
- Modify: `backend/tests/test_full_game_ai_only.py` (if exists, otherwise create)

- [ ] **Step 1: Check if full game test exists and add 9-player variant**

- [ ] **Step 2: Run full game test for 6 players (existing)**

Run: `python3 -m pytest backend/tests/test_full_game_ai_only.py -v`
Expected: PASS

- [ ] **Step 3: Run all tests**

Run: `python3 -m pytest backend/tests/ -x -q`
Expected: all PASS

- [ ] **Step 4: Commit any final changes**

```bash
git add -A
git commit -m "test: add integration verification for 9-player game"
```