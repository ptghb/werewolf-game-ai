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