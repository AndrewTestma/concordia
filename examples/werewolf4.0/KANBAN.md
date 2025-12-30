# 🐺 DeepWerewolf v4.0 开发看板

本文档跟踪 DeepWerewolf 项目 (Concordia + Neo4j + Dify) 的开发进度。

## 📊 状态概览

| 阶段 | 状态 | 进度 |
| :--- | :--- | :--- |
| **阶段 1: 图谱基础** | 🟡 进行中 | 0% |
| **阶段 2: 逻辑映射** | 🔴 待开始 | 0% |
| **阶段 3: 认知闭环** | 🔴 待开始 | 0% |
| **阶段 4: 高级博弈** | 🔴 待开始 | 0% |

---

## 🛠️ 详细任务列表

### 阶段 1: 图谱基础 (基础设施)
*目标: 建立 Neo4j 数据库和 Python 连接层。*

- [ ] **[P0] 项目初始化**
    - [ ] 创建 Python 项目结构。
    - [ ] 配置 `requirements.txt` (neo4j, concordia, 等)。
    - [ ] 创建本地设置说明 `README.md`。
- [ ] **[P0] Neo4j 部署**
    - [ ] 安装/部署 Neo4j 实例。
    - [ ] 定义图谱 Schema (节点: Player, Event; 关系: CLAIM, CHECK, 等)。
    - [ ] 验证 `visibility` 属性约束。
- [ ] **[P1] Neo4j 适配器实现**
    - [ ] 创建 `Neo4jAdapter.py`。
    - [ ] 实现 `connect()` 和 `close()`。
    - [ ] 实现 `clear_graph()` 用于重置。
    - [ ] 实现 `init_game_data(players)` 以初始化节点。

### 阶段 2: 逻辑映射 (数据流)
*目标: 实现对图谱的读取（过滤）和写入（日志记录）。*

- [ ] **[P0] 视角过滤器 (The "Eye")**
    - [ ] 实现 `get_player_view(player_id, role)` 逻辑。
    - [ ] 定义可见性规则 (PUBLIC, WEREWOLF_TEAM, SEER_ONLY)。
    - [ ] 编写 Cypher 查询以获取主观子图。
- [ ] **[P1] 事件解析器与写入器 (The "Hand")**
    - [ ] 实现 `log_public_event(actor, action, target)`。
    - [ ] 实现 `log_private_event(actor, action, target, visibility)`。
    - [ ] 为常见动作（投票、发言、击杀）创建辅助方法。
- [ ] **[P2] 逻辑推理引擎**
    - [ ] 实现 `generate_logic_hints(sub_graph)` 以将图谱路径转换为文本提示。

### 阶段 3: 认知闭环 (引擎)
*目标: 连接身体 (Concordia) 与大脑 (Dify)。*

- [ ] **[P0] 玩家状态管理**
    - [ ] 在 Python 中创建 `PlayerState` 类。
    - [ ] 实现 `suspicion_matrix` 更新。
    - [ ] 实现 `pending_questions` 队列。
- [ ] **[P1] Dify 集成**
    - [ ] 设计 Dify 工作流 `DeepWerewolf_Brain_v3`。
    - [ ] 实现 `DifyClient` 以发送/接收 JSON 载荷。
    - [ ] 构建 `ContextPayload` 组装器（合并图谱 + 状态）。
- [ ] **[P1] 游戏管理员 (GM) 控制器**
    - [ ] 实现主游戏循环 (夜晚 -> 白天 -> 投票)。
    - [ ] 处理阶段转换。
    - [ ] 向 Neo4j 广播事件。

### 阶段 4: 高级博弈 (策略)
*目标: 优化 AI 智能和策略。*

- [ ] **[P2] 夜间策略模块**
    - [ ] 实现 "击杀逻辑" (寻找预言家)。
    - [ ] 实现 "保护逻辑" (女巫救人)。
- [ ] **[P2] 发言生成调优**
    - [ ] 优化 Dify 提示词以实现 "伪装" (狼人表演)。
    - [ ] 优化 "逻辑攻击" (预言家寻找狼人)。
- [ ] **[P3] 集成测试**
    - [ ] 模拟完整的 6 人局游戏脚本。
    - [ ] 验证 "信息差" (预言家知道狼人，村民不知道)。

---

## 📝 注释与决策
*   **可见性规则**: 必须严格遵守所有关系上的 `visibility` 属性。
*   **状态分离**: 切勿将主观怀疑存储在 Neo4j 中；将其保留在 Python 内存/Redis 中。
