# Werewolf AI 陪练游戏

多人在线 6 人局狼人杀，AI 玩家通过 LangChain + 硅基流动 API 参与发言和决策。

## 快速开始

### 后端

```bash
cd backend
conda create -n werewolf python=3.9
conda activate werewolf
pip install -r requirements.txt
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

## 用户系统

项目使用 MySQL + SQLAlchemy（异步）存储用户数据，支持注册和登录。

### 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | 用户ID |
| nickname | VARCHAR(50) UNIQUE | 昵称 |
| phone | VARCHAR(20) UNIQUE | 手机号 |
| account | VARCHAR(50) UNIQUE | 账号 |
| password | VARCHAR(255) | bcrypt 哈希 |
| level | INT DEFAULT 1 | 等级 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### 配置

在 `.env` 中添加：

```ini
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/werewolf
JWT_SECRET=your-secret-key
```

### 初始化

```bash
# 1. 创建数据库
mysql -u root -p < backend/scripts/setup_db.sql

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 创建表
cd backend && python -m scripts.init_db
```

### API

- `POST /api/auth/register` — 注册（body: `{nickname, phone, account, password}`）
- `POST /api/auth/login` — 登录（body: `{account, password}`），account 支持账号或手机号
- `GET /api/auth/rooms/history?user_id=X` — 已结束房间列表
- `GET /api/auth/rooms/history/{room_id}` — 房间复盘详情（含聊天记录）

两者均返回 `{user: {id, nickname, phone, account, level}, token}`。

## 房间复盘

游戏结束后自动记录房间数据和聊天记录。在大厅右侧"我的战绩"列表中可查看已结束的房间，点击"复盘"查看完整聊天记录和玩家角色信息。

### 数据库表

rooms 表记录游戏房间信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK AUTO_INCREMENT | ID |
| room_code | VARCHAR(10) UNIQUE | 房间号 |
| creator_id | INT | 创建人ID |
| creator_nickname | VARCHAR(50) | 创建人昵称 |
| status | VARCHAR(20) | waiting / playing / finished |
| result | VARCHAR(20) | good / werewolf |
| game_log | TEXT | 聊天记录（JSON） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

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