# 设计文档：9人狼人杀 + 猎人角色

## 概述

在现有 6 人局基础上，新增 9 人局模式（3狼3平民1预言家1女巫1猎人），新增猎人角色及其开枪机制。首页创建房间从选择真实玩家数量改为选择"6人场(5AI)"或"9人场(8AI)"。

## 前端改动

### 首页创建房间 (Lobby.jsx)

- 去掉 `humanSlots` 选择器按钮组
- 改为两个大按钮卡片：「6人场(5AI)」和「9人场(8AI)」
- 选择后 POST 请求 body 改为发送 `mode` 字段（`"6"` 或 `"9"`），不再发送 `human_slots` / `ai_slots`
- 固定 1 个真人玩家（房主），其余全 AI

### API 请求变更

```javascript
// 旧
POST /api/rooms  body: { nickname, human_slots: n, ai_slots: 6-n }

// 新
POST /api/rooms  body: { nickname, mode: "6" }  // 1真人+5AI
POST /api/rooms  body: { nickname, mode: "9" }  // 1真人+8AI
```

## 后端改动

### constants.py

- `Role` 枚举新增 `HUNTER = "hunter"`
- `Phase` 枚举新增 `HUNTER_SHOT = "hunter_shot"`
- 新增 `NINE_PLAYER_ROLES: list[Role]`（3狼3平民1预言家1女巫1猎人）
- 新增 `HUNTER_SHOT_TIMEOUT = 30`

### assign.py

- 支持 `n == 9`：返回 `NINE_PLAYER_ROLES` 的洗牌副本
- `n == 6` 逻辑不变

### state.py

- `GameState` 新增字段：
  - `hunter_can_shoot: bool = True` — 猎人是否还有开枪机会
  - `hunter_just_died: bool = False` — 本轮猎人是否刚出局（用于触发开枪）

### room_manager.py

- `create_room` 接收 `mode: str` 参数替代 `human_slots` / `ai_slots`
- 验证规则：`mode in ("6", "9")`
- 6 人：1 真人 + 5 AI（当前逻辑）
- 9 人：1 真人 + 8 AI

### main.py

- `CreateRoomBody` 改为 `{ nickname, mode: str = "6" }`
- `create_room` 调用 `manager.create_room(nickname, mode=body.mode)`

### 新增 phases/hunter_shot.py

猎人开枪阶段，参考 `night_wolf.py` 的结构：

1. 检查 `state.hunter_can_shoot and state.hunter_just_died`
2. 找到猎人玩家（从已死亡的玩家中找，因为猎人已经出局）
3. 如果猎人已死亡且未开过枪：
   - 广播 `phase_change`（hunter_shot）
   - 可选目标：所有存活玩家
   - 猎人选择：开枪（选 1 目标）或放弃
   - 如果开枪：目标玩家 `alive = false`，`hunter_can_shoot = false`
   - 广播 `death_announce` 补充死讯
4. 重置 `state.hunter_just_died = false`

### engine.py

- `DEFAULT_TIMEOUTS` 新增 `"hunter_shot": 30`
- 在 `run_one_round` 的两个死亡触发点后调用 hunter_shot：

**触发条件：** 猎人因以下方式出局时可以开枪：
- 夜里被狼人刀杀（天亮公布死讯后）
- 白天被公投（放逐）出局（投票结束后当场）

**不触发开枪：** 被女巫毒杀不出开枪机会。

**场景 A：夜间被狼刀杀**
在 `run_day_announce` 之后，如果猎人在被狼杀的死者中：
```
run_day_announce → if hunter among dead → run_hunter_shot → check_winner
```

**场景 B：白天被公投出局**
在 `run_day_vote` 结束后，如果被放逐者是猎人：
```
run_day_vote → if eliminated is hunter → run_hunter_shot → check_winner
```

### prompts.py

- `ROLE_DESCRIPTIONS` 新增猎人条目：
  ```
  "你是猎人（好人阵营）。当你被狼人杀死或被投票放逐时，可以开枪带走任意一名玩家。"
  ```
- `RULES_SUMMARY` 更新为动态描述（根据游戏人数）
- 或者保持静态规则描述，分别写 6 人和 9 人两个版本

### tools.py

- `tools_for_action` 新增 `"hunter_shot"` 分支：
  ```python
  if action == "hunter_shot":
      return [
          _mk("hunter_shot", "Shoot a player as the hunter." + opts_hint, TargetInput),
          _mk("hunter_skip", "Choose not to shoot.", NoInput),
      ]
  ```

### ai.py

- `AIPlayer` 中的 `_is_valid` 和回退路径需支持 `hunter_shot` 动作
- `_log_decision` 增加 `hunter_shot` 日志分支

## 数据流

```
engine.run_one_round()
  ├── run_wolf_kill()           # 狼人选目标
  ├── run_seer_check()          # 预言家查验
  ├── run_witch_action()        # 女巫救/毒
  ├── run_day_announce()        # 公布死讯 → 标记 hunter_just_died
  ├── run_hunter_shot()         # [新] 如果猎人刚死，触发开枪
  ├── check_winner()
  ├── run_day_speech()          # 白天发言
  ├── run_day_vote()            # 白天投票
  │     └── if eliminated is hunter → run_hunter_shot()  [新]
  └── check_winner()
```

## 未改动文件

- `win_check.py` — 猎人属于好人阵营，现有逻辑自动兼容
- `visibility.py` — 角色级别可见性通用，无需改动
- `broadcaster.py` — 无变化
- `events.py` — 无变化
- `vote.py` — 无变化