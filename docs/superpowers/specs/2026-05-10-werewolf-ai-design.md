# Werewolf AI 陪练游戏 — 设计文档

Date: 2026-05-10
Status: Design (awaiting implementation plan)

## 1. 目标

构建一个可多人同局的在线狼人杀，由 AI 陪练 + 真人玩家共同游玩：
- 房主创建房间时指定人机比例，空位由 AI 玩家自动填补
- AI 玩家具备完整发言能力（白天圆桌轮流发言 + 投票），能伪装身份、分析局势
- 人类玩家通过浏览器以文字聊天方式参与，AI 能理解并回应
- 法官是虚拟/系统角色（服务端内部流程控制器），不参与投票

首期固定 6 人局配置：3 狼人 + 1 女巫 + 1 预言家 + 1 平民。架构为 8/9 人局等变体预留扩展位，本期不实现。

## 2. 技术栈

- **前端**: React 19 + Vite + 原生 WebSocket。单页应用，夜色圆桌风格 UI。
- **后端**: Python 3.11+，FastAPI（HTTP 用于创建/加入房间 + `/ws` WebSocket），asyncio 驱动房间/游戏循环。
- **AI**: LangChain + `langchain-openai`，`base_url` 指向硅基流动 API；每个 AI 玩家是独立 Agent，通过 OpenAI 兼容的 function calling 输出结构化决策；自然语言发言使用普通 chat 调用。
- **协议**: JSON 消息 over WebSocket，服务端权威（所有游戏状态在后端，前端只渲染）。
- **持久化**: 无；房间状态内存中，进程重启即丢失。单局体验，不做历史回放。

## 3. 核心设计原则

1. **服务端权威**: 所有角色身份、私密信息（查验结果、狼队沟通）只在服务端存在，通过可见性过滤后下发。
2. **人机同接口**: `Player` 抽象对 GameEngine 透明；引擎只调用 `player.request(...)` 等响应。人类响应来自 WS，AI 响应来自内部 Agent。
3. **单房间 = 单 asyncio.Task**: 房间内状态串行推进、无锁；房间间互不影响。
4. **LLM 失败可降级**: AI 超时/解析失败时走默认动作，永远不阻塞游戏。

## 4. 整体架构

```
┌───────────────┐                  ┌─────────────────────────────────┐
│  React 前端    │ ◀─ WebSocket ─▶  │  FastAPI 服务端                 │
│  (人类玩家)    │   JSON msg       │   ├─ RoomManager (多房间)       │
└───────────────┘                  │   ├─ GameEngine (状态机+流程)    │
                                   │   ├─ Judge (广播/计时/裁决)      │
                                   │   ├─ Broadcaster (可见性过滤)    │
                                   │   └─ AIPlayer ×N (LangChain)    │
                                   └─────────────────────────────────┘
                                                 │
                                                 ▼
                                          硅基流动 API
```

## 5. 游戏状态机

Judge（状态机引擎）按下列顺序驱动：

```
LOBBY
  │ start_game（房主触发）
  ▼
ROLE_ASSIGN  ──> 每个玩家收到自己的身份（私密）；狼人额外收到狼队友列表
  │
  ▼
NIGHT_START  ──> 广播"天黑请闭眼"
  │
  ▼
WOLF_KILL    ──> 狼人频道可互相发言；狼人投票锁定击杀目标（平票则随机其中之一）
  │
  ▼
SEER_CHECK   ──> 预言家查验一名存活玩家（可跳过），私密收到身份：好人/狼人
  │
  ▼
WITCH_ACTION ──> 私密告知女巫今夜被杀者身份；选择：救/毒/跳过
  │              救药、毒药各全局 1 次；同一夜不能同时用两瓶
  │              女巫可对自己使用救药（全程可自救）
  ▼
DAY_ANNOUNCE ──> 广播昨夜死亡名单；每个死者有 1 次遗言机会
  │
  ▼
DAY_SPEECH   ──> 圆桌轮流发言：随机起点顺时针，每存活玩家 1 次发言
  │              每人发言窗口 N 秒（默认 60s），AI 自动生成发言
  ▼
DAY_VOTE     ──> 所有存活玩家同时投票；公开计票
  │              平票 → PK 再投一轮；再平票则本轮无人出局
  │              被投出者有 1 次遗言
  ▼
CHECK_WIN    ──> 胜负判定，否则回 NIGHT_START
```

### 胜负判定
- **狼人获胜**: 好人阵营全部死亡（女巫 + 预言家 + 平民皆亡）
- **好人获胜**: 所有狼人死亡
- **其他情况**: 进入下一夜

### 女巫规则确认
- 救药、毒药各 1 次，全局计数
- 同一夜不能同时使用救药 + 毒药
- 女巫可在任何一晚使用救药救自己（不限第一夜）
- 女巫被刀当晚会被告知"今晚被刀的是自己"，此时可选择用救药自救

### 平票处理
- 白天投票平票 → 立即 PK 再投一轮（仅限平票候选人可被投）
- 再平票 → 本轮无人出局，进入下一夜

## 6. 玩家模型

统一抽象，GameEngine 只与 `Player` 接口交互：

```python
class Player(Protocol):
    id: str
    nickname: str
    role: Role              # 服务端内部字段
    alive: bool
    is_ai: bool

    async def request(self, prompt: ActionPrompt) -> ActionResponse: ...
    async def notify(self, event: GameEvent) -> None: ...
```

- `HumanPlayer.request`: 通过 WS 发 `prompt_action` 消息；挂起 `asyncio.Future` 等客户端 `action` 消息回来；超时自动默认动作
- `AIPlayer.request`: 内部调用 LangChain Agent，构造 prompt → function call → 返回 `ActionResponse`
- `notify`: 按可见性把事件推给对应玩家（人类走 WS，AI 走内存缓冲）

### 断线处理
- 人类玩家断线 → 保留座位 30 秒
- 30 秒内重连 → 服务端重放 `last_ack_seq` 之后的事件
- 超时未重连 → 该玩家视为弃权：
  - 发言阶段：跳过（视为沉默）
  - 投票阶段：弃权（不计入任何候选人）

## 7. AI 玩家架构

### 7.1 Agent 构成

```
AIPlayer
├─ role: Role
├─ persona: Persona            # 随机人设（语言风格、性格倾向）
├─ memory: List[GameEvent]     # 按可见性过滤的私有事件流
├─ llm: ChatOpenAI(base_url=硅基流动, model=<可配>)
└─ agent_executor: AgentExecutor（每阶段绑定不同工具集）
```

### 7.2 Prompt 构成

1. **系统提示**: 狼人杀规则摘要 + 你的角色身份 + 胜利条件 + 人设
2. **历史上下文**: 按可见性过滤后的事件流（公开发言、公告、自己的查验结果、狼队发言等）
3. **当前请求**: 当前阶段 + 需要你做什么

### 7.3 Function Calling 工具集（按阶段暴露）

| 阶段 | 暴露给 AI 的工具 |
|------|-----------------|
| WOLF_KILL（夜间狼队沟通）| `speak(text)`, `wolf_vote(target_id)` |
| SEER_CHECK | `seer_check(target_id)`, `seer_skip()` |
| WITCH_ACTION | `witch_save(target_id_or_self)`, `witch_poison(target_id)`, `witch_skip()` |
| DAY_SPEECH（轮到自己）| `speak(text)` |
| DAY_VOTE | `day_vote(target_id)`, `day_abstain()` |
| 遗言 | `speak(text)` |

### 7.4 工程约束

- 发言长度上限：约 80 汉字（控制 token）
- LLM 调用超时：单次 30s；超时或解析失败 → 默认动作（随机合法目标 / 弃权）
- 非法目标（死人 / 自己做非自救动作）→ 服务端拒绝并重试 2 次，仍非法走默认
- 所有 AI 调用并发进行（如多狼人同时决策），用 `asyncio.gather`

## 8. WebSocket 消息协议

所有消息统一外壳：

```json
{
  "type": "...",
  "payload": { ... },
  "room": "ABC123",
  "seq": 42
}
```

### 8.1 客户端 → 服务端

| type | payload |
|------|---------|
| `create_room` | `{ nickname, human_slots, ai_slots }` |
| `join_room` | `{ room_code, nickname }` |
| `start_game` | `{}`（仅房主有效）|
| `chat` | `{ channel: "day"\|"wolf"\|"dead", text }` |
| `action` | `{ action, target?, text? }` |
| `ack` | `{ seq }` — 客户端收到事件的确认，用于断线重放 |

`action` 的合法取值：`wolf_vote`, `seer_check`, `seer_skip`, `witch_save`, `witch_poison`, `witch_skip`, `day_vote`, `day_abstain`, `last_words`, `speech`。

### 8.2 服务端 → 客户端

| type | payload |
|------|---------|
| `room_state` | `{ players: [...], host_id }` |
| `role_assigned` | `{ role, wolf_teammates? }`（私密，仅发给本人）|
| `phase_change` | `{ phase, deadline_ts }` |
| `prompt_action` | `{ action, options: [player_ids], deadline_ts }` |
| `chat_message` | `{ channel, from, text }`（可见性过滤后）|
| `system_announce` | `{ text }` |
| `death_announce` | `{ dead: [ids], reason }` |
| `vote_tally` | `{ votes: {voter_id: target_id} }` |
| `seer_result` | `{ target_id, is_wolf }`（仅发给预言家）|
| `witch_info` | `{ tonight_killed: id, save_left: bool, poison_left: bool }`（仅发给女巫）|
| `game_over` | `{ winner, roles: {id: role} }` |
| `error` | `{ code, message }` |

### 8.3 可见性规则（服务端强制）

| 信息 | 可见对象 |
|------|---------|
| 自己的身份 | 仅本人 |
| 狼队友列表 | 仅狼人 |
| 狼频道聊天/投票 | 仅狼人 |
| 预言家查验结果 | 仅预言家 |
| 女巫被告知的夜间被杀者 | 仅女巫 |
| 死亡频道聊天 | 仅死者之间（可见彼此）|
| 公共白天聊天 | 全员 |
| 死亡公告 | 全员（不含具体角色，除非规则配置）|
| 最终 `game_over` | 全员（含所有人身份）|

## 9. 项目结构

```
werewolf-game-ai/
├─ backend/
│  ├─ pyproject.toml                  # fastapi, uvicorn, langchain, langchain-openai, pydantic, python-dotenv
│  ├─ .env.example                    # SILICONFLOW_API_KEY, SILICONFLOW_BASE_URL, MODEL
│  ├─ app/
│  │  ├─ main.py                      # FastAPI app + /ws 路由
│  │  ├─ config.py
│  │  ├─ protocol.py                  # Pydantic: 所有 WS 消息 schema
│  │  ├─ rooms/
│  │  │  ├─ room_manager.py
│  │  │  └─ room.py
│  │  ├─ game/
│  │  │  ├─ constants.py
│  │  │  ├─ state.py
│  │  │  ├─ engine.py                 # Judge 状态机主循环
│  │  │  ├─ phases/
│  │  │  │   ├─ night_wolf.py
│  │  │  │   ├─ night_seer.py
│  │  │  │   ├─ night_witch.py
│  │  │  │   ├─ day_speech.py
│  │  │  │   └─ day_vote.py
│  │  │  ├─ visibility.py
│  │  │  └─ win_check.py
│  │  ├─ players/
│  │  │  ├─ base.py                   # Player Protocol
│  │  │  ├─ human.py
│  │  │  └─ ai.py
│  │  └─ ai/
│  │     ├─ llm.py                    # ChatOpenAI(base_url=硅基流动)
│  │     ├─ personas.py
│  │     ├─ prompts.py
│  │     └─ tools.py                  # LangChain tool 定义
│  └─ tests/
│     ├─ test_state_machine.py
│     ├─ test_visibility.py
│     ├─ test_win_check.py
│     └─ test_full_game_ai_only.py
├─ frontend/
│  ├─ package.json                    # react, vite
│  ├─ vite.config.js
│  ├─ index.html
│  └─ src/
│     ├─ main.jsx
│     ├─ App.jsx
│     ├─ ws/client.js                 # WS + seq/重连
│     ├─ store/gameStore.js
│     ├─ pages/
│     │   ├─ Lobby.jsx
│     │   └─ Game.jsx
│     ├─ components/
│     │   ├─ RoundTable.jsx
│     │   ├─ PlayerSeat.jsx
│     │   ├─ ChatPanel.jsx
│     │   ├─ PhaseBanner.jsx
│     │   ├─ ActionModal.jsx
│     │   ├─ RoleBadge.jsx
│     │   └─ SystemLog.jsx
│     └─ styles/
│        └─ theme.css                 # 夜色 + 圆桌主题
└─ docs/
   └─ superpowers/specs/
      └─ 2026-05-10-werewolf-ai-design.md
```

## 10. 并发模型

- 每个房间一个 `asyncio.Task` 跑 `game_loop`，状态机内状态串行、无锁
- WS 连接 handler 把入站消息丢进房间队列 `asyncio.Queue`，不直接改状态
- AI 调用 `await agent.ainvoke(...)` 异步，不阻塞其他房间
- 每个 `phase` 函数都接收 `deadline_ts`，通过 `asyncio.wait_for` 实现超时默认
- 同一阶段多个玩家同时决策（如狼人出刀）→ `asyncio.gather` 并发收集

## 11. 错误与边界处理

| 场景 | 策略 |
|------|------|
| LLM 调用超时 | 走该动作的默认值（随机合法目标/跳过） |
| LLM 输出解析失败 | 同上；重试 2 次仍失败走默认 |
| AI 选了非法目标 | 服务端拒绝并重新请求；累计 2 次失败走默认 |
| 人类玩家断线 | 保留 30s；内重连恢复；超时按弃权处理 |
| 房间创建后无玩家加入 | 空闲 10 分钟自动销毁 |
| 游戏结束后 | 房间保留 2 分钟展示结果后销毁 |
| WS 消息 seq 乱序 | 客户端按 seq 去重；断线重连服务端重放 `last_ack_seq+1` 起 |

## 12. 测试策略

- **纯单元测试**（不依赖 LLM）:
  - 状态机转移：给定输入序列 → 预期阶段流转
  - 可见性过滤：每种事件对每种角色的可见性断言
  - 胜负判定：各种存活组合下的 winner
  - 计票：正常、平票、PK、弃权
- **集成测试**: `FakeAIPlayer`（确定性返回）跑完整局，无人类玩家也能跑完
- **LLM 烟测**: 标记 `@pytest.mark.llm`，6 个真实 AI 跑 1 局，断言 game_over 到达；默认不跑，CI 手动触发

## 13. 非目标（明确不做）

- 用户账号 / 注册 / 登录
- 对局历史回放
- 排行榜 / 统计
- 语音聊天
- 8 人局 / 9 人局 / 其他角色（猎人、守卫等）
- 手机原生 App
