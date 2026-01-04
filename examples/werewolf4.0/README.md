# DeepWerewolf v4.0

DeepWerewolf 是一个结合了 Concordia (Agent 框架) 和 Neo4j (图数据库) 的狼人杀游戏模拟项目。本项目旨在通过图谱技术增强 Agent 的推理能力和记忆持久化。

## 🛠️ 环境设置

### 1. 安装依赖

请确保已安装 Python 3.10+。

```bash
pip install -r requirements.txt
```

### 2. Neo4j 配置

本项目使用 Neo4j 存储游戏状态和记忆。

**连接信息:**
- **地址 (Bolt):** `bolt://117.50.34.101:7687` (根据提供的 HTTP 地址推断)
- **地址 (HTTP):** `http://117.50.34.101:7474`
- **用户名:** `neo4j`
- **密码:** `Asd7535437`

建议创建一个 `.env` 文件来管理环境变量 (需安装 `python-dotenv`):

```env
NEO4J_URI=bolt://117.50.34.101:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Asd7535437
```

## 🚀 快速开始

### 初始化与清理

使用 `clean_graph.py` 脚本可以快速清理数据库并验证连接。

```bash
python clean_graph.py
```

### 运行查询

使用 `query_graph.py` 执行自定义 Cypher 查询。

```bash
python query_graph.py
```

## 📁 项目结构

- `Neo4jAdapter.py`: 负责与 Neo4j 数据库交互的核心适配器类。
- `TheEye.py`: 实现视角过滤器，负责根据玩家身份获取主观图谱。
- `TheHand.py`: 负责将事件写入 Neo4j 数据库的事件写入器。
- `LogicEngine.py`: 逻辑推理引擎，负责将图谱数据转换为自然语言提示。
- `DifyClient.py`: Dify API 客户端，负责组装上下文并与 Dify 平台通信。
- `GameMaster.py`: 游戏主控制器，管理游戏循环、阶段转换和玩家代理协调。
- `StrategyModule.py`: 夜间策略模块，负责为不同角色生成战术目标 (Objective)。
- `verify_eye.py`: 用于验证视角逻辑的测试脚本。
- `verify_dify.py`: 用于验证 Dify 集成逻辑的测试脚本。
- `clean_graph.py`: 用于重置数据库的实用脚本。
- `query_graph.py`: 用于测试查询的实用脚本。
- `requirements.txt`: 项目依赖。
- `KANBAN.md`: 开发进度看板。

## 🧩 核心功能 (开发中)

### 👁️ 视角过滤器 (The Eye)

`TheEye` 类负责模拟玩家的主观视角。它根据玩家的角色 (Role) 和 ID，过滤掉不可见的信息。

**可见性规则:**
- `PUBLIC`: 所有玩家可见 (例如：公开这言)。
- `WEREWOLF_TEAM`: 仅狼人阵营可见 (例如：夜间击杀)。
- `SEER_ONLY`: 仅预言家可见 (例如：查验身份)。
- `PRIVATE`: 仅该行为的执行者可见 (例如：内心独白)。

**使用示例:**

```python
from Neo4jAdapter import Neo4jAdapter
from TheEye import TheEye

adapter = Neo4jAdapter(...)
eye = TheEye(adapter)

# 获取狼人的视角
wolf_view = eye.get_player_view(player_id="p2", role="Werewolf")
```

### ✋ 事件写入器 (The Hand)

`TheHand` 类负责将游戏中的各种事件（如发言、投票、击杀）记录到图数据库中，并管理事件的可见性。

**功能:**
- **事件记录**: 支持公开事件和私有事件的记录。
- **辅助方法**: 提供了 `log_vote`, `log_kill`, `log_check`, `log_speech` 等快捷方法。

**使用示例:**

```python
from Neo4jAdapter import Neo4jAdapter
from TheHand import TheHand

adapter = Neo4jAdapter(...)
hand = TheHand(adapter)

# 记录一次投票
hand.log_vote(voter_id="p1", target_id="p2", round_num=1)
```

### 🧠 玩家状态管理 (Player State)

`PlayerState` 类负责管理玩家的短期记忆和主观判断，这些信息不存储在公共的 Neo4j 图谱中。

**功能:**
- **怀疑矩阵 (Suspicion Matrix)**: 跟踪对其他玩家的怀疑程度 (0-100)。
- **待办问题 (Pending Questions)**: 记录需要进一步探究的问题队列。

**使用示例:**

```python
from PlayerState import PlayerState

# 初始化玩家状态
state = PlayerState(player_id="p1", player_name="Alice", role="Villager")
state.init_suspicion(["p1", "p2", "p3"])

# 更新怀疑度
state.update_suspicion("p2", 10.0, reason="发言逻辑混乱")
current_score = state.get_suspicion("p2")
```

- **图谱基础**: 连接 Neo4j，定义 Schema。
- **逻辑映射**: 实现视角过滤器 ("The Eye") 和事件写入器 ("The Hand")。
- **认知闭环**: 集成 Dify 和 Concordia。
- **高级博弈**: 实现复杂的推理策略。
