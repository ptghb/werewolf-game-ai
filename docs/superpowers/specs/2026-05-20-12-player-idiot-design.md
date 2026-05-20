# 12 人局与白痴角色设计

Date: 2026-05-20
Status: Design (awaiting implementation plan)

## 1. 目标

在现有狼人杀后端中新增 12 人场，并实现白痴角色规则。

12 人场角色配置：
- 4 狼人
- 1 预言家
- 1 女巫
- 1 猎人
- 1 白痴
- 4 平民

白痴属于好人阵营。白痴被公投命中时翻牌免死；翻牌后仍存活、仍可白天发言，但失去投票权，且不能再次成为公投候选。白痴翻牌后仍可被夜间击杀或其他非公投死亡来源杀死。

## 2. 范围

本次改动采用最小扩展方案，不重构角色能力系统。

包含：
- 新增 `Role.IDIOT`
- 新增 12 人角色池
- 房间创建支持 `mode="12"`
- AI 规则提示增加 12 人场和白痴说明
- 白天投票阶段实现白痴翻牌免死、翻牌后禁投与不可被投
- 新增服务端事件 `idiot_reveal`
- 增加后端测试覆盖

不包含：
- 抽象通用角色能力表
- 前端复杂 UI 重构
- 新的夜间技能阶段
- 改变现有 6 人局、9 人局规则

## 3. 数据模型

### 3.1 角色枚举

`backend/app/game/constants.py` 的 `Role` 增加：

```python
IDIOT = "idiot"
```

### 3.2 角色池

新增 12 人角色池常量，例如 `TWELVE_PLAYER_ROLES`：

```python
[
    WEREWOLF, WEREWOLF, WEREWOLF, WEREWOLF,
    SEER, WITCH, HUNTER, IDIOT,
    VILLAGER, VILLAGER, VILLAGER, VILLAGER,
]
```

`assign_roles(n)` 支持 `n == 12`，并继续对角色池洗牌。

### 3.3 玩家状态

`PlayerState` 增加白痴翻牌状态，例如：

```python
idiot_revealed: bool = False
```

语义：
- 仅对白痴角色有意义
- 默认 `False`
- 白痴第一次被公投命中时置为 `True`
- 置为 `True` 不改变 `alive`

## 4. 房间模式

`RoomManager.create_room(mode="12")` 创建 12 人房：
- 总人数 12
- 默认 1 真人 + 11 AI
- 其他逻辑沿用现有模式：房主占 seat 0，AI 填充剩余座位，真人加入时替换 AI

无效模式仍抛出 `ValueError`。

## 5. 白痴投票规则

### 5.1 未翻牌白痴

未翻牌白痴与普通存活玩家相同：
- 可以白天发言
- 可以参与第一轮投票
- 可以参与 PK 轮投票
- 可以成为第一轮投票候选
- 可以成为 PK 候选

### 5.2 被公投命中

当白天投票或 PK 投票的最终出局目标是未翻牌白痴：
- 不将其 `alive` 置为 `False`
- 将其 `idiot_revealed` 置为 `True`
- 广播 `idiot_reveal` 事件
- 返回结果中不应把它视为真正死亡出局
- 不触发遗言
- 不触发猎人开枪逻辑

推荐 `run_day_vote` 返回结构保留 `eliminated` 表示真正死亡出局，并增加 `idiot_revealed` 表示本轮翻牌玩家：

```python
{"eliminated": None, "idiot_revealed": player_id, "pk_used": bool, "votes": votes}
```

### 5.3 翻牌后白痴

翻牌白痴仍然 `alive=True`，并且：
- 继续参与 `day_speech`
- 不再作为投票人收到 `day_vote` 或 `day_vote_pk` 请求
- 不再出现在任何投票选项中
- 不再出现在 PK 候选人中
- 仍可被狼人夜间击杀
- 仍可被女巫毒杀
- 非公投死亡时正常广播 `death_announce`

`day_vote` 应通过统一判断函数过滤投票人和候选人，避免第一轮与 PK 轮规则不一致。例如：

```python
def _can_vote(player_state):
    return player_state.alive and not (player_state.role == Role.IDIOT and player_state.idiot_revealed)


def _can_be_voted(player_state):
    return player_state.alive and not (player_state.role == Role.IDIOT and player_state.idiot_revealed)
```

## 6. 事件协议

新增服务端事件类型：

```text
idiot_reveal
```

推荐 payload：

```json
{
  "player_id": "p3"
}
```

该事件表示白痴因公投命中翻牌免死，不表示死亡。它应与 `death_announce` 区分，方便前端和 AI 事件记忆明确理解状态变化。

`backend/app/protocol.py` 的 `ServerMessage.type` 允许值需要加入 `idiot_reveal`。如果项目当前未对 payload 建强 schema，可以先使用 `payload: Any`，无需新增复杂模型。

## 7. AI 提示

`backend/app/ai/prompts.py` 需要：
- `ROLE_DESCRIPTIONS` 增加白痴身份说明
- `RULES_SUMMARY` 增加 12 人局配置
- `RULES_SUMMARY` 增加白痴规则：公投翻牌免死，翻牌后可发言但不可投票、不可再被投票，仍可被杀

白痴作为好人阵营，胜利目标与其他好人一致。

## 8. 胜负判定

当前胜负判定以存活狼人数量和存活非狼人数量计算。白痴属于非狼人且翻牌后仍 `alive=True`，因此自然计入好人存活数。

无需改动核心胜负逻辑，但需要测试证明存活白痴计为好人。

## 9. 测试计划

新增或更新后端测试：

1. `assign_roles(12)` 返回 12 张牌，且配比为 4 狼、1 预言家、1 女巫、1 猎人、1 白痴、4 平民。
2. `assign_roles` 支持 6、9、12，其他人数仍报错。
3. `RoomManager.create_room(mode="12")` 创建 12 名玩家。
4. 未翻牌白痴能作为投票人参与投票。
5. 未翻牌白痴能作为投票候选，被公投命中时不死亡。
6. 白痴翻牌时广播 `idiot_reveal`，不广播投票死亡 `death_announce`。
7. 翻牌白痴后续不再收到投票请求。
8. 翻牌白痴后续不出现在投票选项和 PK 候选中。
9. 翻牌白痴仍参与白天发言。
10. 翻牌白痴被夜间击杀时正常死亡并广播 `death_announce`。
11. 胜负判定中存活白痴计为好人。

## 10. 兼容性与风险

- 6 人局和 9 人局角色池不变。
- 已有猎人逻辑依赖 `run_day_vote` 的 `eliminated` 字段；白痴翻牌不应设置 `eliminated`，避免误触发猎人相关逻辑。
- 投票过滤必须同时应用于第一轮和 PK 轮，否则翻牌白痴可能仍参与或成为 PK 候选。
- 白痴翻牌不是死亡，不能触发遗言、死亡公告或胜负判定中的人数减少。
