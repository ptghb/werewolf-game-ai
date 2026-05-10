# Werewolf AI 陪练游戏 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 React 前端 + Python FastAPI 后端的多人在线 6 人局狼人杀，AI 玩家通过 LangChain + 硅基流动 API 完整参与发言与决策，人机玩家通过 WebSocket 共享同一局。

**Architecture:** 后端权威，单房间 = 单 asyncio.Task 串行推进状态机；`Player` 抽象让 `HumanPlayer`（WS 驱动）和 `AIPlayer`（LangChain Agent 驱动）对游戏引擎透明。服务端按可见性过滤广播事件；AI 用 function calling 输出结构化动作、普通 chat 输出自然语言发言。

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, asyncio, LangChain, langchain-openai, Pydantic v2, pytest, pytest-asyncio / React 19, Vite, native WebSocket.

**Spec:** `docs/superpowers/specs/2026-05-10-werewolf-ai-design.md`

## File Structure

### Backend (`backend/`)

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | Dependencies, pytest config |
| `.env.example` | `SILICONFLOW_API_KEY`, `SILICONFLOW_BASE_URL`, `SILICONFLOW_MODEL` |
| `app/__init__.py` | Package marker |
| `app/main.py` | FastAPI app; mount `/ws` route, `/api/rooms` |
| `app/config.py` | Load env vars; expose `settings` |
| `app/protocol.py` | Pydantic schemas for ALL WS messages (client→server, server→client) |
| `app/rooms/room_manager.py` | `RoomManager` singleton, create/find/cleanup rooms |
| `app/rooms/room.py` | `Room` owns connections, dispatches client msgs into engine queue |
| `app/game/constants.py` | `Role`, `Phase`, `Channel` enums; timing constants |
| `app/game/state.py` | `GameState`, `PlayerState` dataclasses; witch potion tracker |
| `app/game/visibility.py` | Pure functions: given event + player, return whether visible |
| `app/game/win_check.py` | Pure function: `check_winner(state) -> Winner \| None` |
| `app/game/engine.py` | `GameEngine` owns state machine loop, calls phase handlers |
| `app/game/phases/night_wolf.py` | Wolves chat + vote; resolve kill target |
| `app/game/phases/night_seer.py` | Seer selects target, returns result privately |
| `app/game/phases/night_witch.py` | Witch save/poison/skip; apply effects |
| `app/game/phases/day_speech.py` | Round-table speeches in seat order |
| `app/game/phases/day_vote.py` | Simultaneous vote; PK on tie |
| `app/players/base.py` | `Player` Protocol + `ActionPrompt`, `ActionResponse` |
| `app/players/human.py` | `HumanPlayer` wraps WS; `request` via `asyncio.Future` |
| `app/players/ai.py` | `AIPlayer` wraps LangChain Agent |
| `app/ai/llm.py` | Build `ChatOpenAI` with SiliconFlow base_url |
| `app/ai/personas.py` | List of randomized personas (speech style) |
| `app/ai/prompts.py` | Role-specific system prompt templates |
| `app/ai/tools.py` | LangChain `@tool` definitions for each action |
| `tests/test_state_machine.py` | State transitions |
| `tests/test_visibility.py` | Event visibility matrix |
| `tests/test_win_check.py` | Winner decision |
| `tests/test_vote_tally.py` | Vote counting / ties / PK |
| `tests/test_full_game_ai_only.py` | Integration: fake AI players run to `game_over` |
| `tests/fakes.py` | `FakeAIPlayer`, `FakeHumanConn` deterministic doubles |

### Frontend (`frontend/`)

| File | Responsibility |
|------|----------------|
| `package.json`, `vite.config.js`, `index.html` | Vite scaffold |
| `src/main.jsx` | React entry |
| `src/App.jsx` | Routes Lobby ↔ Game by store state |
| `src/ws/client.js` | WS connect, seq tracking, auto-reconnect, event emitter |
| `src/store/gameStore.js` | Zustand store: room, players, phase, chat, my_role |
| `src/pages/Lobby.jsx` | Create/join room forms |
| `src/pages/Game.jsx` | Game layout: table + chat + action modal |
| `src/components/RoundTable.jsx` | Renders 6 seats in a circle |
| `src/components/PlayerSeat.jsx` | One seat (avatar, nickname, alive state) |
| `src/components/ChatPanel.jsx` | Day / wolf / dead channel tabs |
| `src/components/PhaseBanner.jsx` | Current phase + countdown |
| `src/components/ActionModal.jsx` | Prompts for vote/check/save/poison/speech |
| `src/components/RoleBadge.jsx` | Own role indicator (only self) |
| `src/components/SystemLog.jsx` | System announcements feed |
| `src/styles/theme.css` | Dark night + round table theme |

---

## Tasks

### Task 1: Project scaffold + pytest smoke

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_smoke.py`

- [ ] **Step 1: Write `backend/pyproject.toml`**

```toml
[project]
name = "werewolf-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.32",
  "websockets>=13",
  "pydantic>=2.9",
  "python-dotenv>=1.0",
  "langchain>=0.3",
  "langchain-openai>=0.2",
  "httpx>=0.27",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.24"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = ["llm: hits the real LLM (slow, requires API key)"]
```

- [ ] **Step 2: Write `backend/.env.example`**

```
SILICONFLOW_API_KEY=sk-your-key-here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct
```

- [ ] **Step 3: Create empty `backend/app/__init__.py` and `backend/tests/__init__.py`**

Both files empty.

- [ ] **Step 4: Write smoke test `backend/tests/test_smoke.py`**

```python
def test_python_works():
    assert 1 + 1 == 2
```

- [ ] **Step 5: Install deps and verify tests run**

```bash
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

Expected: 1 passed.

- [ ] **Step 6: Commit**

```bash
git init 2>/dev/null || true
git add backend/pyproject.toml backend/.env.example backend/app/__init__.py backend/tests/__init__.py backend/tests/test_smoke.py
git commit -m "chore: scaffold backend with pytest"
```

---


### Task 2: Core constants and enums

**Files:**
- Create: `backend/app/game/__init__.py`
- Create: `backend/app/game/constants.py`
- Create: `backend/tests/test_constants.py`

- [ ] **Step 1: Create `backend/app/game/__init__.py`**

Empty file.

- [ ] **Step 2: Write failing test `backend/tests/test_constants.py`**

```python
from app.game.constants import Role, Phase, Channel, SIX_PLAYER_ROLES

def test_roles_exist():
    assert Role.WEREWOLF
    assert Role.WITCH
    assert Role.SEER
    assert Role.VILLAGER

def test_six_player_roles_has_three_wolves_one_witch_one_seer_one_villager():
    counts = {r: SIX_PLAYER_ROLES.count(r) for r in set(SIX_PLAYER_ROLES)}
    assert len(SIX_PLAYER_ROLES) == 6
    assert counts[Role.WEREWOLF] == 3
    assert counts[Role.WITCH] == 1
    assert counts[Role.SEER] == 1
    assert counts[Role.VILLAGER] == 1

def test_phase_enum_has_all_phases():
    for name in ["LOBBY", "ROLE_ASSIGN", "NIGHT_START", "WOLF_KILL",
                 "SEER_CHECK", "WITCH_ACTION", "DAY_ANNOUNCE",
                 "DAY_SPEECH", "DAY_VOTE", "CHECK_WIN", "GAME_OVER"]:
        assert hasattr(Phase, name)

def test_channels_exist():
    for c in ["DAY", "WOLF", "DEAD"]:
        assert hasattr(Channel, c)
```

- [ ] **Step 3: Run test — expect fail**

```bash
cd backend && pytest tests/test_constants.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 4: Write `backend/app/game/constants.py`**

```python
from enum import Enum


class Role(str, Enum):
    WEREWOLF = "werewolf"
    WITCH = "witch"
    SEER = "seer"
    VILLAGER = "villager"


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
    CHECK_WIN = "check_win"
    GAME_OVER = "game_over"


class Channel(str, Enum):
    DAY = "day"
    WOLF = "wolf"
    DEAD = "dead"


SIX_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
    Role.WITCH, Role.SEER, Role.VILLAGER,
]

# Timing constants (seconds)
WOLF_KILL_TIMEOUT = 45
SEER_CHECK_TIMEOUT = 20
WITCH_ACTION_TIMEOUT = 25
SPEECH_PER_PLAYER_TIMEOUT = 60
DAY_VOTE_TIMEOUT = 30
LAST_WORDS_TIMEOUT = 30
RECONNECT_GRACE_SECONDS = 30
LLM_CALL_TIMEOUT = 30
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest tests/test_constants.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/game/__init__.py backend/app/game/constants.py backend/tests/test_constants.py
git commit -m "feat: add game constants and role/phase enums"
```

---


### Task 3: GameState and PlayerState dataclasses

**Files:**
- Create: `backend/app/game/state.py`
- Create: `backend/tests/test_state.py`

- [ ] **Step 1: Write failing test `backend/tests/test_state.py`**

```python
from app.game.constants import Role, Phase
from app.game.state import GameState, PlayerState, WitchPotions


def test_player_state_defaults():
    p = PlayerState(id="p1", nickname="Alice", role=Role.VILLAGER, is_ai=False, seat=0)
    assert p.alive is True
    assert p.used_last_words is False


def test_witch_potions_defaults():
    w = WitchPotions()
    assert w.save_left is True
    assert w.poison_left is True


def test_game_state_alive_and_by_role():
    ps = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=False, seat=i)
        for i, r in enumerate([Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                               Role.WITCH, Role.SEER, Role.VILLAGER])
    ]
    gs = GameState(room_code="ABC123", players=ps, phase=Phase.LOBBY)
    assert len(gs.alive_players()) == 6
    assert [p.id for p in gs.players_by_role(Role.WEREWOLF)] == ["p0", "p1", "p2"]
    ps[0].alive = False
    assert len(gs.alive_players()) == 5
    assert len(gs.alive_players_by_role(Role.WEREWOLF)) == 2


def test_game_state_get_by_id():
    ps = [PlayerState(id="p1", nickname="a", role=Role.VILLAGER, is_ai=False, seat=0)]
    gs = GameState(room_code="R", players=ps, phase=Phase.LOBBY)
    assert gs.get_player("p1") is ps[0]
    assert gs.get_player("missing") is None
```


- [ ] **Step 2: Run test — expect fail**

```bash
cd backend && pytest tests/test_state.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/state.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field

from app.game.constants import Role, Phase


@dataclass
class WitchPotions:
    save_left: bool = True
    poison_left: bool = True


@dataclass
class PlayerState:
    id: str
    nickname: str
    role: Role
    is_ai: bool
    seat: int
    alive: bool = True
    used_last_words: bool = False
    connected: bool = True


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

    def get_player(self, pid: str) -> PlayerState | None:
        for p in self.players:
            if p.id == pid:
                return p
        return None

    def alive_players(self) -> list[PlayerState]:
        return [p for p in self.players if p.alive]

    def players_by_role(self, role: Role) -> list[PlayerState]:
        return [p for p in self.players if p.role == role]

    def alive_players_by_role(self, role: Role) -> list[PlayerState]:
        return [p for p in self.players if p.alive and p.role == role]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_state.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/state.py backend/tests/test_state.py
git commit -m "feat: add GameState and PlayerState dataclasses"
```

---


### Task 4: Winner check (pure function)

**Files:**
- Create: `backend/app/game/win_check.py`
- Create: `backend/tests/test_win_check.py`

- [ ] **Step 1: Write failing test `backend/tests/test_win_check.py`**

```python
from app.game.constants import Role, Phase
from app.game.state import GameState, PlayerState
from app.game.win_check import check_winner, Winner


def _make_state(alive_roles: list[Role]) -> GameState:
    all_roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                 Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=False, seat=i)
        for i, r in enumerate(all_roles)
    ]
    # Mark alive subset
    counts = {r: 0 for r in set(all_roles)}
    for r in alive_roles:
        counts[r] = counts.get(r, 0) + 1
    # First reset all to dead, then revive `counts[r]` of each role
    for p in players:
        p.alive = False
    remaining = dict(counts)
    for p in players:
        if remaining.get(p.role, 0) > 0:
            p.alive = True
            remaining[p.role] -= 1
    return GameState(room_code="R", players=players, phase=Phase.CHECK_WIN)


def test_all_wolves_dead_good_wins():
    s = _make_state([Role.WITCH, Role.SEER, Role.VILLAGER])
    assert check_winner(s) == Winner.GOOD


def test_all_good_dead_wolves_win():
    s = _make_state([Role.WEREWOLF, Role.WEREWOLF])
    assert check_winner(s) == Winner.WEREWOLF


def test_mixed_still_alive_no_winner():
    s = _make_state([Role.WEREWOLF, Role.SEER, Role.VILLAGER])
    assert check_winner(s) is None


def test_wolves_plus_one_good_still_no_winner():
    # Witch and seer dead, only villager left, plus 1 wolf → good still has 1
    s = _make_state([Role.WEREWOLF, Role.VILLAGER])
    assert check_winner(s) is None
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_win_check.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/win_check.py`**

```python
from enum import Enum

from app.game.constants import Role
from app.game.state import GameState


class Winner(str, Enum):
    GOOD = "good"
    WEREWOLF = "werewolf"


def check_winner(state: GameState) -> Winner | None:
    alive_wolves = len(state.alive_players_by_role(Role.WEREWOLF))
    alive_good = sum(
        1 for p in state.alive_players() if p.role != Role.WEREWOLF
    )
    if alive_wolves == 0:
        return Winner.GOOD
    if alive_good == 0:
        return Winner.WEREWOLF
    return None
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_win_check.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/win_check.py backend/tests/test_win_check.py
git commit -m "feat: add win condition check"
```

---


### Task 5: Game events and visibility filter

**Files:**
- Create: `backend/app/game/events.py`
- Create: `backend/app/game/visibility.py`
- Create: `backend/tests/test_visibility.py`

- [ ] **Step 1: Write `backend/app/game/events.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.game.constants import Channel


@dataclass
class GameEvent:
    """Internal canonical event. Broadcaster decides who sees it."""
    type: str
    payload: dict[str, Any] = field(default_factory=dict)
    # Visibility hints — filled by producers:
    audience: str = "all"  # "all" | "role:werewolf" | "role:seer" | "role:witch" | "player:<id>" | "dead"
    channel: Channel | None = None
```

- [ ] **Step 2: Write failing test `backend/tests/test_visibility.py`**

```python
from app.game.constants import Role, Phase, Channel
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState
from app.game.visibility import is_visible_to


def _mk_state():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=False, seat=i)
        for i, r in enumerate(roles)
    ]
    return GameState(room_code="R", players=players, phase=Phase.LOBBY), players


def test_all_audience_visible_to_everyone():
    state, ps = _mk_state()
    ev = GameEvent(type="system_announce", payload={"text": "天黑请闭眼"}, audience="all")
    for p in ps:
        assert is_visible_to(ev, p, state)


def test_wolf_channel_only_to_wolves():
    state, ps = _mk_state()
    ev = GameEvent(type="chat_message", payload={"text": "kill p4"},
                   audience="role:werewolf", channel=Channel.WOLF)
    for p in ps:
        if p.role == Role.WEREWOLF:
            assert is_visible_to(ev, p, state)
        else:
            assert not is_visible_to(ev, p, state)


def test_seer_result_only_to_seer():
    state, ps = _mk_state()
    seer = next(p for p in ps if p.role == Role.SEER)
    ev = GameEvent(type="seer_result", payload={"target_id": "p0", "is_wolf": True},
                   audience=f"player:{seer.id}")
    for p in ps:
        assert is_visible_to(ev, p, state) == (p.id == seer.id)


def test_dead_channel_only_to_dead():
    state, ps = _mk_state()
    # kill p3 and p4
    ps[3].alive = False
    ps[4].alive = False
    ev = GameEvent(type="chat_message", payload={"text": "hi"},
                   audience="dead", channel=Channel.DEAD)
    for p in ps:
        assert is_visible_to(ev, p, state) == (not p.alive)
```

- [ ] **Step 3: Run test — expect fail**

```bash
pytest tests/test_visibility.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 4: Write `backend/app/game/visibility.py`**

```python
from app.game.constants import Role
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState


def is_visible_to(event: GameEvent, player: PlayerState, state: GameState) -> bool:
    aud = event.audience
    if aud == "all":
        return True
    if aud == "dead":
        return not player.alive
    if aud.startswith("role:"):
        role_name = aud.split(":", 1)[1]
        return player.role.value == role_name
    if aud.startswith("player:"):
        pid = aud.split(":", 1)[1]
        return player.id == pid
    return False


__all__ = ["is_visible_to"]
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest tests/test_visibility.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/game/events.py backend/app/game/visibility.py backend/tests/test_visibility.py
git commit -m "feat: add game events and visibility filter"
```

---


### Task 6: Vote tally helper

**Files:**
- Create: `backend/app/game/vote.py`
- Create: `backend/tests/test_vote_tally.py`

- [ ] **Step 1: Write failing test `backend/tests/test_vote_tally.py`**

```python
from app.game.vote import tally_votes, VoteResult


def test_majority_winner():
    votes = {"v1": "a", "v2": "a", "v3": "b"}
    r = tally_votes(votes)
    assert r.kind == "winner"
    assert r.winner == "a"
    assert r.tied_candidates == []


def test_abstain_excluded():
    votes = {"v1": "a", "v2": None, "v3": "a"}
    r = tally_votes(votes)
    assert r.kind == "winner"
    assert r.winner == "a"


def test_tie_two_candidates():
    votes = {"v1": "a", "v2": "b", "v3": "a", "v4": "b"}
    r = tally_votes(votes)
    assert r.kind == "tie"
    assert set(r.tied_candidates) == {"a", "b"}


def test_all_abstain():
    votes = {"v1": None, "v2": None}
    r = tally_votes(votes)
    assert r.kind == "no_vote"


def test_empty():
    r = tally_votes({})
    assert r.kind == "no_vote"
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_vote_tally.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/vote.py`**

```python
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class VoteResult:
    kind: Literal["winner", "tie", "no_vote"]
    winner: str | None = None
    tied_candidates: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)


def tally_votes(votes: dict[str, str | None]) -> VoteResult:
    counts = Counter(t for t in votes.values() if t is not None)
    if not counts:
        return VoteResult(kind="no_vote", counts={})
    top = counts.most_common()
    max_n = top[0][1]
    leaders = [c for c, n in top if n == max_n]
    if len(leaders) == 1:
        return VoteResult(kind="winner", winner=leaders[0], counts=dict(counts))
    return VoteResult(kind="tie", tied_candidates=leaders, counts=dict(counts))


__all__ = ["tally_votes", "VoteResult"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_vote_tally.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/vote.py backend/tests/test_vote_tally.py
git commit -m "feat: add vote tally helper with tie/abstain handling"
```

---


### Task 7: Player Protocol + ActionPrompt/Response

**Files:**
- Create: `backend/app/players/__init__.py`
- Create: `backend/app/players/base.py`
- Create: `backend/tests/test_player_base.py`

- [ ] **Step 1: Create `backend/app/players/__init__.py`**

Empty file.

- [ ] **Step 2: Write failing test `backend/tests/test_player_base.py`**

```python
from app.players.base import ActionPrompt, ActionResponse, Player


def test_action_prompt_fields():
    p = ActionPrompt(
        action="day_vote",
        options=["p1", "p2"],
        deadline_ts=123.0,
        hint="vote someone out",
    )
    assert p.action == "day_vote"
    assert p.options == ["p1", "p2"]
    assert p.deadline_ts == 123.0
    assert p.hint == "vote someone out"


def test_action_response_fields():
    r = ActionResponse(action="day_vote", target="p1")
    assert r.action == "day_vote"
    assert r.target == "p1"
    assert r.text is None


def test_player_protocol_is_runtime_checkable():
    # Minimal duck-typed fake should satisfy Player at runtime
    class Fake:
        id = "p1"
        nickname = "a"
        role = None
        alive = True
        is_ai = False
        async def request(self, prompt): ...
        async def notify(self, event): ...
    assert isinstance(Fake(), Player)
```

- [ ] **Step 3: Run test — expect fail**

```bash
pytest tests/test_player_base.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 4: Write `backend/app/players/base.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.game.constants import Role
from app.game.events import GameEvent


@dataclass
class ActionPrompt:
    action: str
    options: list[str] = field(default_factory=list)
    deadline_ts: float = 0.0
    hint: str = ""


@dataclass
class ActionResponse:
    action: str
    target: str | None = None
    text: str | None = None


@runtime_checkable
class Player(Protocol):
    id: str
    nickname: str
    role: Role
    alive: bool
    is_ai: bool

    async def request(self, prompt: ActionPrompt) -> ActionResponse: ...
    async def notify(self, event: GameEvent) -> None: ...


__all__ = ["ActionPrompt", "ActionResponse", "Player"]
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest tests/test_player_base.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/players/__init__.py backend/app/players/base.py backend/tests/test_player_base.py
git commit -m "feat: add Player protocol and action prompt/response"
```

---


### Task 8: Deterministic fakes for tests

**Files:**
- Create: `backend/tests/fakes.py`
- Create: `backend/tests/test_fakes.py`

- [ ] **Step 1: Write failing test `backend/tests/test_fakes.py`**

```python
import pytest

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, Player
from tests.fakes import FakeAIPlayer


@pytest.mark.asyncio
async def test_fake_ai_returns_scripted_response():
    fake = FakeAIPlayer(
        id="p1", nickname="a", role=Role.VILLAGER, seat=0,
        scripted={"day_vote": "p2"},
    )
    assert isinstance(fake, Player)
    resp = await fake.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target == "p2"


@pytest.mark.asyncio
async def test_fake_ai_defaults_to_first_option():
    fake = FakeAIPlayer(id="p1", nickname="a", role=Role.VILLAGER, seat=0)
    resp = await fake.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target == "p2"


@pytest.mark.asyncio
async def test_fake_ai_records_notifications():
    fake = FakeAIPlayer(id="p1", nickname="a", role=Role.VILLAGER, seat=0)
    await fake.notify(GameEvent(type="system_announce", payload={"text": "x"}))
    assert len(fake.received) == 1
    assert fake.received[0].type == "system_announce"
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_fakes.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/tests/fakes.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


@dataclass
class FakeAIPlayer:
    id: str
    nickname: str
    role: Role
    seat: int
    alive: bool = True
    is_ai: bool = True
    scripted: dict[str, str | None] = field(default_factory=dict)
    speech: str = "(silence)"
    received: list[GameEvent] = field(default_factory=list)

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        if prompt.action in ("speak", "speech", "last_words"):
            return ActionResponse(action=prompt.action, text=self.speech)
        if prompt.action in self.scripted:
            return ActionResponse(action=prompt.action, target=self.scripted[prompt.action])
        target = prompt.options[0] if prompt.options else None
        return ActionResponse(action=prompt.action, target=target)

    async def notify(self, event: GameEvent) -> None:
        self.received.append(event)
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_fakes.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/fakes.py backend/tests/test_fakes.py
git commit -m "test: add FakeAIPlayer deterministic double"
```

---


### Task 9: Role assignment (shuffle six roles to seats)

**Files:**
- Create: `backend/app/game/assign.py`
- Create: `backend/tests/test_assign.py`

- [ ] **Step 1: Write failing test `backend/tests/test_assign.py`**

```python
import random

from app.game.assign import assign_roles
from app.game.constants import Role, SIX_PLAYER_ROLES


def test_assign_produces_exact_six_roles():
    rng = random.Random(42)
    roles = assign_roles(6, rng=rng)
    assert len(roles) == 6
    assert sorted(roles) == sorted(SIX_PLAYER_ROLES)


def test_assign_deterministic_under_seed():
    r1 = assign_roles(6, rng=random.Random(1))
    r2 = assign_roles(6, rng=random.Random(1))
    assert r1 == r2


def test_assign_rejects_non_six():
    import pytest
    with pytest.raises(ValueError):
        assign_roles(7)
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_assign.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/assign.py`**

```python
from __future__ import annotations

import random

from app.game.constants import Role, SIX_PLAYER_ROLES


def assign_roles(n: int, rng: random.Random | None = None) -> list[Role]:
    if n != 6:
        raise ValueError(f"Only 6-player games supported, got {n}")
    rng = rng or random.Random()
    pool = list(SIX_PLAYER_ROLES)
    rng.shuffle(pool)
    return pool


__all__ = ["assign_roles"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_assign.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/assign.py backend/tests/test_assign.py
git commit -m "feat: add role assignment helper"
```

---


### Task 10: Broadcaster (filter + fanout)

**Files:**
- Create: `backend/app/game/broadcaster.py`
- Create: `backend/tests/test_broadcaster.py`

- [ ] **Step 1: Write failing test `backend/tests/test_broadcaster.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Channel, Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _state():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = [
        FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        for p in players
    ]
    return GameState(room_code="R", players=players, phase=Phase.LOBBY), fakes


@pytest.mark.asyncio
async def test_broadcast_all_goes_to_everyone():
    state, fakes = _state()
    b = Broadcaster(state, fakes)
    await b.broadcast(GameEvent(type="system_announce", payload={"text": "x"}))
    for f in fakes:
        assert len(f.received) == 1


@pytest.mark.asyncio
async def test_broadcast_wolf_channel_only_to_wolves():
    state, fakes = _state()
    b = Broadcaster(state, fakes)
    await b.broadcast(GameEvent(
        type="chat_message", payload={"text": "x"},
        audience="role:werewolf", channel=Channel.WOLF,
    ))
    for p, f in zip(state.players, fakes):
        if p.role == Role.WEREWOLF:
            assert len(f.received) == 1
        else:
            assert len(f.received) == 0


@pytest.mark.asyncio
async def test_broadcast_player_scoped():
    state, fakes = _state()
    b = Broadcaster(state, fakes)
    seer_id = next(p.id for p in state.players if p.role == Role.SEER)
    await b.broadcast(GameEvent(
        type="seer_result", payload={"target_id": "p0", "is_wolf": True},
        audience=f"player:{seer_id}",
    ))
    for p, f in zip(state.players, fakes):
        expected = 1 if p.id == seer_id else 0
        assert len(f.received) == expected
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_broadcaster.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/broadcaster.py`**

```python
from __future__ import annotations

import asyncio
from typing import Iterable

from app.game.events import GameEvent
from app.game.state import GameState
from app.game.visibility import is_visible_to
from app.players.base import Player


class Broadcaster:
    def __init__(self, state: GameState, players: Iterable[Player]):
        self.state = state
        self.players = list(players)

    async def broadcast(self, event: GameEvent) -> None:
        targets = [p for p in self.players
                   if is_visible_to(event, self.state.get_player(p.id), self.state)]
        if not targets:
            return
        await asyncio.gather(*(p.notify(event) for p in targets))


__all__ = ["Broadcaster"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_broadcaster.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/broadcaster.py backend/tests/test_broadcaster.py
git commit -m "feat: add broadcaster that filters events by visibility"
```

---


### Task 11: Night wolf phase (kill target resolution)

**Files:**
- Create: `backend/app/game/phases/__init__.py`
- Create: `backend/app/game/phases/night_wolf.py`
- Create: `backend/tests/test_phase_night_wolf.py`

- [ ] **Step 1: Create `backend/app/game/phases/__init__.py`**

Empty file.

- [ ] **Step 2: Write failing test `backend/tests/test_phase_night_wolf.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_wolf import run_wolf_kill
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(wolf_targets: list[str | None]):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    wolf_i = 0
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        if p.role == Role.WEREWOLF:
            f.scripted = {"wolf_vote": wolf_targets[wolf_i]}
            wolf_i += 1
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.WOLF_KILL)
    return state, fakes


@pytest.mark.asyncio
async def test_wolf_majority_picks_target():
    state, fakes = _setup(["p5", "p5", "p4"])
    b = Broadcaster(state, fakes)
    target = await run_wolf_kill(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert target == "p5"
    assert state.tonight_killed_by_wolves == "p5"


@pytest.mark.asyncio
async def test_wolf_tie_picks_one_of_tied():
    state, fakes = _setup(["p5", "p4", None])
    b = Broadcaster(state, fakes)
    target = await run_wolf_kill(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert target in {"p4", "p5"}


@pytest.mark.asyncio
async def test_wolf_all_abstain_no_kill():
    state, fakes = _setup([None, None, None])
    b = Broadcaster(state, fakes)
    target = await run_wolf_kill(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert target is None
    assert state.tonight_killed_by_wolves is None
```

- [ ] **Step 3: Run test — expect fail**

```bash
pytest tests/test_phase_night_wolf.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 4: Write `backend/app/game/phases/night_wolf.py`**

```python
from __future__ import annotations

import asyncio
import random
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


async def run_wolf_kill(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
    rng: random.Random | None = None,
) -> str | None:
    rng = rng or random.Random()
    state.phase = Phase.WOLF_KILL
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "wolf_kill", "deadline_ts": deadline_ts},
    ))
    wolves = [p for p in players if p.role == Role.WEREWOLF and p.alive]
    alive_non_wolf = [p for p in state.alive_players() if p.role != Role.WEREWOLF]
    options = [p.id for p in alive_non_wolf]
    prompts = [
        ActionPrompt(action="wolf_vote", options=options, deadline_ts=deadline_ts)
        for _ in wolves
    ]
    responses = await asyncio.gather(
        *(w.request(p) for w, p in zip(wolves, prompts))
    )
    votes = {w.id: (r.target if r.target in options else None)
             for w, r in zip(wolves, responses)}
    result = tally_votes(votes)
    if result.kind == "winner":
        target = result.winner
    elif result.kind == "tie":
        target = rng.choice(result.tied_candidates)
    else:
        target = None
    state.tonight_killed_by_wolves = target
    return target


__all__ = ["run_wolf_kill"]
```

- [ ] **Step 5: Run test — expect pass**

```bash
pytest tests/test_phase_night_wolf.py -v
```

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/game/phases/__init__.py backend/app/game/phases/night_wolf.py backend/tests/test_phase_night_wolf.py
git commit -m "feat: implement night wolf kill phase"
```

---


### Task 12: Night seer phase (check target, return result privately)

**Files:**
- Create: `backend/app/game/phases/night_seer.py`
- Create: `backend/tests/test_phase_night_seer.py`

- [ ] **Step 1: Write failing test `backend/tests/test_phase_night_seer.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_seer import run_seer_check
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(seer_target: str | None):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        if p.role == Role.SEER:
            f.scripted = {"seer_check": seer_target}
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.SEER_CHECK)
    return state, fakes


@pytest.mark.asyncio
async def test_seer_checks_wolf_gets_true():
    state, fakes = _setup("p0")  # p0 is wolf
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    results = [e for e in seer_fake.received if e.type == "seer_result"]
    assert len(results) == 1
    assert results[0].payload["target_id"] == "p0"
    assert results[0].payload["is_wolf"] is True


@pytest.mark.asyncio
async def test_seer_checks_villager_gets_false():
    state, fakes = _setup("p5")  # p5 is villager
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    results = [e for e in seer_fake.received if e.type == "seer_result"]
    assert results[0].payload["is_wolf"] is False


@pytest.mark.asyncio
async def test_seer_skip_no_result():
    state, fakes = _setup(None)
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    results = [e for e in seer_fake.received if e.type == "seer_result"]
    assert results == []


@pytest.mark.asyncio
async def test_seer_dead_is_noop():
    state, fakes = _setup("p0")
    seer_player = next(p for p in state.players if p.role == Role.SEER)
    seer_player.alive = False
    b = Broadcaster(state, fakes)
    await run_seer_check(state, fakes, broadcaster=b, deadline_ts=9999999999)
    # no crash; seer fake should get no seer_result
    seer_fake = next(f for f in fakes if f.role == Role.SEER)
    assert not any(e.type == "seer_result" for e in seer_fake.received)
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_phase_night_seer.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/phases/night_seer.py`**

```python
from __future__ import annotations

from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


async def run_seer_check(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> None:
    state.phase = Phase.SEER_CHECK
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "seer_check", "deadline_ts": deadline_ts},
    ))
    seer = next((p for p in players if p.role == Role.SEER and p.alive), None)
    if seer is None:
        return
    # Options: any alive player except self
    options = [p.id for p in state.alive_players() if p.id != seer.id]
    resp = await seer.request(ActionPrompt(
        action="seer_check", options=options, deadline_ts=deadline_ts,
    ))
    if resp.target is None or resp.target not in options:
        return  # skip
    target = state.get_player(resp.target)
    await seer.notify(GameEvent(
        type="seer_result",
        payload={"target_id": target.id, "is_wolf": target.role == Role.WEREWOLF},
        audience=f"player:{seer.id}",
    ))


__all__ = ["run_seer_check"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_phase_night_seer.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/phases/night_seer.py backend/tests/test_phase_night_seer.py
git commit -m "feat: implement seer night check"
```

---


### Task 13: Night witch phase (save / poison / skip)

**Files:**
- Create: `backend/app/game/phases/night_witch.py`
- Create: `backend/tests/test_phase_night_witch.py`

- [ ] **Step 1: Write failing test `backend/tests/test_phase_night_witch.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.night_witch import run_witch_action
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(scripted_action: str, target: str | None, killed_by_wolves: str | None = "p5"):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        if p.role == Role.WITCH:
            f.scripted = {scripted_action: target}
        fakes.append(f)
    state = GameState(room_code="R", players=players, phase=Phase.WITCH_ACTION)
    state.tonight_killed_by_wolves = killed_by_wolves
    return state, fakes


@pytest.mark.asyncio
async def test_witch_save_consumes_save_potion():
    state, fakes = _setup("witch_save", "p5")
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_saved_by_witch is True
    assert state.witch.save_left is False
    assert state.witch.poison_left is True


@pytest.mark.asyncio
async def test_witch_poison_consumes_poison_potion():
    state, fakes = _setup("witch_poison", "p0")
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.tonight_poisoned_by_witch == "p0"
    assert state.witch.poison_left is False
    assert state.witch.save_left is True


@pytest.mark.asyncio
async def test_witch_cannot_use_both_same_night():
    state, fakes = _setup("witch_save", "p5")
    # manually override the witch fake to try both via a custom response sequence
    witch_fake = next(f for f in fakes if f.role == Role.WITCH)
    # Script: first call → save target; if engine asks again, try poison — engine should not ask again
    witch_fake.scripted = {"witch_save": "p5", "witch_poison": "p0"}
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    # save was used → no poison applied
    assert state.tonight_saved_by_witch is True
    assert state.tonight_poisoned_by_witch is None


@pytest.mark.asyncio
async def test_witch_skip_leaves_potions():
    state, fakes = _setup("witch_skip", None)
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert state.witch.save_left is True
    assert state.witch.poison_left is True
    assert state.tonight_saved_by_witch is False
    assert state.tonight_poisoned_by_witch is None


@pytest.mark.asyncio
async def test_witch_gets_info_about_tonight_kill():
    state, fakes = _setup("witch_skip", None, killed_by_wolves="p5")
    b = Broadcaster(state, fakes)
    await run_witch_action(state, fakes, broadcaster=b, deadline_ts=9999999999)
    witch_fake = next(f for f in fakes if f.role == Role.WITCH)
    infos = [e for e in witch_fake.received if e.type == "witch_info"]
    assert len(infos) == 1
    assert infos[0].payload["tonight_killed"] == "p5"
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_phase_night_witch.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/phases/night_witch.py`**

```python
from __future__ import annotations

from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


async def run_witch_action(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> None:
    state.phase = Phase.WITCH_ACTION
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "witch_action", "deadline_ts": deadline_ts},
    ))
    witch = next((p for p in players if p.role == Role.WITCH and p.alive), None)
    if witch is None:
        return
    # Private info: who was killed tonight, potion remaining
    await witch.notify(GameEvent(
        type="witch_info",
        payload={
            "tonight_killed": state.tonight_killed_by_wolves,
            "save_left": state.witch.save_left,
            "poison_left": state.witch.poison_left,
        },
        audience=f"player:{witch.id}",
    ))
    # Single prompt: the witch picks one of save/poison/skip.
    # options: alive players for poison; "self" or killed-id for save target (kept as list for uniformity)
    options = [p.id for p in state.alive_players()]
    resp = await witch.request(ActionPrompt(
        action="witch_action", options=options, deadline_ts=deadline_ts,
        hint="Reply via witch_save/witch_poison/witch_skip",
    ))
    # Resolve one-of. Same-night both-potions is forbidden: first valid wins.
    if resp.action == "witch_save" and state.witch.save_left:
        if state.tonight_killed_by_wolves and resp.target == state.tonight_killed_by_wolves:
            state.tonight_saved_by_witch = True
            state.witch.save_left = False
            return
    if resp.action == "witch_poison" and state.witch.poison_left:
        if resp.target in options:
            state.tonight_poisoned_by_witch = resp.target
            state.witch.poison_left = False
            return
    # skip or invalid → no-op


__all__ = ["run_witch_action"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_phase_night_witch.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/phases/night_witch.py backend/tests/test_phase_night_witch.py
git commit -m "feat: implement witch night action with potion tracking"
```

---


### Task 14: Day announce — resolve night deaths + last words

**Files:**
- Create: `backend/app/game/phases/day_announce.py`
- Create: `backend/tests/test_phase_day_announce.py`

- [ ] **Step 1: Write failing test `backend/tests/test_phase_day_announce.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_announce import run_day_announce
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _state(killed: str | None, poisoned: str | None, saved: bool):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = [FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="bye")
             for p in players]
    s = GameState(room_code="R", players=players, phase=Phase.DAY_ANNOUNCE)
    s.tonight_killed_by_wolves = killed
    s.tonight_poisoned_by_witch = poisoned
    s.tonight_saved_by_witch = saved
    return s, fakes


@pytest.mark.asyncio
async def test_wolf_kill_unsaved_dies():
    s, fakes = _state("p5", None, False)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert dead == ["p5"]
    assert s.get_player("p5").alive is False


@pytest.mark.asyncio
async def test_wolf_kill_saved_nobody_dies():
    s, fakes = _state("p5", None, True)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert dead == []
    assert s.get_player("p5").alive is True


@pytest.mark.asyncio
async def test_wolf_and_poison_both_die():
    s, fakes = _state("p5", "p0", False)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert set(dead) == {"p5", "p0"}


@pytest.mark.asyncio
async def test_peaceful_night():
    s, fakes = _state(None, None, False)
    b = Broadcaster(s, fakes)
    dead = await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert dead == []


@pytest.mark.asyncio
async def test_night_counters_reset_after_announce():
    s, fakes = _state("p5", None, False)
    b = Broadcaster(s, fakes)
    await run_day_announce(s, fakes, broadcaster=b, deadline_ts=9999999999)
    assert s.tonight_killed_by_wolves is None
    assert s.tonight_poisoned_by_witch is None
    assert s.tonight_saved_by_witch is False
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_phase_day_announce.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/phases/day_announce.py`**

```python
from __future__ import annotations

import asyncio
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


async def run_day_announce(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> list[str]:
    state.phase = Phase.DAY_ANNOUNCE
    state.day_number += 1
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "day_announce", "day": state.day_number,
                                      "deadline_ts": deadline_ts},
    ))
    dead_ids: list[str] = []
    killed = state.tonight_killed_by_wolves
    if killed and not state.tonight_saved_by_witch:
        dead_ids.append(killed)
    poisoned = state.tonight_poisoned_by_witch
    if poisoned and poisoned != killed:
        dead_ids.append(poisoned)

    for pid in dead_ids:
        p = state.get_player(pid)
        if p and p.alive:
            p.alive = False

    await broadcaster.broadcast(GameEvent(
        type="death_announce",
        payload={"dead": dead_ids, "reason": "night" if dead_ids else "peaceful"},
    ))

    # Last words sequentially (keeps chat linear)
    lookup = {p.id: p for p in players}
    for pid in dead_ids:
        player = lookup.get(pid)
        if player is None:
            continue
        resp = await player.request(ActionPrompt(
            action="last_words", deadline_ts=deadline_ts,
            hint="Your final words (<=80 chars)",
        ))
        text = (resp.text or "").strip()
        if text:
            await broadcaster.broadcast(GameEvent(
                type="chat_message",
                payload={"from": pid, "text": text, "channel": "day", "last_words": True},
            ))
        state.get_player(pid).used_last_words = True

    # Reset night counters
    state.tonight_killed_by_wolves = None
    state.tonight_poisoned_by_witch = None
    state.tonight_saved_by_witch = False
    return dead_ids


__all__ = ["run_day_announce"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_phase_day_announce.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/phases/day_announce.py backend/tests/test_phase_day_announce.py
git commit -m "feat: implement day announce with death resolution and last words"
```

---


### Task 15: Day speech — round-table speeches in seat order

**Files:**
- Create: `backend/app/game/phases/day_speech.py`
- Create: `backend/tests/test_phase_day_speech.py`

- [ ] **Step 1: Write failing test `backend/tests/test_phase_day_speech.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_speech import run_day_speech
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(speeches: dict[str, str]):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        f.speech = speeches.get(p.id, "(silence)")
        fakes.append(f)
    return GameState(room_code="R", players=players, phase=Phase.DAY_SPEECH), fakes


@pytest.mark.asyncio
async def test_all_alive_speak_in_seat_order_starting_from_start_id():
    speeches = {f"p{i}": f"s{i}" for i in range(6)}
    state, fakes = _setup(speeches)
    b = Broadcaster(state, fakes)
    order = await run_day_speech(state, fakes, broadcaster=b,
                                 start_player_id="p2", per_player_timeout=5)
    assert order == ["p2", "p3", "p4", "p5", "p0", "p1"]


@pytest.mark.asyncio
async def test_dead_players_skipped():
    speeches = {f"p{i}": f"s{i}" for i in range(6)}
    state, fakes = _setup(speeches)
    state.get_player("p3").alive = False
    state.get_player("p5").alive = False
    b = Broadcaster(state, fakes)
    order = await run_day_speech(state, fakes, broadcaster=b,
                                 start_player_id="p2", per_player_timeout=5)
    assert order == ["p2", "p4", "p0", "p1"]


@pytest.mark.asyncio
async def test_empty_speech_skipped_in_broadcast():
    speeches = {"p0": "hello", "p1": "", "p2": "hi"}
    state, fakes = _setup(speeches)
    # Mark only these 3 alive for simplicity
    for p in state.players:
        p.alive = p.id in {"p0", "p1", "p2"}
    b = Broadcaster(state, fakes)
    await run_day_speech(state, fakes, broadcaster=b,
                        start_player_id="p0", per_player_timeout=5)
    # All alive players should receive p0 and p2 chat; p1's empty speech filtered
    some_fake = fakes[0]
    texts = [e.payload.get("text") for e in some_fake.received if e.type == "chat_message"]
    assert "hello" in texts
    assert "hi" in texts
    assert "" not in texts
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_phase_day_speech.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/phases/day_speech.py`**

```python
from __future__ import annotations

import time
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.players.base import ActionPrompt, Player


async def run_day_speech(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    start_player_id: str,
    per_player_timeout: int,
) -> list[str]:
    state.phase = Phase.DAY_SPEECH
    player_lookup = {p.id: p for p in players}
    # Build speaking order: seat-wise from start_player, only alive
    alive = sorted(state.alive_players(), key=lambda p: p.seat)
    if not alive:
        return []
    ids_in_seat_order = [p.id for p in alive]
    try:
        start_idx = ids_in_seat_order.index(start_player_id)
    except ValueError:
        # start player dead — begin from next seat
        seats = [p.seat for p in alive]
        start_seat = state.get_player(start_player_id).seat if state.get_player(start_player_id) else 0
        start_idx = next((i for i, s in enumerate(seats) if s >= start_seat), 0)
    order = ids_in_seat_order[start_idx:] + ids_in_seat_order[:start_idx]

    await broadcaster.broadcast(GameEvent(
        type="phase_change",
        payload={"phase": "day_speech", "order": order,
                 "per_player_timeout": per_player_timeout},
    ))

    for pid in order:
        speaker = player_lookup.get(pid)
        if speaker is None:
            continue
        await broadcaster.broadcast(GameEvent(
            type="speech_turn", payload={"speaker": pid},
        ))
        resp = await speaker.request(ActionPrompt(
            action="speech",
            deadline_ts=time.time() + per_player_timeout,
            hint=f"Your speech (<=80 chars)",
        ))
        text = (resp.text or "").strip()
        if text:
            await broadcaster.broadcast(GameEvent(
                type="chat_message",
                payload={"from": pid, "text": text, "channel": "day"},
            ))
    return order


__all__ = ["run_day_speech"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_phase_day_speech.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/phases/day_speech.py backend/tests/test_phase_day_speech.py
git commit -m "feat: implement day speech round-table in seat order"
```

---


### Task 16: Day vote with PK tie-break

**Files:**
- Create: `backend/app/game/phases/day_vote.py`
- Create: `backend/tests/test_phase_day_vote.py`

- [ ] **Step 1: Write failing test `backend/tests/test_phase_day_vote.py`**

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_vote import run_day_vote
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


def _setup(vote_scripts: dict[str, str | None], pk_scripts: dict[str, str | None] | None = None):
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    fakes = []
    for p in players:
        f = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="pk")
        scripts: dict[str, str | None] = {}
        if p.id in vote_scripts:
            scripts["day_vote"] = vote_scripts[p.id]
        if pk_scripts and p.id in pk_scripts:
            scripts["day_vote_pk"] = pk_scripts[p.id]
        f.scripted = scripts
        fakes.append(f)
    return GameState(room_code="R", players=players, phase=Phase.DAY_VOTE), fakes


@pytest.mark.asyncio
async def test_majority_vote_eliminates():
    votes = {"p0": "p5", "p1": "p5", "p2": "p4", "p3": "p5", "p4": "p5", "p5": "p0"}
    state, fakes = _setup(votes)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] == "p5"
    assert state.get_player("p5").alive is False


@pytest.mark.asyncio
async def test_tie_goes_to_pk_then_resolves():
    # Round 1: p4 vs p5 tied 3-3
    votes = {"p0": "p4", "p1": "p4", "p2": "p4",
             "p3": "p5", "p4": "p5", "p5": "p5"}
    pk = {"p0": "p4", "p1": "p4", "p2": "p4",
          "p3": "p5", "p4": "p4", "p5": "p5"}  # p4 now 4, p5 now 2
    state, fakes = _setup(votes, pk)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] == "p4"
    assert result["pk_used"] is True


@pytest.mark.asyncio
async def test_double_tie_nobody_out():
    votes = {"p0": "p4", "p1": "p4", "p2": "p4",
             "p3": "p5", "p4": "p5", "p5": "p5"}
    pk = dict(votes)  # same tie again
    state, fakes = _setup(votes, pk)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] is None
    for p in state.players:
        assert p.alive


@pytest.mark.asyncio
async def test_abstain_not_counted():
    votes = {"p0": None, "p1": None, "p2": None,
             "p3": None, "p4": None, "p5": None}
    state, fakes = _setup(votes)
    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    assert result["eliminated"] is None


@pytest.mark.asyncio
async def test_eliminated_player_gets_last_words():
    votes = {"p0": "p5", "p1": "p5", "p2": "p5",
             "p3": "p5", "p4": "p5", "p5": "p0"}
    state, fakes = _setup(votes)
    p5_fake = next(f for f in fakes if f.id == "p5")
    p5_fake.speech = "farewell"
    b = Broadcaster(state, fakes)
    await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)
    # p0 fake should have received p5's last words broadcast
    p0_fake = next(f for f in fakes if f.id == "p0")
    chats = [e for e in p0_fake.received if e.type == "chat_message"
             and e.payload.get("from") == "p5"]
    assert any(c.payload.get("text") == "farewell" for c in chats)
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_phase_day_vote.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/phases/day_vote.py`**

```python
from __future__ import annotations

import asyncio
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase
from app.game.events import GameEvent
from app.game.state import GameState
from app.game.vote import tally_votes
from app.players.base import ActionPrompt, Player


async def _collect_votes(
    voters,
    options: list[str],
    action_name: str,
    deadline_ts: float,
) -> dict[str, str | None]:
    prompts = [
        ActionPrompt(action=action_name, options=options, deadline_ts=deadline_ts)
        for _ in voters
    ]
    responses = await asyncio.gather(*(v.request(p) for v, p in zip(voters, prompts)))
    return {
        v.id: (r.target if r.target in options else None)
        for v, r in zip(voters, responses)
    }


async def run_day_vote(
    state: GameState,
    players: Iterable[Player],
    *,
    broadcaster: Broadcaster,
    deadline_ts: float,
) -> dict:
    state.phase = Phase.DAY_VOTE
    await broadcaster.broadcast(GameEvent(
        type="phase_change", payload={"phase": "day_vote", "deadline_ts": deadline_ts},
    ))
    player_lookup = {p.id: p for p in players}
    alive_ids = [p.id for p in state.alive_players()]
    voters = [player_lookup[pid] for pid in alive_ids]

    votes = await _collect_votes(voters, alive_ids, "day_vote", deadline_ts)
    state.last_vote_tally = {k: v for k, v in votes.items() if v is not None}
    await broadcaster.broadcast(GameEvent(
        type="vote_tally", payload={"votes": votes, "round": 1},
    ))
    result = tally_votes(votes)
    eliminated: str | None = None
    pk_used = False

    if result.kind == "winner":
        eliminated = result.winner
    elif result.kind == "tie":
        pk_used = True
        candidates = result.tied_candidates
        await broadcaster.broadcast(GameEvent(
            type="pk_round", payload={"candidates": candidates},
        ))
        pk_votes = await _collect_votes(voters, candidates, "day_vote_pk", deadline_ts)
        await broadcaster.broadcast(GameEvent(
            type="vote_tally", payload={"votes": pk_votes, "round": 2},
        ))
        pk_result = tally_votes(pk_votes)
        if pk_result.kind == "winner":
            eliminated = pk_result.winner

    if eliminated:
        victim = state.get_player(eliminated)
        victim.alive = False
        await broadcaster.broadcast(GameEvent(
            type="death_announce",
            payload={"dead": [eliminated], "reason": "vote"},
        ))
        # last words
        speaker = player_lookup.get(eliminated)
        if speaker is not None:
            resp = await speaker.request(ActionPrompt(
                action="last_words", deadline_ts=deadline_ts,
                hint="Your final words (<=80 chars)",
            ))
            text = (resp.text or "").strip()
            if text:
                await broadcaster.broadcast(GameEvent(
                    type="chat_message",
                    payload={"from": eliminated, "text": text, "channel": "day",
                             "last_words": True},
                ))
            victim.used_last_words = True
    return {"eliminated": eliminated, "pk_used": pk_used, "votes": votes}


__all__ = ["run_day_vote"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_phase_day_vote.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/phases/day_vote.py backend/tests/test_phase_day_vote.py
git commit -m "feat: implement day vote with PK tie-break"
```

---


### Task 17: GameEngine — state machine loop

**Files:**
- Create: `backend/app/game/engine.py`
- Create: `backend/tests/test_state_machine.py`

- [ ] **Step 1: Write failing test `backend/tests/test_state_machine.py`**

```python
import pytest

from app.game.constants import Phase, Role
from app.game.engine import GameEngine
from tests.fakes import FakeAIPlayer


def _make_players():
    # 3 wolves vote p5; seer skips; witch skips → p5 dies night 1.
    specs = [
        ("p0", Role.WEREWOLF, {"wolf_vote": "p5"}),
        ("p1", Role.WEREWOLF, {"wolf_vote": "p5"}),
        ("p2", Role.WEREWOLF, {"wolf_vote": "p5"}),
        ("p3", Role.WITCH, {"witch_skip": None}),
        ("p4", Role.SEER, {"seer_skip": None}),
        ("p5", Role.VILLAGER, {}),
    ]
    return [
        FakeAIPlayer(id=i, nickname=i, role=r, seat=idx, scripted=sc, speech="...")
        for idx, (i, r, sc) in enumerate(specs)
    ]


@pytest.mark.asyncio
async def test_single_night_day_cycle_transitions_phases_in_order():
    players = _make_players()
    # Day vote: everyone votes p0 (a wolf) → p0 out
    for f in players:
        f.scripted["day_vote"] = "p0"
    engine = GameEngine(room_code="R", players=players, start_player_id="p0",
                       phase_timeouts={"wolf_kill": 1, "seer_check": 1, "witch_action": 1,
                                       "day_announce": 1, "day_speech": 1, "day_vote": 1,
                                       "last_words": 1})
    await engine.run_one_round()
    assert engine.state.phase in (Phase.CHECK_WIN, Phase.GAME_OVER, Phase.DAY_VOTE)
    # At minimum: p5 should be dead (wolves killed, no save)
    assert engine.state.get_player("p5").alive is False
    # p0 eliminated by day vote
    assert engine.state.get_player("p0").alive is False


@pytest.mark.asyncio
async def test_game_ends_when_all_wolves_dead():
    players = _make_players()
    # Force all wolves dead before running
    for pid in ("p0", "p1", "p2"):
        # The engine reads alive from state; we set it up via assign
        pass
    engine = GameEngine(room_code="R", players=players, start_player_id="p0",
                       phase_timeouts={k: 1 for k in [
                           "wolf_kill","seer_check","witch_action",
                           "day_announce","day_speech","day_vote","last_words"]})
    for pid in ("p0", "p1", "p2"):
        engine.state.get_player(pid).alive = False
    await engine.run_until_game_over()
    assert engine.state.phase == Phase.GAME_OVER
    assert engine.winner == "good"


@pytest.mark.asyncio
async def test_game_ends_when_all_good_dead():
    players = _make_players()
    engine = GameEngine(room_code="R", players=players, start_player_id="p0",
                       phase_timeouts={k: 1 for k in [
                           "wolf_kill","seer_check","witch_action",
                           "day_announce","day_speech","day_vote","last_words"]})
    for pid in ("p3", "p4", "p5"):
        engine.state.get_player(pid).alive = False
    await engine.run_until_game_over()
    assert engine.state.phase == Phase.GAME_OVER
    assert engine.winner == "werewolf"
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_state_machine.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/game/engine.py`**

```python
from __future__ import annotations

import random
import time
from typing import Iterable

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.events import GameEvent
from app.game.phases.day_announce import run_day_announce
from app.game.phases.day_speech import run_day_speech
from app.game.phases.day_vote import run_day_vote
from app.game.phases.night_seer import run_seer_check
from app.game.phases.night_witch import run_witch_action
from app.game.phases.night_wolf import run_wolf_kill
from app.game.state import GameState, PlayerState
from app.game.win_check import check_winner
from app.players.base import Player


DEFAULT_TIMEOUTS = {
    "wolf_kill": 45,
    "seer_check": 20,
    "witch_action": 25,
    "day_announce": 5,
    "day_speech": 60,  # per player
    "day_vote": 30,
    "last_words": 30,
}


class GameEngine:
    def __init__(
        self,
        room_code: str,
        players: Iterable[Player],
        *,
        start_player_id: str | None = None,
        phase_timeouts: dict[str, int] | None = None,
        rng: random.Random | None = None,
    ):
        self.players = list(players)
        self.rng = rng or random.Random()
        self.phase_timeouts = {**DEFAULT_TIMEOUTS, **(phase_timeouts or {})}
        player_states = [
            PlayerState(id=p.id, nickname=p.nickname, role=p.role,
                        is_ai=p.is_ai, seat=getattr(p, "seat", idx))
            for idx, p in enumerate(self.players)
        ]
        self.state = GameState(room_code=room_code, players=player_states, phase=Phase.LOBBY)
        self.broadcaster = Broadcaster(self.state, self.players)
        self.start_player_id = start_player_id or player_states[0].id
        self.winner: str | None = None

    def _now(self) -> float:
        return time.time()

    def _deadline(self, key: str) -> float:
        return self._now() + self.phase_timeouts[key]

    async def run_one_round(self) -> None:
        # NIGHT_START
        self.state.phase = Phase.NIGHT_START
        await self.broadcaster.broadcast(GameEvent(
            type="system_announce", payload={"text": "天黑请闭眼"}))

        await run_wolf_kill(self.state, self.players, broadcaster=self.broadcaster,
                            deadline_ts=self._deadline("wolf_kill"), rng=self.rng)
        await run_seer_check(self.state, self.players, broadcaster=self.broadcaster,
                             deadline_ts=self._deadline("seer_check"))
        await run_witch_action(self.state, self.players, broadcaster=self.broadcaster,
                               deadline_ts=self._deadline("witch_action"))

        # DAY_ANNOUNCE
        await run_day_announce(self.state, self.players, broadcaster=self.broadcaster,
                               deadline_ts=self._deadline("day_announce"))
        if self._resolve_winner(): return

        # Pick starting speaker: for day 1, fixed start_player_id; otherwise random alive
        alive_ids = [p.id for p in self.state.alive_players()]
        if self.state.day_number == 1 and self.start_player_id in alive_ids:
            start = self.start_player_id
        else:
            start = self.rng.choice(alive_ids) if alive_ids else self.start_player_id

        await run_day_speech(self.state, self.players, broadcaster=self.broadcaster,
                             start_player_id=start,
                             per_player_timeout=self.phase_timeouts["day_speech"])

        await run_day_vote(self.state, self.players, broadcaster=self.broadcaster,
                           deadline_ts=self._deadline("day_vote"))
        self._resolve_winner()

    def _resolve_winner(self) -> bool:
        self.state.phase = Phase.CHECK_WIN
        w = check_winner(self.state)
        if w is None:
            return False
        self.winner = w.value
        self.state.phase = Phase.GAME_OVER
        return True

    async def run_until_game_over(self, max_rounds: int = 20) -> None:
        if self._resolve_winner():
            await self._broadcast_game_over()
            return
        for _ in range(max_rounds):
            await self.run_one_round()
            if self.state.phase == Phase.GAME_OVER:
                break
        await self._broadcast_game_over()

    async def _broadcast_game_over(self) -> None:
        await self.broadcaster.broadcast(GameEvent(
            type="game_over",
            payload={
                "winner": self.winner,
                "roles": {p.id: p.role.value for p in self.state.players},
            },
        ))


__all__ = ["GameEngine"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_state_machine.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/game/engine.py backend/tests/test_state_machine.py
git commit -m "feat: implement GameEngine state machine loop"
```

---


### Task 18: Full-game integration test (all FakeAI)

**Files:**
- Create: `backend/tests/test_full_game_ai_only.py`

- [ ] **Step 1: Write test `backend/tests/test_full_game_ai_only.py`**

```python
import pytest

from app.game.constants import Phase, Role
from app.game.engine import GameEngine
from tests.fakes import FakeAIPlayer


@pytest.mark.asyncio
async def test_all_fake_ai_game_runs_to_game_over():
    # Wolves always try to kill villager, vote for seer; good players vote for a wolf
    specs = [
        ("p0", Role.WEREWOLF,
         {"wolf_vote": "p5", "day_vote": "p4", "day_vote_pk": "p4"}),
        ("p1", Role.WEREWOLF,
         {"wolf_vote": "p5", "day_vote": "p4", "day_vote_pk": "p4"}),
        ("p2", Role.WEREWOLF,
         {"wolf_vote": "p5", "day_vote": "p4", "day_vote_pk": "p4"}),
        ("p3", Role.WITCH,
         {"witch_skip": None, "day_vote": "p0", "day_vote_pk": "p0"}),
        ("p4", Role.SEER,
         {"seer_check": "p0", "day_vote": "p0", "day_vote_pk": "p0"}),
        ("p5", Role.VILLAGER,
         {"day_vote": "p0", "day_vote_pk": "p0"}),
    ]
    players = [
        FakeAIPlayer(id=pid, nickname=pid, role=role, seat=idx, scripted=sc, speech="...")
        for idx, (pid, role, sc) in enumerate(specs)
    ]
    engine = GameEngine(
        room_code="IT",
        players=players,
        start_player_id="p0",
        phase_timeouts={k: 1 for k in [
            "wolf_kill", "seer_check", "witch_action",
            "day_announce", "day_speech", "day_vote", "last_words",
        ]},
    )
    await engine.run_until_game_over(max_rounds=10)
    assert engine.state.phase == Phase.GAME_OVER
    assert engine.winner in {"good", "werewolf"}
    # Every fake received at least the final game_over event
    for f in players:
        assert any(e.type == "game_over" for e in f.received)


@pytest.mark.asyncio
async def test_witch_save_prevents_night_death():
    specs = [
        ("p0", Role.WEREWOLF, {"wolf_vote": "p5", "day_vote": None}),
        ("p1", Role.WEREWOLF, {"wolf_vote": "p5", "day_vote": None}),
        ("p2", Role.WEREWOLF, {"wolf_vote": "p5", "day_vote": None}),
        ("p3", Role.WITCH, {"witch_save": "p5", "day_vote": None}),
        ("p4", Role.SEER, {"seer_skip": None, "day_vote": None}),
        ("p5", Role.VILLAGER, {"day_vote": None}),
    ]
    players = [
        FakeAIPlayer(id=pid, nickname=pid, role=role, seat=idx, scripted=sc, speech="...")
        for idx, (pid, role, sc) in enumerate(specs)
    ]
    engine = GameEngine(
        room_code="IT2", players=players, start_player_id="p0",
        phase_timeouts={k: 1 for k in [
            "wolf_kill","seer_check","witch_action",
            "day_announce","day_speech","day_vote","last_words"]},
    )
    await engine.run_one_round()
    # After one round: p5 should still be alive (witch saved), no vote-out either
    assert engine.state.get_player("p5").alive is True
```

- [ ] **Step 2: Run test — expect pass**

```bash
pytest tests/test_full_game_ai_only.py -v
```

Expected: 2 passed.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_full_game_ai_only.py
git commit -m "test: full-game integration with deterministic FakeAI players"
```

---


### Task 19: AI — LLM client, personas, prompts scaffolding

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/ai/__init__.py`
- Create: `backend/app/ai/llm.py`
- Create: `backend/app/ai/personas.py`
- Create: `backend/app/ai/prompts.py`
- Create: `backend/tests/test_ai_config.py`

- [ ] **Step 1: Write failing test `backend/tests/test_ai_config.py`**

```python
import os

import pytest


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_[API Key_2]")
    monkeypatch.setenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    from importlib import reload

    from app import config
    reload(config)
    assert config.settings.api_key == "XYZ"
    assert config.settings.base_url == "https://api.siliconflow.cn/v1"
    assert config.settings.model == "Qwen/Qwen2.5-7B-Instruct"


def test_build_llm_uses_settings(monkeypatch):
    monkeypatch.setenv("SILICONFLOW_[API Key_3]")
    monkeypatch.setenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    from importlib import reload

    from app import config as config_mod
    from app.ai import llm as llm_mod
    reload(config_mod)
    reload(llm_mod)
    llm = llm_mod.build_llm()
    # ChatOpenAI keeps these attributes on the bound instance
    assert str(llm.openai_api_base).rstrip("/").endswith("/v1")
    assert llm.model_name == "Qwen/Qwen2.5-7B-Instruct"


def test_personas_non_empty():
    from app.ai.personas import PERSONAS, random_persona
    assert len(PERSONAS) >= 6
    p = random_persona(seed=1)
    assert p.name and p.style


def test_role_system_prompt_contains_role():
    from app.ai.prompts import build_system_prompt
    from app.game.constants import Role
    from app.ai.personas import Persona

    persona = Persona(name="A", style="calm")
    prompt = build_system_prompt(role=Role.SEER, persona=persona,
                                 wolf_teammates=[])
    assert "预言家" in prompt or "seer" in prompt.lower()
    assert "calm" in prompt.lower() or "A" in prompt
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_ai_config.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/config.py`**

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    api_key: str
    base_url: str
    model: str


settings = Settings(
    api_key=os.getenv("SILICONFLOW_API_KEY", ""),
    base_url=os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"),
    model=os.getenv("SILICONFLOW_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
)
```

- [ ] **Step 4: Write `backend/app/ai/__init__.py`**

Empty file.

- [ ] **Step 5: Write `backend/app/ai/llm.py`**

```python
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.config import settings
from app.game.constants import LLM_CALL_TIMEOUT


def build_llm(model: str | None = None, temperature: float = 0.8) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or settings.model,
        temperature=temperature,
        api_key=settings.api_key or "dummy",
        base_url=settings.base_url,
        timeout=LLM_CALL_TIMEOUT,
        max_retries=0,
    )


__all__ = ["build_llm"]
```

- [ ] **Step 6: Write `backend/app/ai/personas.py`**

```python
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    style: str


PERSONAS: list[Persona] = [
    Persona("理性派", "calm, analytical, cites timeline and vote logic"),
    Persona("活泼派", "energetic, uses humor and casual tone"),
    Persona("话少派", "terse, speaks in short declarative sentences"),
    Persona("冲锋派", "aggressive, pushes bold claims early"),
    Persona("和事佬", "diplomatic, avoids commitments, summarizes others"),
    Persona("玄学派", "intuitive, references feelings and impressions"),
    Persona("推理狂", "over-detailed, long chains of suspicion"),
    Persona("摸鱼党", "low-effort speeches, often agrees with last speaker"),
]


def random_persona(seed: int | None = None) -> Persona:
    rng = random.Random(seed)
    return rng.choice(PERSONAS)


__all__ = ["Persona", "PERSONAS", "random_persona"]
```

- [ ] **Step 7: Write `backend/app/ai/prompts.py`**

```python
from __future__ import annotations

from app.ai.personas import Persona
from app.game.constants import Role


ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.WEREWOLF: "你是狼人。夜间你和狼队友一起决定击杀目标；白天要伪装好人，避免被投出。",
    Role.SEER: "你是预言家（好人阵营）。夜间每晚查验一名玩家的身份；白天要利用信息引导好人投票。",
    Role.WITCH: "你是女巫（好人阵营）。你有救药和毒药各 1 瓶（全局计数），同一夜不能同时使用两瓶。",
    Role.VILLAGER: "你是平民（好人阵营）。你无特殊技能，依靠推理和发言引导投票。",
}


RULES_SUMMARY = """
游戏规则：6 人局（3 狼人 + 1 女巫 + 1 预言家 + 1 平民）。
夜间：狼人共刀 → 预言家查验 → 女巫决定救/毒/跳。
白天：公布死讯 → 轮流发言 → 全员投票（平票则 PK，再平无人出局）。
胜负：所有狼人死 → 好人胜；好人（女巫+预言家+平民）全死 → 狼人胜。
""".strip()


def build_system_prompt(
    role: Role,
    persona: Persona,
    wolf_teammates: list[str],
) -> str:
    teammate_line = ""
    if role == Role.WEREWOLF and wolf_teammates:
        teammate_line = f"\n你的狼队友 id：{', '.join(wolf_teammates)}。"
    return (
        f"{RULES_SUMMARY}\n\n"
        f"{ROLE_DESCRIPTIONS[role]}{teammate_line}\n\n"
        f"你的人设：{persona.name} — {persona.style}。\n"
        f"发言时严格控制在 80 汉字以内；保持人设一致。"
    )


__all__ = ["build_system_prompt", "ROLE_DESCRIPTIONS", "RULES_SUMMARY"]
```

- [ ] **Step 8: Run test — expect pass**

```bash
pytest tests/test_ai_config.py -v
```

Expected: 4 passed.

- [ ] **Step 9: Commit**

```bash
git add backend/app/config.py backend/app/ai/__init__.py backend/app/ai/llm.py backend/app/ai/personas.py backend/app/ai/prompts.py backend/tests/test_ai_config.py
git commit -m "feat: add AI config, LLM client, personas and role prompts"
```

---


### Task 20: AI tool schemas (LangChain function-calling)

**Files:**
- Create: `backend/app/ai/tools.py`
- Create: `backend/tests/test_ai_tools.py`

- [ ] **Step 1: Write failing test `backend/tests/test_ai_tools.py`**

```python
from app.ai.tools import tools_for_action


def test_wolf_vote_tool_has_target_field():
    tools = tools_for_action("wolf_vote", options=["p0", "p1"])
    assert any(t.name == "wolf_vote" for t in tools)
    tool = next(t for t in tools if t.name == "wolf_vote")
    schema = tool.args_schema.model_json_schema()
    assert "target_id" in schema["properties"]


def test_seer_check_has_skip_option():
    tools = tools_for_action("seer_check", options=["p0", "p1"])
    names = {t.name for t in tools}
    assert "seer_check" in names
    assert "seer_skip" in names


def test_witch_action_exposes_three_tools():
    tools = tools_for_action("witch_action", options=["p0", "p1"])
    names = {t.name for t in tools}
    assert names >= {"witch_save", "witch_poison", "witch_skip"}


def test_speech_tool_text_only():
    tools = tools_for_action("speech", options=[])
    assert any(t.name == "speak" for t in tools)
    tool = next(t for t in tools if t.name == "speak")
    schema = tool.args_schema.model_json_schema()
    assert "text" in schema["properties"]


def test_day_vote_tool_and_abstain():
    tools = tools_for_action("day_vote", options=["p0", "p1"])
    names = {t.name for t in tools}
    assert "day_vote" in names
    assert "day_abstain" in names
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_ai_tools.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/ai/tools.py`**

```python
from __future__ import annotations

from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TargetInput(BaseModel):
    target_id: str = Field(..., description="Player id to target")


class NoInput(BaseModel):
    pass


class SpeakInput(BaseModel):
    text: str = Field(..., description="Your message (<=80 Chinese chars)")


def _noop(**_kwargs):
    return ""


def _mk(name: str, description: str, schema: type[BaseModel]) -> StructuredTool:
    return StructuredTool.from_function(
        func=_noop, name=name, description=description, args_schema=schema,
    )


def tools_for_action(action: str, options: list[str]) -> list[StructuredTool]:
    opts_hint = f" Valid target_id: {options}." if options else ""
    if action == "wolf_vote":
        return [_mk("wolf_vote", "Cast your wolf-kill vote." + opts_hint, TargetInput)]
    if action == "seer_check":
        return [
            _mk("seer_check", "Check a player's identity tonight." + opts_hint, TargetInput),
            _mk("seer_skip", "Skip tonight's check.", NoInput),
        ]
    if action == "witch_action":
        return [
            _mk("witch_save", "Use save potion on a player (typically tonight's victim or yourself)." + opts_hint, TargetInput),
            _mk("witch_poison", "Use poison potion on a player." + opts_hint, TargetInput),
            _mk("witch_skip", "Use neither potion tonight.", NoInput),
        ]
    if action in ("speech", "speak", "last_words"):
        return [_mk("speak", "Speak aloud during your turn.", SpeakInput)]
    if action == "day_vote":
        return [
            _mk("day_vote", "Vote to eliminate a player." + opts_hint, TargetInput),
            _mk("day_abstain", "Abstain from voting.", NoInput),
        ]
    return []


__all__ = ["tools_for_action"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_ai_tools.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai/tools.py backend/tests/test_ai_tools.py
git commit -m "feat: add LangChain function-calling tool schemas per phase"
```

---


### Task 21: AIPlayer — LangChain-backed Player

**Files:**
- Create: `backend/app/players/ai.py`
- Create: `backend/tests/test_ai_player.py`

- [ ] **Step 1: Write failing test `backend/tests/test_ai_player.py`**

Use a stub LLM so this is fast and deterministic.

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.ai.personas import Persona
from app.game.constants import Role
from app.game.events import GameEvent
from app.players.ai import AIPlayer
from app.players.base import ActionPrompt


def _make_ai(stub_response, persona_style="calm"):
    """Build AIPlayer with a stub llm that returns tool_calls or content."""
    stub_llm = MagicMock()
    stub_llm.bind_tools.return_value = stub_llm
    stub_llm.ainvoke = AsyncMock(return_value=stub_response)
    return AIPlayer(
        id="p0", nickname="AI-0", role=Role.WEREWOLF, seat=0,
        persona=Persona(name="X", style=persona_style),
        llm=stub_llm,
    ), stub_llm


@pytest.mark.asyncio
async def test_ai_parses_tool_call_to_response():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "wolf_vote", "args": {"target_id": "p5"},
    }])
    ai, _ = _make_ai(resp)
    out = await ai.request(ActionPrompt(action="wolf_vote", options=["p4", "p5"]))
    assert out.action == "wolf_vote"
    assert out.target == "p5"


@pytest.mark.asyncio
async def test_ai_speech_returns_text():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "speak", "args": {"text": "我觉得 p5 是狼"},
    }])
    ai, _ = _make_ai(resp)
    out = await ai.request(ActionPrompt(action="speech", options=[]))
    assert out.text == "我觉得 p5 是狼"


@pytest.mark.asyncio
async def test_ai_falls_back_to_default_on_invalid_target():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[{
        "id": "c1", "name": "wolf_vote", "args": {"target_id": "nonexistent"},
    }])
    ai, _ = _make_ai(resp)
    out = await ai.request(ActionPrompt(action="wolf_vote", options=["p4", "p5"]))
    # After retries fail, falls back → target in options
    assert out.target in {"p4", "p5"}


@pytest.mark.asyncio
async def test_ai_timeout_falls_back():
    import asyncio
    stub_llm = MagicMock()
    stub_llm.bind_tools.return_value = stub_llm
    async def hang(*a, **kw):
        await asyncio.sleep(10)
    stub_llm.ainvoke = hang
    ai = AIPlayer(id="p0", nickname="AI-0", role=Role.WEREWOLF, seat=0,
                  persona=Persona(name="X", style="calm"),
                  llm=stub_llm, llm_timeout=0.05)
    out = await ai.request(ActionPrompt(action="wolf_vote", options=["p4", "p5"]))
    assert out.target in {"p4", "p5"}


@pytest.mark.asyncio
async def test_ai_notify_appends_to_memory():
    from langchain_core.messages import AIMessage
    resp = AIMessage(content="", tool_calls=[])
    ai, _ = _make_ai(resp)
    await ai.notify(GameEvent(type="system_announce", payload={"text": "天黑"}))
    assert len(ai.memory) == 1
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_ai_player.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/players/ai.py`**

```python
from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.personas import Persona, random_persona
from app.ai.prompts import build_system_prompt
from app.ai.tools import tools_for_action
from app.game.constants import LLM_CALL_TIMEOUT, Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


MAX_LLM_RETRIES = 2


@dataclass
class AIPlayer:
    id: str
    nickname: str
    role: Role
    seat: int
    persona: Persona = field(default_factory=random_persona)
    wolf_teammates: list[str] = field(default_factory=list)
    llm: object | None = None
    memory: list[GameEvent] = field(default_factory=list)
    alive: bool = True
    is_ai: bool = True
    llm_timeout: float = LLM_CALL_TIMEOUT

    def _default_target(self, options: list[str]) -> str | None:
        return random.choice(options) if options else None

    async def notify(self, event: GameEvent) -> None:
        self.memory.append(event)

    def _memory_text(self) -> str:
        lines = []
        for e in self.memory[-40:]:  # cap context
            lines.append(f"[{e.type}] {e.payload}")
        return "\n".join(lines) or "(no prior events)"

    async def _single_llm_call(self, prompt: ActionPrompt) -> ActionResponse | None:
        tools = tools_for_action(prompt.action, prompt.options)
        if self.llm is None:
            return None
        llm = self.llm.bind_tools(tools) if tools else self.llm
        sys_prompt = build_system_prompt(self.role, self.persona, self.wolf_teammates)
        user_msg = (
            f"当前阶段：{prompt.action}\n"
            f"可选目标 id：{prompt.options}\n"
            f"提示：{prompt.hint}\n\n"
            f"历史事件：\n{self._memory_text()}\n\n"
            f"请通过 function calling 作出决策。"
        )
        messages = [SystemMessage(content=sys_prompt), HumanMessage(content=user_msg)]
        try:
            resp = await asyncio.wait_for(llm.ainvoke(messages), timeout=self.llm_timeout)
        except (asyncio.TimeoutError, Exception):
            return None
        tool_calls = getattr(resp, "tool_calls", None) or []
        if not tool_calls:
            return ActionResponse(action=prompt.action, text=(resp.content or "").strip() or None)
        call = tool_calls[0]
        name = call.get("name")
        args = call.get("args", {})
        if name in ("seer_skip", "witch_skip", "day_abstain"):
            return ActionResponse(action=name)
        if name == "speak":
            return ActionResponse(action=prompt.action, text=(args.get("text") or "").strip())
        target = args.get("target_id")
        if name in ("witch_save", "witch_poison"):
            return ActionResponse(action=name, target=target)
        return ActionResponse(action=name or prompt.action, target=target)

    def _is_valid(self, prompt: ActionPrompt, resp: ActionResponse) -> bool:
        if resp is None:
            return False
        if prompt.action in ("speech", "speak", "last_words"):
            return bool(resp.text is not None)
        if resp.action in ("seer_skip", "witch_skip", "day_abstain"):
            return True
        if prompt.action == "witch_action":
            # save target should be tonight's killed or self; poison target from alive options
            if resp.action == "witch_save":
                return resp.target is not None  # engine re-validates
            if resp.action == "witch_poison":
                return resp.target in prompt.options
            return False
        if prompt.options and resp.target not in prompt.options:
            return False
        return True

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        last: ActionResponse | None = None
        for _ in range(MAX_LLM_RETRIES + 1):
            resp = await self._single_llm_call(prompt)
            if resp is not None and self._is_valid(prompt, resp):
                return resp
            last = resp
        # Fallback defaults
        if prompt.action in ("speech", "speak", "last_words"):
            return ActionResponse(action=prompt.action, text="(沉默)")
        if prompt.action == "seer_check":
            return ActionResponse(action="seer_skip")
        if prompt.action == "witch_action":
            return ActionResponse(action="witch_skip")
        if prompt.action == "day_vote":
            return ActionResponse(action="day_abstain")
        # wolf_vote / day_vote_pk / fallback → random legal target
        return ActionResponse(action=prompt.action, target=self._default_target(prompt.options))


__all__ = ["AIPlayer"]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_ai_player.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/players/ai.py backend/tests/test_ai_player.py
git commit -m "feat: implement AIPlayer with LangChain tool-calling and fallback"
```

---


### Task 22: WebSocket protocol schemas

**Files:**
- Create: `backend/app/protocol.py`
- Create: `backend/tests/test_protocol.py`

- [ ] **Step 1: Write failing test `backend/tests/test_protocol.py`**

```python
import pytest
from pydantic import ValidationError

from app.protocol import (
    ClientMessage, ServerMessage,
    CreateRoomPayload, JoinRoomPayload, ActionPayload, ChatPayload, AckPayload,
    PhaseChangePayload, PromptActionPayload, ChatMessagePayload, RoleAssignedPayload,
)


def test_create_room_roundtrip():
    msg = ClientMessage(
        type="create_room",
        payload=CreateRoomPayload(nickname="alice", human_slots=1, ai_slots=5),
        room=None, seq=1,
    )
    data = msg.model_dump()
    assert data["type"] == "create_room"
    parsed = ClientMessage.model_validate(data)
    assert parsed.payload.nickname == "alice"


def test_join_room_requires_code():
    with pytest.raises(ValidationError):
        JoinRoomPayload(nickname="a")  # room_code missing


def test_action_payload_allows_optional_fields():
    p = ActionPayload(action="day_vote", target="p5")
    assert p.target == "p5"
    assert p.text is None


def test_server_phase_change_roundtrip():
    msg = ServerMessage(
        type="phase_change",
        payload=PhaseChangePayload(phase="day_vote", deadline_ts=123.0),
        seq=10,
    )
    raw = msg.model_dump_json()
    ServerMessage.model_validate_json(raw)


def test_role_assigned_wolf_includes_teammates():
    p = RoleAssignedPayload(role="werewolf", wolf_teammates=["p1", "p2"])
    assert p.wolf_teammates == ["p1", "p2"]


def test_prompt_action_requires_action():
    with pytest.raises(ValidationError):
        PromptActionPayload(options=[], deadline_ts=1.0)
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_protocol.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/protocol.py`**

```python
from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, Field


# Client → Server payloads

class CreateRoomPayload(BaseModel):
    nickname: str
    human_slots: int = 1
    ai_slots: int = 5


class JoinRoomPayload(BaseModel):
    room_code: str
    nickname: str


class StartGamePayload(BaseModel):
    pass


class ChatPayload(BaseModel):
    channel: Literal["day", "wolf", "dead"]
    text: str


class ActionPayload(BaseModel):
    action: str
    target: str | None = None
    text: str | None = None


class AckPayload(BaseModel):
    seq: int


class ClientMessage(BaseModel):
    type: Literal[
        "create_room", "join_room", "start_game", "chat", "action", "ack",
    ]
    payload: dict[str, Any] | CreateRoomPayload | JoinRoomPayload | StartGamePayload | ChatPayload | ActionPayload | AckPayload = Field(default_factory=dict)
    room: str | None = None
    seq: int = 0


# Server → Client payloads

class PlayerInfo(BaseModel):
    id: str
    nickname: str
    seat: int
    is_ai: bool
    alive: bool = True
    connected: bool = True


class RoomStatePayload(BaseModel):
    room_code: str
    host_id: str
    players: list[PlayerInfo]


class RoleAssignedPayload(BaseModel):
    role: str
    wolf_teammates: list[str] | None = None


class PhaseChangePayload(BaseModel):
    phase: str
    deadline_ts: float | None = None
    day: int | None = None
    order: list[str] | None = None


class PromptActionPayload(BaseModel):
    action: str
    options: list[str] = Field(default_factory=list)
    deadline_ts: float = 0.0
    hint: str | None = None


class ChatMessagePayload(BaseModel):
    channel: Literal["day", "wolf", "dead"]
    from_id: str = Field(..., alias="from")
    text: str
    last_words: bool = False

    model_config = {"populate_by_name": True}


class SystemAnnouncePayload(BaseModel):
    text: str


class DeathAnnouncePayload(BaseModel):
    dead: list[str]
    reason: str


class VoteTallyPayload(BaseModel):
    votes: dict[str, str | None]
    round: int = 1


class SeerResultPayload(BaseModel):
    target_id: str
    is_wolf: bool


class WitchInfoPayload(BaseModel):
    tonight_killed: str | None
    save_left: bool
    poison_left: bool


class GameOverPayload(BaseModel):
    winner: str
    roles: dict[str, str]


class ErrorPayload(BaseModel):
    code: str
    message: str


class ServerMessage(BaseModel):
    type: Literal[
        "room_state", "role_assigned", "phase_change", "prompt_action",
        "chat_message", "system_announce", "death_announce", "vote_tally",
        "seer_result", "witch_info", "game_over", "error",
    ]
    payload: Any
    room: str | None = None
    seq: int = 0


__all__ = [
    "ClientMessage", "ServerMessage",
    "CreateRoomPayload", "JoinRoomPayload", "StartGamePayload",
    "ChatPayload", "ActionPayload", "AckPayload",
    "PlayerInfo", "RoomStatePayload", "RoleAssignedPayload",
    "PhaseChangePayload", "PromptActionPayload", "ChatMessagePayload",
    "SystemAnnouncePayload", "DeathAnnouncePayload", "VoteTallyPayload",
    "SeerResultPayload", "WitchInfoPayload", "GameOverPayload", "ErrorPayload",
]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_protocol.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/protocol.py backend/tests/test_protocol.py
git commit -m "feat: add WebSocket protocol schemas"
```

---


### Task 23: HumanPlayer — WS-backed Player with reconnect buffer

**Files:**
- Create: `backend/app/players/human.py`
- Create: `backend/tests/test_human_player.py`

- [ ] **Step 1: Write failing test `backend/tests/test_human_player.py`**

```python
import asyncio
import pytest

from app.game.constants import Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt
from app.players.human import HumanPlayer


class FakeSocket:
    def __init__(self):
        self.sent = []
    async def send_json(self, data):
        self.sent.append(data)


@pytest.mark.asyncio
async def test_human_notify_sends_via_socket():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock)
    await hp.notify(GameEvent(type="system_announce", payload={"text": "天黑"}))
    assert len(sock.sent) == 1
    assert sock.sent[0]["type"] == "system_announce"


@pytest.mark.asyncio
async def test_human_request_resolved_by_deliver_action():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock,
                     request_timeout=5)

    async def feed():
        await asyncio.sleep(0.01)
        await hp.deliver_action({"action": "day_vote", "target": "p3"})

    asyncio.create_task(feed())
    resp = await hp.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target == "p3"
    # Socket should have received a prompt_action first
    assert any(m["type"] == "prompt_action" for m in sock.sent)


@pytest.mark.asyncio
async def test_human_request_timeout_returns_default():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock,
                     request_timeout=0.05)
    resp = await hp.request(ActionPrompt(action="day_vote", options=["p2", "p3"]))
    assert resp.target is None  # abstain on timeout
    assert resp.action == "day_vote"


@pytest.mark.asyncio
async def test_human_disconnect_buffers_events_and_replays_on_attach():
    sock = FakeSocket()
    hp = HumanPlayer(id="p1", nickname="A", role=Role.VILLAGER, seat=0, socket=sock)
    await hp.detach()
    await hp.notify(GameEvent(type="chat_message", payload={"from": "p2", "text": "hi"}))
    assert sock.sent == []  # buffered
    new_sock = FakeSocket()
    await hp.attach(new_sock, last_ack_seq=0)
    # All buffered events should have been replayed
    assert any(m["type"] == "chat_message" for m in new_sock.sent)
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_human_player.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/players/human.py`**

```python
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.game.constants import RECONNECT_GRACE_SECONDS, Role
from app.game.events import GameEvent
from app.players.base import ActionPrompt, ActionResponse


class _SocketLike(Protocol):
    async def send_json(self, data: dict) -> None: ...


DEFAULT_REQUEST_TIMEOUT = 60


@dataclass
class _Buffered:
    seq: int
    envelope: dict


@dataclass
class HumanPlayer:
    id: str
    nickname: str
    role: Role
    seat: int
    socket: _SocketLike | None = None
    alive: bool = True
    is_ai: bool = False
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT
    _seq: int = 0
    _buffer: list[_Buffered] = field(default_factory=list)
    _pending: asyncio.Future | None = None
    _pending_action: str | None = None

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    async def _send(self, envelope: dict) -> None:
        self._buffer.append(_Buffered(seq=envelope["seq"], envelope=envelope))
        if self.socket is not None:
            try:
                await self.socket.send_json(envelope)
            except Exception:
                self.socket = None

    async def notify(self, event: GameEvent) -> None:
        envelope = {
            "type": event.type,
            "payload": event.payload,
            "seq": self._next_seq(),
        }
        await self._send(envelope)

    async def request(self, prompt: ActionPrompt) -> ActionResponse:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self._pending = fut
        self._pending_action = prompt.action
        envelope = {
            "type": "prompt_action",
            "payload": {
                "action": prompt.action,
                "options": prompt.options,
                "deadline_ts": prompt.deadline_ts or (time.time() + self.request_timeout),
                "hint": prompt.hint,
            },
            "seq": self._next_seq(),
        }
        await self._send(envelope)
        try:
            action_dict = await asyncio.wait_for(fut, timeout=self.request_timeout)
        except asyncio.TimeoutError:
            return self._default_response(prompt)
        finally:
            self._pending = None
            self._pending_action = None
        return ActionResponse(
            action=action_dict.get("action", prompt.action),
            target=action_dict.get("target"),
            text=action_dict.get("text"),
        )

    def _default_response(self, prompt: ActionPrompt) -> ActionResponse:
        if prompt.action in ("speech", "speak", "last_words"):
            return ActionResponse(action=prompt.action, text="")
        if prompt.action in ("seer_check",):
            return ActionResponse(action="seer_skip")
        if prompt.action in ("witch_action",):
            return ActionResponse(action="witch_skip")
        return ActionResponse(action=prompt.action, target=None)

    async def deliver_action(self, action: dict[str, Any]) -> None:
        fut = self._pending
        if fut is not None and not fut.done():
            fut.set_result(action)

    async def detach(self) -> None:
        self.socket = None

    async def attach(self, socket: _SocketLike, last_ack_seq: int) -> None:
        self.socket = socket
        for item in self._buffer:
            if item.seq > last_ack_seq:
                try:
                    await socket.send_json(item.envelope)
                except Exception:
                    self.socket = None
                    return

    def prune_acked(self, ack_seq: int) -> None:
        self._buffer = [b for b in self._buffer if b.seq > ack_seq]
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_human_player.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/players/human.py backend/tests/test_human_player.py
git commit -m "feat: implement HumanPlayer with reconnect buffer + timeout default"
```

---


### Task 24: Room + RoomManager

**Files:**
- Create: `backend/app/rooms/__init__.py`
- Create: `backend/app/rooms/room.py`
- Create: `backend/app/rooms/room_manager.py`
- Create: `backend/tests/test_room_manager.py`

- [ ] **Step 1: Create `backend/app/rooms/__init__.py`**

Empty file.

- [ ] **Step 2: Write failing test `backend/tests/test_room_manager.py`**

```python
import pytest

from app.rooms.room_manager import RoomManager


@pytest.mark.asyncio
async def test_create_room_returns_unique_code():
    mgr = RoomManager()
    r1 = await mgr.create_room(host_nickname="alice", human_slots=2, ai_slots=4)
    r2 = await mgr.create_room(host_nickname="bob", human_slots=2, ai_slots=4)
    assert r1.code != r2.code


@pytest.mark.asyncio
async def test_join_room_adds_human_player():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", human_slots=2, ai_slots=4)
    pid = await mgr.join_room(room.code, nickname="bob")
    assert pid is not None
    assert any(p.nickname == "bob" for p in room.players)


@pytest.mark.asyncio
async def test_room_fills_ai_slots():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", human_slots=1, ai_slots=5)
    assert sum(1 for p in room.players if p.is_ai) == 5
    assert sum(1 for p in room.players if not p.is_ai) == 1


@pytest.mark.asyncio
async def test_join_rejects_unknown_code():
    mgr = RoomManager()
    with pytest.raises(KeyError):
        await mgr.join_room("NOPE", nickname="bob")


@pytest.mark.asyncio
async def test_join_rejects_full_room():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", human_slots=1, ai_slots=5)
    with pytest.raises(ValueError):
        await mgr.join_room(room.code, nickname="bob")
```

- [ ] **Step 3: Run test — expect fail**

```bash
pytest tests/test_room_manager.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 4: Write `backend/app/rooms/room.py`**

```python
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from app.game.constants import Role
from app.players.ai import AIPlayer
from app.players.human import HumanPlayer


@dataclass
class Room:
    code: str
    host_id: str
    human_slots: int
    ai_slots: int
    players: list[Any] = field(default_factory=list)  # HumanPlayer | AIPlayer
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    created_at: float = 0.0

    @property
    def full(self) -> bool:
        humans = sum(1 for p in self.players if not p.is_ai)
        return humans >= self.human_slots

    def get_player(self, pid: str):
        return next((p for p in self.players if p.id == pid), None)
```

- [ ] **Step 5: Write `backend/app/rooms/room_manager.py`**

```python
from __future__ import annotations

import random
import string
import time
import uuid
from asyncio import Lock

from app.ai.personas import random_persona
from app.game.constants import Role
from app.players.ai import AIPlayer
from app.players.human import HumanPlayer
from app.rooms.room import Room


def _new_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


class RoomManager:
    def __init__(self):
        self._rooms: dict[str, Room] = {}
        self._lock = Lock()

    async def create_room(self, *, host_nickname: str, human_slots: int, ai_slots: int) -> Room:
        if human_slots + ai_slots != 6:
            raise ValueError("Only 6-player rooms supported")
        async with self._lock:
            code = _new_code()
            while code in self._rooms:
                code = _new_code()
            host_id = f"h_{uuid.uuid4().hex[:8]}"
            host = HumanPlayer(id=host_id, nickname=host_nickname,
                               role=Role.VILLAGER, seat=0)
            ai_players = [
                AIPlayer(
                    id=f"ai_{uuid.uuid4().hex[:8]}",
                    nickname=f"AI-{i+1}",
                    role=Role.VILLAGER,  # reassigned at game start
                    seat=human_slots + i,
                    persona=random_persona(),
                )
                for i in range(ai_slots)
            ]
            room = Room(code=code, host_id=host_id,
                        human_slots=human_slots, ai_slots=ai_slots,
                        players=[host, *ai_players], created_at=time.time())
            self._rooms[code] = room
            return room

    async def join_room(self, code: str, *, nickname: str) -> str:
        async with self._lock:
            room = self._rooms.get(code)
            if room is None:
                raise KeyError(f"Room not found: {code}")
            if room.full:
                raise ValueError("Room is full")
            # replace first non-host empty human slot, or append
            pid = f"h_{uuid.uuid4().hex[:8]}"
            seat = next((i for i, p in enumerate(room.players) if p.is_ai), len(room.players))
            hp = HumanPlayer(id=pid, nickname=nickname, role=Role.VILLAGER, seat=seat)
            # Evict an AI to make space (room was pre-filled with AIs)
            ai_idx = next((i for i, p in enumerate(room.players) if p.is_ai), None)
            if ai_idx is not None:
                room.players[ai_idx] = hp
            else:
                room.players.append(hp)
            return pid

    def get_room(self, code: str) -> Room | None:
        return self._rooms.get(code)

    def destroy(self, code: str) -> None:
        self._rooms.pop(code, None)
```

- [ ] **Step 6: Run test — expect pass**

```bash
pytest tests/test_room_manager.py -v
```

Expected: 5 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/rooms/__init__.py backend/app/rooms/room.py backend/app/rooms/room_manager.py backend/tests/test_room_manager.py
git commit -m "feat: add Room and RoomManager with AI slot filling"
```

---


### Task 25: FastAPI app — HTTP + WS + game loop wiring

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/tests/test_http_routes.py`

- [ ] **Step 1: Write failing test `backend/tests/test_http_routes.py`**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200


def test_create_room_http():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "human_slots": 1, "ai_slots": 5})
    assert r.status_code == 200
    body = r.json()
    assert "room_code" in body
    assert body["host_id"].startswith("h_")


def test_join_room_http():
    client = TestClient(app)
    r = client.post("/api/rooms", json={"nickname": "alice", "human_slots": 2, "ai_slots": 4})
    code = r.json()["room_code"]
    r2 = client.post(f"/api/rooms/{code}/join", json={"nickname": "bob"})
    assert r2.status_code == 200
    assert r2.json()["player_id"].startswith("h_")


def test_join_unknown_room_404():
    client = TestClient(app)
    r = client.post("/api/rooms/NOPE/join", json={"nickname": "bob"})
    assert r.status_code == 404
```

- [ ] **Step 2: Run test — expect fail**

```bash
pytest tests/test_http_routes.py -v
```

Expected: FAIL (ImportError).

- [ ] **Step 3: Write `backend/app/main.py`**

```python
from __future__ import annotations

import asyncio
import json
import random

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.game.assign import assign_roles
from app.game.constants import Role
from app.game.engine import GameEngine
from app.game.events import GameEvent
from app.players.ai import AIPlayer
from app.ai.llm import build_llm
from app.rooms.room_manager import RoomManager


app = FastAPI(title="Werewolf AI Backend")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
manager = RoomManager()


class CreateRoomBody(BaseModel):
    nickname: str
    human_slots: int = 1
    ai_slots: int = 5


class JoinRoomBody(BaseModel):
    nickname: str


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/rooms")
async def create_room(body: CreateRoomBody):
    try:
        room = await manager.create_room(
            host_nickname=body.nickname,
            human_slots=body.human_slots,
            ai_slots=body.ai_slots,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"room_code": room.code, "host_id": room.host_id}


@app.post("/api/rooms/{code}/join")
async def join_room(code: str, body: JoinRoomBody):
    try:
        pid = await manager.join_room(code, nickname=body.nickname)
    except KeyError:
        raise HTTPException(status_code=404, detail="Room not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"player_id": pid, "room_code": code}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    # Handshake: first message must be {type:"hello", room, player_id}
    hello = await ws.receive_json()
    if hello.get("type") != "hello":
        await ws.close(code=1003)
        return
    room = manager.get_room(hello.get("room"))
    if room is None:
        await ws.send_json({"type": "error", "payload": {"code": "no_room", "message": "unknown room"}})
        await ws.close()
        return
    player = room.get_player(hello.get("player_id"))
    if player is None or player.is_ai:
        await ws.send_json({"type": "error", "payload": {"code": "no_player", "message": "unknown or AI player"}})
        await ws.close()
        return
    await player.attach(ws, last_ack_seq=int(hello.get("last_ack_seq", 0)))

    try:
        while True:
            msg = await ws.receive_json()
            mtype = msg.get("type")
            payload = msg.get("payload", {}) or {}
            if mtype == "ack":
                player.prune_acked(int(payload.get("seq", 0)))
            elif mtype == "action":
                await player.deliver_action(payload)
            elif mtype == "chat":
                await room.queue.put({"type": "chat", "from": player.id, **payload})
            elif mtype == "start_game":
                if player.id == room.host_id:
                    asyncio.create_task(_run_game(room))
    except WebSocketDisconnect:
        await player.detach()


async def _run_game(room) -> None:
    # Assign roles
    roles = assign_roles(6)
    wolf_ids = []
    for player, role in zip(room.players, roles):
        player.role = role
        if role == Role.WEREWOLF:
            wolf_ids.append(player.id)
    for p in room.players:
        if p.role == Role.WEREWOLF and hasattr(p, "wolf_teammates"):
            p.wolf_teammates = [w for w in wolf_ids if w != p.id]
        # Notify role privately
        extra = {"wolf_teammates": [w for w in wolf_ids if w != p.id]} if p.role == Role.WEREWOLF else {}
        await p.notify(GameEvent(
            type="role_assigned",
            payload={"role": p.role.value, **extra},
            audience=f"player:{p.id}",
        ))

    # Attach llm lazily for AI players
    for p in room.players:
        if isinstance(p, AIPlayer) and p.llm is None:
            try:
                p.llm = build_llm()
            except Exception:
                p.llm = None  # fallback path kicks in inside AIPlayer

    # Pick start seat
    start_id = room.players[random.randrange(len(room.players))].id
    engine = GameEngine(room_code=room.code, players=room.players, start_player_id=start_id)
    await engine.run_until_game_over()
```

- [ ] **Step 4: Run test — expect pass**

```bash
pytest tests/test_http_routes.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Smoke — start server and curl healthz**

```bash
cd backend
uvicorn app.main:app --port 8000 &
SERVER_PID=$!
sleep 2
curl -s http://localhost:8000/healthz
kill $SERVER_PID
```

Expected: `{"ok":true}`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/tests/test_http_routes.py
git commit -m "feat: wire FastAPI HTTP + WS endpoints with game loop"
```

---


### Task 26: Frontend scaffold (Vite + React 19)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/styles/theme.css`

- [ ] **Step 1: Write `frontend/package.json`**

```json
{
  "name": "werewolf-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2: Write `frontend/vite.config.js`**

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
```

- [ ] **Step 3: Write `frontend/index.html`**

```html
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>狼人杀 AI 陪练</title>
    <link rel="stylesheet" href="/src/styles/theme.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Write `frontend/src/main.jsx`**

```jsx
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(<App />);
```

- [ ] **Step 5: Write minimal `frontend/src/App.jsx`**

```jsx
import React from "react";
import useGameStore from "./store/gameStore.js";
import Lobby from "./pages/Lobby.jsx";
import Game from "./pages/Game.jsx";

export default function App() {
  const inGame = useGameStore((s) => s.inGame);
  return inGame ? <Game /> : <Lobby />;
}
```

- [ ] **Step 6: Write `frontend/src/styles/theme.css`**

```css
:root {
  --bg: #0b0d14;
  --bg-soft: #161a25;
  --fg: #e9ecf1;
  --accent: #d4a574;
  --danger: #c9464b;
  --muted: #7f8699;
  --shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}

* { box-sizing: border-box; }
html, body, #root { height: 100%; margin: 0; background: var(--bg); color: var(--fg);
  font-family: "PingFang SC", "Hiragino Sans GB", sans-serif; }

button { cursor: pointer; background: var(--accent); color: #111;
  border: none; border-radius: 8px; padding: 8px 16px; font-weight: 600; }
button:hover { filter: brightness(1.08); }
button:disabled { opacity: 0.5; cursor: not-allowed; }

input, select { background: var(--bg-soft); color: var(--fg);
  border: 1px solid #2a2f3c; border-radius: 6px; padding: 8px; }
```

- [ ] **Step 7: Install and smoke-build**

```bash
cd frontend
npm install
# Will fail to build until pages+store exist; skip build for now
```

- [ ] **Step 8: Commit**

```bash
git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/src/main.jsx frontend/src/App.jsx frontend/src/styles/theme.css
git commit -m "feat: scaffold React frontend with dark theme"
```

---


### Task 27: WS client — connect, seq dedupe, auto-reconnect

**Files:**
- Create: `frontend/src/ws/client.js`

- [ ] **Step 1: Write `frontend/src/ws/client.js`**

```javascript
// Tiny WebSocket client with seq dedupe + auto-reconnect + ack.
// Intentionally untested — behavior is covered by end-to-end manual smoke.
export function createWSClient({ url, room, playerId, onMessage }) {
  let ws = null;
  let lastAckSeq = 0;
  let shouldReconnect = true;
  let reconnectDelay = 500;

  function connect() {
    ws = new WebSocket(url);
    ws.onopen = () => {
      reconnectDelay = 500;
      ws.send(JSON.stringify({
        type: "hello", room, player_id: playerId, last_ack_seq: lastAckSeq,
      }));
    };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (typeof msg.seq === "number") {
        if (msg.seq <= lastAckSeq) return;  // dedupe
        lastAckSeq = msg.seq;
        try { ws.send(JSON.stringify({ type: "ack", payload: { seq: msg.seq } })); } catch {}
      }
      onMessage?.(msg);
    };
    ws.onclose = () => {
      if (!shouldReconnect) return;
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 5000);
    };
    ws.onerror = () => ws.close();
  }

  connect();

  return {
    send(type, payload) {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      ws.send(JSON.stringify({ type, payload, room }));
    },
    close() {
      shouldReconnect = false;
      try { ws?.close(); } catch {}
    },
  };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/ws/client.js
git commit -m "feat: add WS client with seq dedupe, ack and auto-reconnect"
```

---


### Task 28: Zustand store + Lobby page

**Files:**
- Create: `frontend/src/store/gameStore.js`
- Create: `frontend/src/pages/Lobby.jsx`

- [ ] **Step 1: Write `frontend/src/store/gameStore.js`**

```javascript
import { create } from "zustand";

const useGameStore = create((set, get) => ({
  inGame: false,
  roomCode: "",
  playerId: "",
  isHost: false,
  players: [],
  hostId: "",
  phase: "lobby",
  day: 0,
  deadlineTs: null,
  chat: [],          // [{channel, from, text, last_words?}]
  systemLog: [],     // announcements
  myRole: null,
  wolfTeammates: [],
  seerResults: [],   // [{target_id, is_wolf}]
  witchInfo: null,
  gameOver: null,
  promptAction: null, // {action, options, deadline_ts, hint}
  ws: null,

  setConnection({ ws, roomCode, playerId, isHost }) {
    set({ ws, roomCode, playerId, isHost, inGame: true });
  },

  handleEvent(msg) {
    const { type, payload } = msg;
    if (type === "room_state") {
      set({ players: payload.players, hostId: payload.host_id });
    } else if (type === "role_assigned") {
      set({ myRole: payload.role, wolfTeammates: payload.wolf_teammates || [] });
    } else if (type === "phase_change") {
      set({ phase: payload.phase, deadlineTs: payload.deadline_ts || null,
            day: payload.day ?? get().day });
    } else if (type === "prompt_action") {
      set({ promptAction: payload });
    } else if (type === "chat_message") {
      set((s) => ({ chat: [...s.chat, payload] }));
    } else if (type === "system_announce") {
      set((s) => ({ systemLog: [...s.systemLog, payload.text] }));
    } else if (type === "death_announce") {
      const line = payload.dead.length ? `死亡：${payload.dead.join(", ")} (${payload.reason})` : "昨夜平安夜";
      set((s) => ({
        systemLog: [...s.systemLog, line],
        players: s.players.map((p) => payload.dead.includes(p.id) ? { ...p, alive: false } : p),
      }));
    } else if (type === "seer_result") {
      set((s) => ({ seerResults: [...s.seerResults, payload] }));
    } else if (type === "witch_info") {
      set({ witchInfo: payload });
    } else if (type === "game_over") {
      set({ gameOver: payload, phase: "game_over" });
    }
  },

  sendAction(action) {
    get().ws?.send("action", action);
    set({ promptAction: null });
  },
  sendChat(channel, text) {
    get().ws?.send("chat", { channel, text });
  },
  startGame() {
    get().ws?.send("start_game", {});
  },
}));

export default useGameStore;
```

- [ ] **Step 2: Write `frontend/src/pages/Lobby.jsx`**

```jsx
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
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/store/gameStore.js frontend/src/pages/Lobby.jsx
git commit -m "feat: zustand store + lobby page"
```

---


### Task 29: Game page + components (RoundTable, Chat, ActionModal, etc.)

**Files:**
- Create: `frontend/src/pages/Game.jsx`
- Create: `frontend/src/components/RoundTable.jsx`
- Create: `frontend/src/components/PlayerSeat.jsx`
- Create: `frontend/src/components/ChatPanel.jsx`
- Create: `frontend/src/components/PhaseBanner.jsx`
- Create: `frontend/src/components/ActionModal.jsx`
- Create: `frontend/src/components/RoleBadge.jsx`
- Create: `frontend/src/components/SystemLog.jsx`

- [ ] **Step 1: Write `frontend/src/components/PlayerSeat.jsx`**

```jsx
import React from "react";
export default function PlayerSeat({ player, isMe }) {
  const opacity = player.alive === false ? 0.35 : 1;
  return (
    <div style={{
      width: 90, height: 90, borderRadius: "50%",
      background: isMe ? "var(--accent)" : "var(--bg-soft)",
      color: isMe ? "#111" : "var(--fg)",
      display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
      boxShadow: "var(--shadow)", opacity, textAlign: "center", fontSize: 13,
    }}>
      <div>{player.nickname}</div>
      <div style={{ fontSize: 10, opacity: 0.7 }}>
        {player.is_ai ? "AI" : "玩家"} · 座{player.seat + 1}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Write `frontend/src/components/RoundTable.jsx`**

```jsx
import React from "react";
import PlayerSeat from "./PlayerSeat.jsx";

export default function RoundTable({ players, myId }) {
  const radius = 180;
  const cx = 240, cy = 240;
  return (
    <div style={{ position: "relative", width: 480, height: 480, margin: "0 auto" }}>
      <div style={{
        position: "absolute", left: cx - 120, top: cy - 120,
        width: 240, height: 240, borderRadius: "50%",
        background: "radial-gradient(circle, #1c2230 0%, #0b0d14 100%)",
        boxShadow: "var(--shadow)",
      }} />
      {players.map((p, i) => {
        const angle = (i / players.length) * 2 * Math.PI - Math.PI / 2;
        const x = cx + radius * Math.cos(angle) - 45;
        const y = cy + radius * Math.sin(angle) - 45;
        return (
          <div key={p.id} style={{ position: "absolute", left: x, top: y }}>
            <PlayerSeat player={p} isMe={p.id === myId} />
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Write `frontend/src/components/PhaseBanner.jsx`**

```jsx
import React, { useEffect, useState } from "react";

const PHASE_LABELS = {
  lobby: "等待开始", role_assign: "发牌", night_start: "天黑请闭眼",
  wolf_kill: "狼人行动", seer_check: "预言家行动", witch_action: "女巫行动",
  day_announce: "天亮公告", day_speech: "白天发言", day_vote: "白天投票",
  check_win: "判定胜负", game_over: "游戏结束",
};

export default function PhaseBanner({ phase, day, deadlineTs }) {
  const [remaining, setRemaining] = useState(null);
  useEffect(() => {
    if (!deadlineTs) { setRemaining(null); return; }
    const iv = setInterval(() => {
      setRemaining(Math.max(0, Math.ceil(deadlineTs - Date.now() / 1000)));
    }, 500);
    return () => clearInterval(iv);
  }, [deadlineTs]);
  return (
    <div style={{ padding: 12, background: "var(--bg-soft)", borderRadius: 8, marginBottom: 12 }}>
      <strong>第 {day || 0} 天</strong> — {PHASE_LABELS[phase] || phase}
      {remaining != null && <span style={{ marginLeft: 12, color: "var(--muted)" }}>⏱ {remaining}s</span>}
    </div>
  );
}
```

- [ ] **Step 4: Write `frontend/src/components/ChatPanel.jsx`**

```jsx
import React, { useState } from "react";
import useGameStore from "../store/gameStore.js";

export default function ChatPanel() {
  const { chat, sendChat, myRole } = useGameStore();
  const [tab, setTab] = useState("day");
  const [text, setText] = useState("");
  const tabs = ["day"];
  if (myRole === "werewolf") tabs.push("wolf");
  tabs.push("dead");
  const filtered = chat.filter((m) => m.channel === tab);
  return (
    <div style={{ background: "var(--bg-soft)", padding: 12, borderRadius: 8 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{ background: tab === t ? "var(--accent)" : "transparent",
                     color: tab === t ? "#111" : "var(--fg)", border: "1px solid var(--muted)" }}>
            {t === "day" ? "白天" : t === "wolf" ? "狼频道" : "死亡"}
          </button>
        ))}
      </div>
      <div style={{ height: 260, overflowY: "auto", fontSize: 14 }}>
        {filtered.map((m, i) => (
          <div key={i} style={{ marginBottom: 4, opacity: m.last_words ? 0.8 : 1 }}>
            <strong>{m.from}</strong>: {m.text}
            {m.last_words && <span style={{ color: "var(--danger)" }}> [遗言]</span>}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <input style={{ flex: 1 }} value={text} onChange={(e) => setText(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter" && text) { sendChat(tab, text); setText(""); } }} />
        <button onClick={() => { if (text) { sendChat(tab, text); setText(""); } }}>发送</button>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Write `frontend/src/components/ActionModal.jsx`**

```jsx
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
```

- [ ] **Step 6: Write `frontend/src/components/RoleBadge.jsx`**

```jsx
import React from "react";
import useGameStore from "../store/gameStore.js";

const ROLE_LABELS = { werewolf: "狼人", witch: "女巫", seer: "预言家", villager: "平民" };

export default function RoleBadge() {
  const { myRole, wolfTeammates } = useGameStore();
  if (!myRole) return null;
  return (
    <div style={{ padding: 8, background: "var(--bg-soft)", borderRadius: 8, marginBottom: 12 }}>
      <strong>我的身份：</strong>{ROLE_LABELS[myRole]}
      {wolfTeammates?.length > 0 && (
        <div style={{ fontSize: 12, color: "var(--muted)" }}>
          狼队友：{wolfTeammates.join(", ")}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 7: Write `frontend/src/components/SystemLog.jsx`**

```jsx
import React from "react";
import useGameStore from "../store/gameStore.js";

export default function SystemLog() {
  const log = useGameStore((s) => s.systemLog);
  return (
    <div style={{ background: "var(--bg-soft)", padding: 8, borderRadius: 8,
                  maxHeight: 160, overflowY: "auto", fontSize: 13 }}>
      <strong>系统</strong>
      {log.map((line, i) => (
        <div key={i} style={{ color: "var(--muted)" }}>{line}</div>
      ))}
    </div>
  );
}
```

- [ ] **Step 8: Write `frontend/src/pages/Game.jsx`**

```jsx
import React from "react";
import useGameStore from "../store/gameStore.js";
import RoundTable from "../components/RoundTable.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import PhaseBanner from "../components/PhaseBanner.jsx";
import ActionModal from "../components/ActionModal.jsx";
import RoleBadge from "../components/RoleBadge.jsx";
import SystemLog from "../components/SystemLog.jsx";

export default function Game() {
  const { roomCode, players, playerId, phase, day, deadlineTs,
          isHost, startGame, gameOver } = useGameStore();
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 16, padding: 16 }}>
      <div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <h2>房间 {roomCode}</h2>
          {isHost && phase === "lobby" && (
            <button onClick={startGame} disabled={players.length < 6}>开始游戏</button>
          )}
        </div>
        <RoleBadge />
        <PhaseBanner phase={phase} day={day} deadlineTs={deadlineTs} />
        <RoundTable players={players} myId={playerId} />
        {gameOver && (
          <div style={{ marginTop: 16, padding: 12, background: "var(--bg-soft)", borderRadius: 8 }}>
            <h3>游戏结束 — {gameOver.winner === "good" ? "好人胜利" : "狼人胜利"}</h3>
            <pre>{JSON.stringify(gameOver.roles, null, 2)}</pre>
          </div>
        )}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <SystemLog />
        <ChatPanel />
      </div>
      <ActionModal />
    </div>
  );
}
```

- [ ] **Step 9: Smoke build**

```bash
cd frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 10: Commit**

```bash
git add frontend/src/pages/Game.jsx frontend/src/components/
git commit -m "feat: game page with round table, chat, action modal, role badge"
```

---


### Task 30: Real-LLM smoke test (opt-in) + README

**Files:**
- Create: `backend/tests/test_llm_smoke.py`
- Create: `README.md`

- [ ] **Step 1: Write `backend/tests/test_llm_smoke.py`**

```python
import os

import pytest

from app.ai.llm import build_llm
from app.ai.personas import random_persona
from app.game.constants import Role
from app.game.engine import GameEngine
from app.players.ai import AIPlayer


pytestmark = pytest.mark.llm


@pytest.mark.asyncio
async def test_six_real_ai_finish_game():
    if not os.getenv("SILICONFLOW_API_KEY"):
        pytest.skip("No SILICONFLOW_API_KEY in env")
    llm = build_llm()
    specs = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.VILLAGER]
    players = [
        AIPlayer(id=f"ai_{i}", nickname=f"AI-{i}", role=r, seat=i,
                 persona=random_persona(seed=i), llm=llm)
        for i, r in enumerate(specs)
    ]
    engine = GameEngine(
        room_code="LLM", players=players, start_player_id="ai_0",
        phase_timeouts={k: 60 for k in [
            "wolf_kill","seer_check","witch_action",
            "day_announce","day_speech","day_vote","last_words"]},
    )
    await engine.run_until_game_over(max_rounds=8)
    assert engine.winner in {"good", "werewolf"}
```

- [ ] **Step 2: Run — expect skip by default, runs when LLM marker selected**

```bash
pytest -m llm tests/test_llm_smoke.py -v
```

Expected when no API key: SKIPPED. When `SILICONFLOW_API_KEY` set: PASS within ~2 min.

- [ ] **Step 3: Write top-level `README.md`**

```markdown
# Werewolf AI 陪练游戏

多人在线 6 人局狼人杀，AI 玩家通过 LangChain + 硅基流动 API 参与发言和决策。

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 填入 SILICONFLOW_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 创建或加入房间。

## 测试

```bash
cd backend
pytest                   # 单元 + 集成（无 LLM）
pytest -m llm            # 真实 LLM 烟测（需 API key）
```

## 架构

- 服务端权威；每房间一个 `asyncio.Task` 串行推进状态机
- `Player` 抽象统一人机接口；事件通过可见性过滤广播
- 详见 `docs/superpowers/specs/2026-05-10-werewolf-ai-design.md`
```

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_llm_smoke.py README.md
git commit -m "test: add opt-in real-LLM smoke; add README"
```

---


## Execution Notes

- **Order matters**: Tasks 1–30 are ordered by dependency. Complete each before the next; the test of a later task usually imports code from an earlier one.
- **TDD discipline**: every task writes its failing test first. Do not skip the "expect fail" step — seeing the import fail confirms the fixture targets the right module path.
- **Backend commands** assume `cd backend` with the venv activated. Each task commits once tests pass; resolve one test module at a time.
- **Frontend**: no test harness is set up beyond `npm run build`. Manual smoke is the primary check — bring up both processes and run through one game in the browser after Task 29.
- **Fallbacks over coverage**: when the LLM misbehaves the AIPlayer falls back to legal defaults (random target / skip / abstain). Tests use `FakeAIPlayer` for determinism; real-LLM path is only covered by the opt-in `@pytest.mark.llm` smoke.
- **Concurrent timing**: phase tests pass `deadline_ts=9999999999` to sidestep wall-clock; `GameEngine` uses real `time.time()` but tests override `phase_timeouts` to 1 second. Wall-clock timeouts are not unit-tested — rely on the LLM smoke + manual play.

## Open Risks

1. **LLM latency**: 30s per call × 6 AIs in serial could stall speech phase. If latency is a problem, parallelize speeches (but this breaks round-table feel). Revisit after first real game.
2. **Token budget**: memory trims to last 40 events; long games could still exceed context. Consider a summarization pass after day 3 if we hit limits.
3. **WS reconnect during AI turn**: if a human disconnects mid-speech, the 30s grace may collide with speech deadline. Engine does not currently distinguish; document and observe.
4. **SiliconFlow API compatibility with LangChain tool-calling**: some models advertise OpenAI function-calling but respond with text only. `AIPlayer` handles both paths (tool_calls → structured; content → text speech) but non-speech actions without tool_calls fall back to defaults. Pick a model that supports tool calls (e.g. `Qwen/Qwen2.5-14B-Instruct` or `DeepSeek-V2.5`).

<!-- APPEND_HERE -->
