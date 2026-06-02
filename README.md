# Werewolf AI 陪练游戏

多人在线狼人杀，AI 玩家通过 LangChain + 任意 OpenAI 兼容 API（如硅基流动、DeepSeek、OpenAI 等）参与发言和决策。支持 6/9/12 人三种模式。

**技术栈：** FastAPI + React 19 + LangChain + SQLAlchemy + MySQL + WebSocket

## 功能特性

- **三种人数模式**：6 人（3 狼 + 女巫 + 预言家 + 村民）、9 人（+ 猎人）、12 人（+ 猎人 + 白痴）
- **AI 玩家**：基于 LangChain function calling，支持 8 种人格风格，可接入任意 OpenAI 兼容 API
- **上帝视角**：观战者可查看全部角色信息
- **VIP 优先选角**：VIP 用户开房时可指定偏好角色
- **用户自定义 LLM**：可在前台管理多个 LLM Token 配置（base_url / api_key / model），支持在线测试
- **房间复盘**：游戏结束后自动保存完整聊天记录，支持历史回溯

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 18
- MySQL >= 5.7

### 1. 数据库初始化

```bash
# 创建数据库
mysql -u root -p < backend/scripts/setup_db.sql

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 创建表
python -m scripts.init_db
```

### 2. 配置

```bash
cd backend
cp .env.example .env   # 编辑填入 LLM_API_KEY、DATABASE_URL、JWT_SECRET
```

`.env` 配置项：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | LLM API 密钥 | — |
| `LLM_BASE_URL` | API 地址（OpenAI 兼容格式） | `https://api.siliconflow.cn/v1` |
| `LLM_MODEL` | 模型名称 | `Qwen/Qwen2.5-7B-Instruct` |
| `DATABASE_URL` | MySQL 连接串 | `mysql+aiomysql://root:password@localhost:3306/werewolf` |
| `JWT_SECRET` | JWT 签名密钥 | — |
| `PORT` | 服务端口 | `8000` |

LLM 配置兼容任何 OpenAI 格式的 API 服务，只需修改 `LLM_BASE_URL` 和 `LLM_MODEL` 即可切换供应商。

### 3. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 创建或加入房间。

## 项目结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口，HTTP + WebSocket 路由
│   ├── config.py               # Settings 配置类（dotenv）
│   ├── protocol.py             # WebSocket 消息协议（Pydantic）
│   ├── auth_routes.py          # 认证 API（注册/登录/战绩）
│   ├── llm_routes.py           # LLM Token CRUD API
│   ├── database/               # ORM 模型、Schema、会话管理、JWT 认证
│   ├── game/
│   │   ├── engine.py           # 游戏引擎（状态机主循环）
│   │   ├── state.py            # 游戏状态与玩家状态
│   │   ├── events.py           # 事件模型 + 广播
│   │   ├── constants.py        # 角色/阶段/人数配置
│   │   ├── assign.py           # 角色分配
│   │   ├── vote.py             # 投票计票
│   │   ├── win_check.py        # 胜负判定
│   │   └── phases/             # 各阶段实现（狼刀/预言家/女巫/发言/投票/猎人）
│   ├── players/
│   │   ├── base.py             # Player 抽象协议
│   │   ├── human.py            # 真人玩家（WebSocket）
│   │   └── ai.py               # AI 玩家（LangChain + LLM）
│   ├── rooms/
│   │   ├── room.py             # Room 数据模型
│   │   └── room_manager.py     # 房间管理器
│   └── ai/
│       ├── llm.py              # ChatOpenAI 工厂
│       ├── prompts.py          # 系统提示词构建
│       ├── personas.py         # AI 人格定义（8 种）
│       └── tools.py            # LangChain 工具定义
├── scripts/
│   ├── setup_db.sql            # 建库 SQL
│   └── init_db.py              # 建表脚本
└── tests/                      # 30+ 测试文件
    ├── test_ai_config.py
    ├── test_full_game_ai_only.py
    ├── test_phase_*.py         # 各阶段测试
    └── test_llm_smoke.py       # 真实 LLM 烟测

frontend/
├── src/
│   ├── main.jsx                # React 入口
│   ├── App.jsx                 # 根组件（路由：Auth/Lobby/Game/Review）
│   ├── store/gameStore.js      # Zustand 全局状态
│   ├── ws/client.js            # WebSocket 客户端（重连/去重/ACK）
│   ├── pages/
│   │   ├── AuthPage.jsx        # 登录/注册
│   │   ├── Lobby.jsx           # 大厅（建房/战绩/LLM 设置）
│   │   ├── Game.jsx            # 游戏页面
│   │   └── Review.jsx          # 复盘页面
│   ├── components/
│   │   ├── RoundTable.jsx      # 圆桌座位布局
│   │   ├── PlayerSeat.jsx      # 玩家座位
│   │   ├── ChatPanel.jsx       # 聊天面板
│   │   ├── ActionModal.jsx     # 操作弹窗
│   │   ├── PhaseBanner.jsx     # 阶段横幅 + 倒计时
│   │   ├── NightOverlay.jsx    # 天黑动画
│   │   └── ...
│   └── styles/theme.css        # 深色主题样式
├── index.html
├── vite.config.js              # Vite 配置（代理 /api → :8000）
└── package.json
```

## API 总览

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 `{nickname, phone, account, password}` |
| POST | `/api/auth/login` | 登录 `{account, password}`（account 支持账号或手机号） |
| GET | `/api/auth/rooms/history?user_id=X` | 已结束房间列表 |
| GET | `/api/auth/rooms/history/{room_id}` | 房间复盘详情（含聊天记录） |

登录/注册返回 `{user: {id, nickname, phone, account, level}, token}`。

### 房间

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/rooms` | 创建房间 `{user_id, nickname, mode, god_mode}` |
| POST | `/api/rooms/{code}/join` | 加入房间 `{nickname}` |

### LLM Token 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/llm-tokens?user_id=X` | 列表 |
| POST | `/api/llm-tokens?user_id=X` | 创建 `{base_url, api_key, model}` |
| PUT | `/api/llm-tokens/{id}` | 更新 |
| DELETE | `/api/llm-tokens/{id}` | 删除（软删除） |
| POST | `/api/llm-tokens/{id}/test` | 测试连接 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws` | 游戏实时通信 |

连接后首条消息须为 `{type: "hello", room, player_id}`（或 `spectator: true` 作为观战者加入）。支持消息类型：`action` / `chat` / `ack` / `start_game`。

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/healthz` | `{"ok": true}` |

## 数据库表

### `users`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | 用户 ID |
| nickname | VARCHAR(50) UNIQUE | 昵称 |
| phone | VARCHAR(20) UNIQUE | 手机号 |
| account | VARCHAR(50) UNIQUE | 账号 |
| password | VARCHAR(255) | bcrypt 哈希 |
| level | INT DEFAULT 1 | 等级 |
| vip | INT DEFAULT 0 | VIP 标识 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### `rooms`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | ID |
| room_code | VARCHAR(10) UNIQUE | 房间号 |
| creator_id | INT | 创建人 ID |
| creator_nickname | VARCHAR(50) | 创建人昵称 |
| status | VARCHAR(20) | waiting / playing / finished |
| result | VARCHAR(20) | good / werewolf |
| game_log | TEXT | 聊天记录（JSON） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### `llmtokens`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | ID |
| user_id | INT | 用户 ID |
| base_url | VARCHAR(255) | API 地址 |
| api_key | VARCHAR(512) | API 密钥 |
| model | VARCHAR(100) | 模型名称 |
| enable | SMALLINT | 启用状态 |
| del_flag | SMALLINT | 删除标记 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 测试

```bash
cd backend

# 单元 + 集成测试（无需 LLM）
pytest

# LLM 烟测（需配置 LLM_API_KEY）
pytest -m llm
```

## 架构设计

- **服务端权威**：每房间一个 `asyncio.Task` 串行推进状态机，状态变更由服务端统一计算和广播
- **阶段驱动**：GameEngine 按顺序调度 wolf_kill → seer_check → witch_action → day_announce → hunter_shot → day_speech → day_vote → win_check，支持最多 20 回合
- **Player 抽象**：`Player` 协议统一人类玩家（WebSocket 驱动）和 AI 玩家（LangChain function calling），事件通过可见性过滤广播
- **事件系统**：`GameEvent` 带 audience 字段（all / role / player / dead），`Broadcaster` 过滤后推送；前端 Zustand store 去重消费
- **AI 可替换**：`build_llm()` 工厂基于 `langchain_openai.ChatOpenAI`，base_url 可指向任何 OpenAI 兼容 API；用户可在前端管理自己的 LLM 配置
- **前端响应式**：桌面端圆桌布局，移动端纵向列表；WebSocket 自动重连 + 序列号去重 + ACK 确认