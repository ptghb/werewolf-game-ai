# 12 Player Idiot Role Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 12-player mode and the idiot role, including reveal-on-vote behavior and post-reveal voting restrictions.

**Architecture:** Keep the current explicit role/mode structure and extend it minimally. Store idiot reveal state on `PlayerState`; make `day_vote` responsible for excluding revealed idiots from voters and vote options and for emitting `idiot_reveal` instead of `death_announce` when an unrevealed idiot is voted out.

**Tech Stack:** Python 3.11+, FastAPI backend, dataclasses, pytest, pytest-asyncio.

---

## File Structure

- Modify `backend/app/game/constants.py` — add `Role.IDIOT` and the 12-player role pool.
- Modify `backend/app/game/assign.py` — allow `assign_roles(12)` and choose the 12-player pool.
- Modify `backend/app/rooms/room_manager.py` — allow `mode="12"` and create 11 AI slots.
- Modify `backend/app/game/state.py` — add `PlayerState.idiot_revealed`.
- Modify `backend/app/game/phases/day_vote.py` — implement idiot reveal and post-reveal voting restrictions.
- Modify `backend/app/protocol.py` — allow server event type `idiot_reveal`.
- Modify `backend/app/ai/prompts.py` — document 12-player rules and idiot behavior for AI players.
- Modify `backend/tests/test_assign.py` — cover 12-player role assignment.
- Modify `backend/tests/test_room_manager.py` — cover 12-player room creation.
- Modify `backend/tests/test_phase_day_vote.py` — cover idiot vote/reveal restrictions.
- Modify `backend/tests/test_phase_day_speech.py` — prove revealed idiot still speaks.
- Modify `backend/tests/test_phase_day_announce.py` — prove revealed idiot can still die at night.
- Modify `backend/tests/test_win_check.py` — prove alive idiot counts as good.

---

### Task 1: Add 12-player role constants and assignment

**Files:**
- Modify: `backend/app/game/constants.py:3-42`
- Modify: `backend/app/game/assign.py:4-13`
- Test: `backend/tests/test_assign.py`

- [ ] **Step 1: Write failing assignment tests**

Edit `backend/tests/test_assign.py` to include `TWELVE_PLAYER_ROLES` import and add these tests:

```python
import random

from app.game.assign import assign_roles
from app.game.constants import Role, SIX_PLAYER_ROLES, TWELVE_PLAYER_ROLES


def test_assign_produces_exact_six_roles():
    rng = random.Random(42)
    roles = assign_roles(6, rng=rng)
    assert len(roles) == 6
    assert sorted(roles) == sorted(SIX_PLAYER_ROLES)


def test_assign_deterministic_under_seed():
    r1 = assign_roles(6, rng=random.Random(1))
    r2 = assign_roles(6, rng=random.Random(1))
    assert r1 == r2


def test_assign_roles_9_players():
    roles = assign_roles(9)
    assert len(roles) == 9
    assert roles.count(Role.WEREWOLF) == 3
    assert roles.count(Role.VILLAGER) == 3
    assert roles.count(Role.SEER) == 1
    assert roles.count(Role.WITCH) == 1
    assert roles.count(Role.HUNTER) == 1


def test_assign_roles_12_players():
    roles = assign_roles(12)
    assert len(roles) == 12
    assert sorted(roles) == sorted(TWELVE_PLAYER_ROLES)
    assert roles.count(Role.WEREWOLF) == 4
    assert roles.count(Role.VILLAGER) == 4
    assert roles.count(Role.SEER) == 1
    assert roles.count(Role.WITCH) == 1
    assert roles.count(Role.HUNTER) == 1
    assert roles.count(Role.IDIOT) == 1


def test_assign_rejects_invalid_player_counts():
    import pytest
    for player_count in (5, 7, 10, 13):
        with pytest.raises(ValueError):
            assign_roles(player_count)
```

- [ ] **Step 2: Run tests to verify failure**

Run from repo root:

```bash
cd backend && pytest tests/test_assign.py -v
```

Expected: FAIL because `TWELVE_PLAYER_ROLES` and `Role.IDIOT` do not exist, and `assign_roles(12)` is rejected.

- [ ] **Step 3: Implement role constants**

Edit `backend/app/game/constants.py` so the role section becomes:

```python
class Role(str, Enum):
    WEREWOLF = "werewolf"
    WITCH = "witch"
    SEER = "seer"
    VILLAGER = "villager"
    HUNTER = "hunter"
    IDIOT = "idiot"
```

Add the 12-player pool after `NINE_PLAYER_ROLES`:

```python
TWELVE_PLAYER_ROLES: list[Role] = [
    Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
    Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT,
    Role.VILLAGER, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
]
```

- [ ] **Step 4: Implement assignment support**

Edit `backend/app/game/assign.py` to:

```python
from __future__ import annotations

import random

from app.game.constants import Role, SIX_PLAYER_ROLES, NINE_PLAYER_ROLES, TWELVE_PLAYER_ROLES


ROLE_POOLS = {
    6: SIX_PLAYER_ROLES,
    9: NINE_PLAYER_ROLES,
    12: TWELVE_PLAYER_ROLES,
}


def assign_roles(n: int, rng: random.Random | None = None) -> list[Role]:
    if n not in ROLE_POOLS:
        raise ValueError(f"Only 6, 9, or 12-player games supported, got {n}")
    rng = rng or random.Random()
    pool = list(ROLE_POOLS[n])
    rng.shuffle(pool)
    return pool


__all__ = ["assign_roles"]
```

- [ ] **Step 5: Run assignment tests**

```bash
cd backend && pytest tests/test_assign.py -v
```

Expected: PASS.

- [ ] **Step 6: Check git diff**

```bash
git diff -- backend/app/game/constants.py backend/app/game/assign.py backend/tests/test_assign.py
```

Expected: Diff only contains role constants, assignment support, and assignment tests.

---

### Task 2: Add 12-player room mode

**Files:**
- Modify: `backend/app/rooms/room_manager.py:25-33`
- Test: `backend/tests/test_room_manager.py`

- [ ] **Step 1: Write failing room mode test**

Append to `backend/tests/test_room_manager.py`:

```python
@pytest.mark.asyncio
async def test_create_room_12_mode_fills_eleven_ai_slots():
    mgr = RoomManager()
    room = await mgr.create_room(host_nickname="alice", mode="12")
    assert len(room.players) == 12
    assert sum(1 for p in room.players if p.is_ai) == 11
    assert sum(1 for p in room.players if not p.is_ai) == 1
    assert room.players[0].nickname == "alice"
    assert room.players[0].seat == 0
    assert [p.seat for p in room.players] == list(range(12))
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && pytest tests/test_room_manager.py::test_create_room_12_mode_fills_eleven_ai_slots -v
```

Expected: FAIL with `ValueError: Invalid mode: 12`.

- [ ] **Step 3: Implement room mode support**

Edit the mode branch in `backend/app/rooms/room_manager.py`:

```python
    async def create_room(self, *, host_nickname: str, mode: str = "6") -> Room:
        if mode == "6":
            ai_slots = 5
        elif mode == "9":
            ai_slots = 8
        elif mode == "12":
            ai_slots = 11
        else:
            raise ValueError(f"Invalid mode: {mode}")
```

Do not keep an unused `total` variable.

- [ ] **Step 4: Run room manager tests**

```bash
cd backend && pytest tests/test_room_manager.py -v
```

Expected: PASS.

- [ ] **Step 5: Check git diff**

```bash
git diff -- backend/app/rooms/room_manager.py backend/tests/test_room_manager.py
```

Expected: Diff only contains 12-player room mode support and its test.

---

### Task 3: Add idiot reveal state and protocol event

**Files:**
- Modify: `backend/app/game/state.py:13-22`
- Modify: `backend/app/protocol.py:146-151`
- Test: `backend/tests/test_phase_day_vote.py`

- [ ] **Step 1: Write failing state/protocol test through vote behavior**

Append this test to `backend/tests/test_phase_day_vote.py`:

```python
@pytest.mark.asyncio
async def test_idiot_vote_reveal_sets_state_and_event_without_death():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    fakes = []
    for p in state.players:
        fake = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="farewell")
        fake.scripted = {"day_vote": "p5"}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    idiot = state.get_player("p5")
    assert idiot.alive is True
    assert idiot.idiot_revealed is True
    assert result["eliminated"] is None
    assert result["idiot_revealed"] == "p5"

    events = fakes[0].received
    assert any(e.type == "idiot_reveal" and e.payload == {"player_id": "p5"} for e in events)
    assert not any(e.type == "death_announce" and e.payload.get("reason") == "vote" for e in events)
    assert not any(e.type == "chat_message" and e.payload.get("last_words") for e in events)
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend && pytest tests/test_phase_day_vote.py::test_idiot_vote_reveal_sets_state_and_event_without_death -v
```

Expected: FAIL because `Role.IDIOT` may now exist, but `PlayerState.idiot_revealed` and `run_day_vote` reveal behavior do not.

- [ ] **Step 3: Add state field**

Edit `backend/app/game/state.py` `PlayerState`:

```python
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
    idiot_revealed: bool = False
```

- [ ] **Step 4: Allow protocol event type**

Edit `backend/app/protocol.py` `ServerMessage.type` literal to include `idiot_reveal`:

```python
class ServerMessage(BaseModel):
    type: Literal[
        "room_state", "role_assigned", "phase_change", "prompt_action",
        "chat_message", "system_announce", "death_announce", "vote_tally",
        "seer_result", "witch_info", "game_over", "error", "idiot_reveal",
    ]
    payload: Any
    room: Optional[str] = None
    seq: int = 0
```

- [ ] **Step 5: Implement reveal branch in day vote**

Edit imports in `backend/app/game/phases/day_vote.py`:

```python
from app.game.constants import Phase, Role
```

Add helper above `run_day_vote`:

```python
def _is_revealed_idiot(player) -> bool:
    return player.role == Role.IDIOT and player.idiot_revealed
```

Replace the final `if eliminated:` block with:

```python
    idiot_revealed: str | None = None
    if eliminated:
        victim = state.get_player(eliminated)
        if victim and victim.role == Role.IDIOT and not victim.idiot_revealed:
            victim.idiot_revealed = True
            idiot_revealed = eliminated
            eliminated = None
            logger.info("白痴翻牌免死 | player=%s(%s)", victim.id, victim.nickname)
            await broadcaster.broadcast(GameEvent(
                type="idiot_reveal", payload={"player_id": victim.id},
            ))
        else:
            if victim:
                victim.alive = False
            logger.info("放逐 | player=%s(%s) | is_ai=%s",
                        eliminated, victim.nickname if victim else "?", victim.is_ai if victim else "?")
            await broadcaster.broadcast(GameEvent(
                type="death_announce", payload={"dead": [eliminated], "reason": "vote"},
            ))
            speaker = player_lookup.get(eliminated)
            if speaker is not None:
                resp = await speaker.request(ActionPrompt(
                    action="last_words",
                    deadline_ts=deadline_ts,
                    hint="Your final words (<=80 chars)",
                    nickname_map=nickname_map,
                ))
                text = (resp.text or "").strip()
                if text:
                    await broadcaster.broadcast(GameEvent(
                        type="chat_message",
                        payload={"from": eliminated, "from_name": speaker.nickname, "text": text, "channel": "day", "last_words": True},
                    ))
                if victim:
                    victim.used_last_words = True
    return {"eliminated": eliminated, "idiot_revealed": idiot_revealed, "pk_used": pk_used, "votes": votes}
```

- [ ] **Step 6: Run the reveal test**

```bash
cd backend && pytest tests/test_phase_day_vote.py::test_idiot_vote_reveal_sets_state_and_event_without_death -v
```

Expected: PASS.

- [ ] **Step 7: Run all day vote tests**

```bash
cd backend && pytest tests/test_phase_day_vote.py -v
```

Expected: PASS.

- [ ] **Step 8: Check git diff**

```bash
git diff -- backend/app/game/state.py backend/app/protocol.py backend/app/game/phases/day_vote.py backend/tests/test_phase_day_vote.py
```

Expected: Diff only contains idiot reveal state, protocol event allowance, vote reveal behavior, and related tests.

---

### Task 4: Exclude revealed idiots from voting and vote options

**Files:**
- Modify: `backend/app/game/phases/day_vote.py:17-111`
- Test: `backend/tests/test_phase_day_vote.py`

- [ ] **Step 1: Add tests for post-reveal restrictions**

Append to `backend/tests/test_phase_day_vote.py`:

```python
@pytest.mark.asyncio
async def test_revealed_idiot_cannot_vote_or_be_voted():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    state.get_player("p5").idiot_revealed = True

    fakes = []
    for p in state.players:
        fake = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        fake.scripted = {"day_vote": "p5"}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    assert "p5" not in result["votes"]
    assert all(target != "p5" for target in result["votes"].values())
    idiot_fake = next(f for f in fakes if f.id == "p5")
    assert not any(event.type == "prompt_action" for event in idiot_fake.received)
    assert state.get_player("p5").alive is True


@pytest.mark.asyncio
async def test_revealed_idiot_excluded_from_pk_candidates():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    state = GameState(
        room_code="R",
        players=[
            PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
            for i, r in enumerate(roles)
        ],
        phase=Phase.DAY_VOTE,
    )
    state.get_player("p5").idiot_revealed = True

    vote_scripts = {
        "p0": "p3",
        "p1": "p3",
        "p2": "p4",
        "p3": "p4",
        "p4": "p5",
        "p5": "p3",
    }
    pk_scripts = {
        "p0": "p3",
        "p1": "p3",
        "p2": "p3",
        "p3": "p4",
        "p4": "p4",
        "p5": "p4",
    }
    fakes = []
    for p in state.players:
        fake = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        fake.scripted = {"day_vote": vote_scripts[p.id], "day_vote_pk": pk_scripts[p.id]}
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    result = await run_day_vote(state, fakes, broadcaster=b, deadline_ts=9999999999)

    assert result["pk_used"] is True
    pk_event = next(e for e in fakes[0].received if e.type == "pk_round")
    assert pk_event.payload["candidates"] == ["p3", "p4"]
    assert result["eliminated"] == "p3"
    assert state.get_player("p5").alive is True
```

- [ ] **Step 2: Run tests to verify failure**

```bash
cd backend && pytest tests/test_phase_day_vote.py::test_revealed_idiot_cannot_vote_or_be_voted tests/test_phase_day_vote.py::test_revealed_idiot_excluded_from_pk_candidates -v
```

Expected: FAIL because revealed idiot is still included in voters and options.

- [ ] **Step 3: Implement voting eligibility helpers**

In `backend/app/game/phases/day_vote.py`, replace `_is_revealed_idiot` helper with:

```python
def _is_revealed_idiot(player) -> bool:
    return player.role == Role.IDIOT and player.idiot_revealed


def _can_vote(player) -> bool:
    return player.alive and not _is_revealed_idiot(player)


def _can_be_voted(player) -> bool:
    return player.alive and not _is_revealed_idiot(player)
```

- [ ] **Step 4: Apply helper filters in `run_day_vote`**

Replace:

```python
    alive_ids = [p.id for p in state.alive_players()]
    voters = [player_lookup[pid] for pid in alive_ids if pid in player_lookup]
```

with:

```python
    vote_options = [p.id for p in state.players if _can_be_voted(p)]
    voter_ids = [p.id for p in state.players if _can_vote(p)]
    voters = [player_lookup[pid] for pid in voter_ids if pid in player_lookup]
```

Replace first-round collection:

```python
    votes = await _collect_votes(voters, alive_ids, "day_vote", deadline_ts, nickname_map)
```

with:

```python
    votes = await _collect_votes(voters, vote_options, "day_vote", deadline_ts, nickname_map)
```

Replace tie candidates:

```python
        candidates = vote_result.tied_candidates
```

with:

```python
        candidates = [pid for pid in vote_result.tied_candidates if pid in vote_options]
```

- [ ] **Step 5: Run restriction tests**

```bash
cd backend && pytest tests/test_phase_day_vote.py::test_revealed_idiot_cannot_vote_or_be_voted tests/test_phase_day_vote.py::test_revealed_idiot_excluded_from_pk_candidates -v
```

Expected: PASS.

- [ ] **Step 6: Run all day vote tests**

```bash
cd backend && pytest tests/test_phase_day_vote.py -v
```

Expected: PASS.

- [ ] **Step 7: Check git diff**

```bash
git diff -- backend/app/game/phases/day_vote.py backend/tests/test_phase_day_vote.py
```

Expected: Diff only contains revealed idiot voting restrictions and related tests.

---

### Task 5: Verify speech, night death, and win behavior

**Files:**
- Modify: `backend/tests/test_phase_day_speech.py`
- Modify: `backend/tests/test_phase_day_announce.py`
- Modify: `backend/tests/test_win_check.py`

- [ ] **Step 1: Add revealed idiot speech test**

Append to `backend/tests/test_phase_day_speech.py`:

```python
@pytest.mark.asyncio
async def test_revealed_idiot_still_speaks():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    players[5].idiot_revealed = True
    state = GameState(room_code="R", players=players, phase=Phase.DAY_SPEECH)
    fakes = []
    for p in players:
        fake = FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat)
        fake.speech = f"speech-{p.id}"
        fakes.append(fake)

    b = Broadcaster(state, fakes)
    order = await run_day_speech(state, fakes, broadcaster=b, start_player_id="p4", per_player_timeout=5)

    assert "p5" in order
    assert any(
        e.type == "chat_message" and e.payload.get("from") == "p5" and e.payload.get("text") == "speech-p5"
        for e in fakes[0].received
    )
```

- [ ] **Step 2: Add revealed idiot night death test**

If `backend/tests/test_phase_day_announce.py` exists, append this test. If it does not exist, create it with the imports shown:

```python
import pytest

from app.game.broadcaster import Broadcaster
from app.game.constants import Phase, Role
from app.game.phases.day_announce import run_day_announce
from app.game.state import GameState, PlayerState
from tests.fakes import FakeAIPlayer


@pytest.mark.asyncio
async def test_revealed_idiot_can_die_at_night():
    roles = [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
             Role.WITCH, Role.SEER, Role.IDIOT]
    players = [
        PlayerState(id=f"p{i}", nickname=f"n{i}", role=r, is_ai=True, seat=i)
        for i, r in enumerate(roles)
    ]
    players[5].idiot_revealed = True
    state = GameState(room_code="R", players=players, phase=Phase.DAY_ANNOUNCE)
    state.tonight_killed_by_wolves = "p5"
    fakes = [FakeAIPlayer(id=p.id, nickname=p.nickname, role=p.role, seat=p.seat, speech="last") for p in players]

    b = Broadcaster(state, fakes)
    dead = await run_day_announce(state, fakes, broadcaster=b, deadline_ts=9999999999)

    assert dead == ["p5"]
    assert state.get_player("p5").alive is False
    assert any(
        e.type == "death_announce" and e.payload == {"dead": ["p5"], "reason": "night"}
        for e in fakes[0].received
    )
```

- [ ] **Step 3: Add win-check test**

Append to `backend/tests/test_win_check.py`:

```python
def test_alive_idiot_counts_as_good():
    players = [
        PlayerState(id="wolf", nickname="wolf", role=Role.WEREWOLF, is_ai=False, seat=0),
        PlayerState(id="idiot", nickname="idiot", role=Role.IDIOT, is_ai=False, seat=1, idiot_revealed=True),
    ]
    state = GameState(room_code="R", players=players, phase=Phase.CHECK_WIN)
    assert check_winner(state) is None
```

- [ ] **Step 4: Run behavior tests**

```bash
cd backend && pytest tests/test_phase_day_speech.py::test_revealed_idiot_still_speaks tests/test_phase_day_announce.py::test_revealed_idiot_can_die_at_night tests/test_win_check.py::test_alive_idiot_counts_as_good -v
```

Expected: PASS after prior tasks. These tests document behavior; no production code change should be required.

- [ ] **Step 5: Check git diff**

```bash
git diff -- backend/tests/test_phase_day_speech.py backend/tests/test_phase_day_announce.py backend/tests/test_win_check.py
```

Expected: Diff only contains lifecycle behavior tests for revealed idiot speech, night death, and win checking.

---

### Task 6: Update AI prompts for 12-player idiot rules

**Files:**
- Modify: `backend/app/ai/prompts.py:6-22`
- Test: `backend/tests/test_ai_prompts.py`

- [ ] **Step 1: Add prompt tests**

If `backend/tests/test_ai_prompts.py` does not exist, create it with:

```python
from app.ai.personas import Persona
from app.ai.prompts import ROLE_DESCRIPTIONS, RULES_SUMMARY, build_system_prompt
from app.game.constants import Role


def test_rules_summary_mentions_12_player_idiot_rules():
    assert "游戏规则（12 人局）" in RULES_SUMMARY
    assert "4 狼人" in RULES_SUMMARY
    assert "1 白痴" in RULES_SUMMARY
    assert "翻牌免死" in RULES_SUMMARY
    assert "不能投票" in RULES_SUMMARY
    assert "不能再被投票" in RULES_SUMMARY
    assert "仍可被杀" in RULES_SUMMARY


def test_idiot_role_prompt_exists():
    persona = Persona(name="测试人格", style="冷静")
    prompt = build_system_prompt(
        Role.IDIOT,
        persona,
        wolf_teammates=[],
        nickname_map={"p1": "白痴玩家"},
        self_id="p1",
        self_nickname="白痴玩家",
    )
    assert ROLE_DESCRIPTIONS[Role.IDIOT] in prompt
    assert "你是白痴" in prompt
    assert "好人阵营" in prompt
```

- [ ] **Step 2: Run prompt tests to verify failure**

```bash
cd backend && pytest tests/test_ai_prompts.py -v
```

Expected: FAIL because prompts do not mention 12-player idiot rules and `ROLE_DESCRIPTIONS` lacks `Role.IDIOT`.

- [ ] **Step 3: Update prompts**

Edit `backend/app/ai/prompts.py` role descriptions:

```python
ROLE_DESCRIPTIONS: dict[Role, str] = {
    Role.WEREWOLF: "你是狼人。夜间你和狼队友一起决定击杀目标；白天要伪装好人，避免被投出。",
    Role.SEER: "你是预言家（好人阵营）。夜间每晚查验一名玩家的身份；白天要利用信息引导好人投票。",
    Role.WITCH: "你是女巫（好人阵营）。你有救药和毒药各 1 瓶（全局计数），同一夜不能同时使用两瓶。",
    Role.VILLAGER: "你是平民（好人阵营）。你无特殊技能，依靠推理和发言引导投票。",
    Role.HUNTER: "你是猎人（好人阵营）。当你被狼人杀死或被投票放逐时，可以开枪带走任意一名玩家。被女巫毒死不能开枪。",
    Role.IDIOT: "你是白痴（好人阵营）。未翻牌前正常发言和投票；被公投出局时翻牌免死，之后仍可发言，但不能投票、不能再被投票，仍可被杀。",
}
```

Edit `RULES_SUMMARY`:

```python
RULES_SUMMARY = """
游戏规则（6 人局）：2 狼人 + 1 女巫 + 1 预言家 + 2 平民。
游戏规则（9 人局）：3 狼人 + 1 女巫 + 1 预言家 + 3 平民 + 1 猎人。
游戏规则（12 人局）：4 狼人 + 1 预言家 + 1 女巫 + 1 猎人 + 1 白痴 + 4 平民。
夜间：狼人共刀 → 预言家查验 → 女巫决定救/毒/跳。
白天：公布死讯 → 轮流发言 → 全员投票（平票则 PK，再平无人出局）。
猎人：被狼刀或公投出局时可开枪带走一人；被毒不能开枪。
白痴：未翻牌前正常发言和投票；被公投出局时翻牌免死，之后可继续发言，但不能投票、不能再被投票，仍可被杀。
胜负：所有狼人死 → 好人胜；好人全死 → 狼人胜。
""".strip()
```

- [ ] **Step 4: Run prompt tests**

```bash
cd backend && pytest tests/test_ai_prompts.py -v
```

Expected: PASS.

- [ ] **Step 5: Check git diff**

```bash
git diff -- backend/app/ai/prompts.py backend/tests/test_ai_prompts.py
```

Expected: Diff only contains AI prompt text and prompt tests for 12-player idiot rules.

---

### Task 7: Final integration verification

**Files:**
- Verify all modified backend files

- [ ] **Step 1: Run targeted backend tests**

```bash
cd backend && pytest tests/test_assign.py tests/test_room_manager.py tests/test_phase_day_vote.py tests/test_phase_day_speech.py tests/test_phase_day_announce.py tests/test_win_check.py tests/test_ai_prompts.py -v
```

Expected: PASS.

- [ ] **Step 2: Run full backend test suite**

```bash
cd backend && pytest -v
```

Expected: PASS.

- [ ] **Step 3: Inspect git diff for accidental changes**

```bash
git diff -- backend/app/game/constants.py backend/app/game/assign.py backend/app/rooms/room_manager.py backend/app/game/state.py backend/app/game/phases/day_vote.py backend/app/protocol.py backend/app/ai/prompts.py backend/tests/test_assign.py backend/tests/test_room_manager.py backend/tests/test_phase_day_vote.py backend/tests/test_phase_day_speech.py backend/tests/test_phase_day_announce.py backend/tests/test_win_check.py backend/tests/test_ai_prompts.py
```

Expected: Diff only contains 12-player mode, idiot role, tests, and prompt updates.

- [ ] **Step 4: Create a commit only if requested**

If the user explicitly requests a commit after implementation, stage the relevant files and create one new commit with a message that reflects the implemented feature. If no commit is requested, leave changes uncommitted.

---

## Self-Review

- Spec coverage: role enum, 12-player role pool, room mode, AI prompts, idiot reveal state, `idiot_reveal` event, vote restrictions, speech behavior, night death behavior, and win behavior are each mapped to tasks above.
- Placeholder scan: no `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: the plan consistently uses `Role.IDIOT`, `PlayerState.idiot_revealed`, `idiot_reveal`, and `result["idiot_revealed"]`.
