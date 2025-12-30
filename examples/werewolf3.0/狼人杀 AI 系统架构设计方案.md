这是一个面向 **高扩展性（Scalability）** 和 **高鲁棒性（Robustness）** 的狼人杀 AI 系统架构设计方案。

核心理念是：**将“规则裁判”与“角色扮演”彻底分离**。代码负责绝对的逻辑与状态，LLM 负责模糊的推理与伪装。

---

# 狼人杀 AI 系统架构设计方案 (6-12+ 人局通用版)

## 1. 总体架构图 (The Big Picture)

我们将系统划分为四个核心层级：

```mermaid
graph TD
    A[游戏引擎层<br>(Game Engine)] -->|全量状态| B[认知过滤层<br>(Cognitive Filter)]
    B -->|个人视角数据| C[Agent决策层<br>(LLM Core)]
    C -->|结构化动作/发言| D[校验与执行层<br>(Validator & Executor)]
    D -->|合法动作| A
    D -->|非法动作| C
```

---

## 2. 详细模块设计

### 第一层：游戏引擎层 (Game Engine) - Python/Backend
**职责**：上帝视角，维护绝对事实，处理结算优先级，判断胜负。**这里没有 AI，只有 `if/else`。**

#### 2.1 状态数据结构 (Global State)
```python
class GlobalState:
    def __init__(self):
        self.players = {
            "p1": {
                "role": "WITCH",
                "status": "ALIVE",
                "inventory": {"poison": True, "antidote": False}, # 物品栏
                "tags": ["SHERIFF"] # 警长标志
            },
            "p2": {
                "role": "WEREWOLF",
                "status": "ALIVE",
                "linked_to": ["p3", "p4"] # 能够看到的队友
            }
        }
        self.phase = "NIGHT_ACTION" // 当前阶段
        self.pending_actions = []   // 等待结算的动作队列
        self.history_log = []       // 全局事件日志
```

#### 2.2 结算逻辑 (Resolution Logic)
必须硬编码复杂的结算优先级（例如：守卫守了 -> 狼刀 -> 女巫救 -> 还是死/奶穿）。
*   **配置化规则**：通过 Config 文件定义板子（例如 `12_player_standard.json`），定义神职数量、胜利条件。

---

### 第二层：认知过滤层 (Cognitive Filter) - The Lens
**职责**：解决幻觉的核心。根据角色身份，从 Global State 中提取“他应该知道的信息”，生成 **Context JSON**。

#### 2.1 动态构建 Prompt 上下文
系统根据 `player_id` 自动生成以下 JSON 注入给 LLM：

*   **身份与技能 (Static)**：
    > "你是女巫。你有一瓶毒药（可用），一瓶解药（已用）。"
*   **视野信息 (Dynamic - 关键！)**：
    *   **狼人**：注入 `{"teammates": ["p2", "p3"]}`。
    *   **预言家**：注入历史查验表 `{"night1": {"target": "p2", "result": "WEREWOLF"}}`。
    *   **平民**：注入 `{"known_info": "None"}`。
*   **合法动作集 (Constraints)**：
    > "你当前可执行的动作：['POISON', 'SKIP']。注意：你不能使用解药，也不能自救。"

**设计意图**：LLM 不需要回忆自己有没有药，Context 里写着 `poison: True` 就是有。

---

### 第三层：Agent 决策层 (LLM Core) - The Brain
**职责**：基于 Filter 提供的信息，进行推理、伪装和决策。

#### 3.1 提示词工程 (Prompt Engineering) - 结构化思维
强制 LLM 输出 JSON，包含“内心戏”和“公开行为”。

**System Prompt 模板：**
> 你是 [角色名]。
> **绝对准则**：
> 1. 你的思考必须基于 `system_injected_facts`（系统注入事实）。
> 2. 如果你是狼人，你在 `public_speech` 中必须伪装，但在 `inner_thought` 中必须诚实。
> 3. 你的输出必须符合 JSON 格式。

**User Input (Context):**
```json
{
  "phase": "DAY_DISCUSSION",
  "dead_last_night": ["p5"],
  "system_injected_facts": {
    "my_role": "WEREWOLF",
    "teammates": ["p2"],
    "who_we_killed": "p5"
  },
  "discussion_history_summary": "p1跳预言家查杀p2..."
}
```

#### 3.2 记忆管理 (Memory Management)
12人局对话量巨大，不能全量塞入 Context。
*   **短期记忆**：最近 5-10 条完整对话。
*   **长期记忆**：使用 **Event Summarizer**。每晚生成一份摘要：
    > "Day 1: p1 (Seer) checked p3 (Good). p4 voted out."
    LLM 读取的是摘要列表 + 最新对话。

---

### 第四层：校验与执行层 (Validator & Executor) - The Gatekeeper
**职责**：防止 LLM 乱来（比如平民说要发动毒药，或者预言家说验人结果不明）。

#### 4.1 规则校验器 (Rule Validator)
在 LLM 返回 JSON 后，**先不执行，先校验**：

```python
def validate_action(agent_response, player_real_state):
    action = agent_response['action']

    # 校验1：你有这个技能吗？
    if action == 'POISON' and player_real_state['role'] != 'WITCH':
        return False, "Error: You are not a Witch."

    # 校验2：你有这个物品吗？
    if action == 'POISON' and not player_real_state['inventory']['poison']:
        return False, "Error: You have no poison left."

    # 校验3：逻辑自洽性（针对发言）
    if "查验不明" in agent_response['speech'] and player_real_state['role'] == 'SEER':
         return False, "Error: Seer results must be definitive."

    return True, "OK"
```

#### 4.2 错误回环 (Feedback Loop)
如果校验失败，将错误信息作为 Prompt 发回给 LLM，强制其重试（Retry）：
> "系统警告：你的决策无效。原因：你没有解药了。请重新决策。"

---

## 3. 扩展性设计 (Scalability Strategy)

如何从 6 人扩展到 12 人 + 复杂身份？

### 3.1 角色配置化 (Config-Driven Roles)
不要在代码里写死 `if role == 'SEER'`。定义一个 `RoleAbility` 接口。

```json
// roles_config.json
"WITCH": {
    "abilities": ["poison", "save"],
    "night_priority": 20,
    "can_self_save": false
},
"HUNTER": {
    "abilities": ["shoot_on_death"],
    "trigger": "passive"
}
```

### 3.2 动态通信协议
定义一套标准的动作协议，支持任意扩展。

**Action Schema:**
```json
{
  "action_type": "USE_ABILITY",
  "ability_name": "POISON", // 或者是 "GUARD", "CHECK", "CHARM" (丘比特)
  "targets": ["p3"],
  "meta_data": {}
}
```

### 3.3 第三方阵营支持 (Third-Party Factions)
对于“人狼恋”、“混血儿”等复杂情况，引擎层需要维护动态的 **WinCondition**。

*   **传统**：`Team = [WEREWOLF]` vs `Team = [VILLAGER, GOD]`
*   **第三方**：引擎检测到丘比特连了人狼，动态创建一个 `Team ID: LOVE_LINK`。
*   **注入**：在 `Cognitive Filter` 层，告诉这两个玩家："你的胜利条件已改变，你必须杀光其他人。"

---

## 4. 实施路线图建议

1.  **阶段一：重构引擎 (Engine Refactor)**
    *   抛弃目前的简单脚本。
    *   建立 `GlobalState` 和 `Player` 类。
    *   实现“上帝视角”的结算逻辑，确保 100% 准确。

2.  **阶段二：实现过滤器 (Filter Implementation)**
    *   编写代码，根据角色生成 `system_injected_facts`。
    *   测试：打印出预言家、狼人、平民在同一回合看到的 Context 是否不同。

3.  **阶段三：接入校验器 (Validator)**
    *   先做简单的规则校验（有无技能）。
    *   再做逻辑校验（检测发言中的关键词）。

4.  **阶段四：增加角色**
    *   有了上述框架，增加“守卫”只需：
        1.  Config 加角色。
        2.  Engine 加结算优先级。
        3.  Prompt 加一句技能描述。
        4.  Validator 不需要改（如果设计得通用）。

通过这套方案，你可以轻松驾驭 12 人甚至 20 人的复杂板子，因为**复杂度被代码封装了，LLM 只需要在限定范围内做“填空题”和“小作文”**。
