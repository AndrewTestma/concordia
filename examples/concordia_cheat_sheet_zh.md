# Concordia 模拟速查表

构建和运行 Concordia 模拟的简明指南。

---

## 核心概念

| 概念 | 描述 |
|---------|-------------|
| **Prefab** | 用于构建实体（代理或游戏管理员）的可重用配方 |
| **InstanceConfig** | 指定使用哪个 prefab 及其参数的配置 |
| **Config** | 包含 prefabs、instances、前提的完整模拟配置 |
| **Simulation** | 协调实体和游戏管理员的主要对象 |
| **Entity** | 可以观察世界并采取行动的代理 |
| **Game Master** | 控制模拟流程，解析动作，生成观察结果 |
| **AssociativeMemoryBank** | 使用嵌入向量存储和检索记忆 |

---

## 最小模拟设置

```python
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs import game_master as game_master_prefabs
from concordia.prefabs.simulation import generic as simulation
from concordia.typing import prefab as prefab_lib
from concordia.utils import helper_functions

# 1. 加载可用的 prefabs
prefabs = {
    **helper_functions.get_package_classes(entity_prefabs),
    **helper_functions.get_package_classes(game_master_prefabs),
}

# 2. 定义代理实例
instances = [
    prefab_lib.InstanceConfig(
        prefab="basic__Entity",
        role=prefab_lib.Role.ENTITY,
        params={"name": "Alice", "goal": "交新朋友"},
    ),
    prefab_lib.InstanceConfig(
        prefab="basic__Entity",
        role=prefab_lib.Role.ENTITY,
        params={"name": "Bob", "goal": "找商业伙伴"},
    ),
]

# 3. 添加游戏管理员
instances.append(
    prefab_lib.InstanceConfig(
        prefab="dialogic__GameMaster",
        role=prefab_lib.Role.GAME_MASTER,
        params={
            "name": "对话规则",
            "next_game_master_name": "对话规则",
        },
    )
)

# 4. 创建配置
config = prefab_lib.Config(
    default_premise="Alice 和 Bob 在咖啡店相遇。",
    default_max_steps=20,
    prefabs=prefabs,
    instances=instances,
)

# 5. 初始化并运行模拟
sim = simulation.Simulation(config=config, model=model, embedder=embedder)
results = sim.play()
```

---

## 模拟引擎

引擎控制时间流、执行顺序以及代理如何更新状态。

| 引擎 | 执行流程 | 状态处理 | 最佳用途 |
| :--- | :--- | :--- | :--- |
| **Sequential** | 回合制。一个代理行动，然后游戏管理员解析。 | 代理立即观察到每个事件。 | 叙事模拟、对话、依赖性动作。 |
| **Simultaneous** | 批次制。所有代理提交动作，然后游戏管理员解析所有动作。 | 代理在回合结束前看不到其他人的动作。 | 市场、投票、博弈论场景（如囚徒困境）。 |
| **Sequential Questionnaire** | 逐个迭代问题/代理。 | 在每次回答后更新代理记忆。 | 访谈、先前上下文影响下一个答案的序列。 |
| **Parallel Questionnaire** | 同时向代理发送批量问题。 | **无状态**：代理基于当前状态回答，不更新批次中的记忆。 | 调查、心理测量学、高效收集独立数据点。 |

**用法：**
```python
from concordia.environment.engines import sequential, simultaneous

# 1. 顺序执行（默认）
engine = sequential.Sequential()

# 2. 同时执行（用于快速模拟与同时行动）
engine = simultaneous.Simultaneous()

simultaneous_simulation = simulation.Simulation(
    config=config,
    model=model,
    embedder=embedder,
    engine=engine,
)
```

---

## Prefab 角色

```python
from concordia.typing import prefab as prefab_lib

prefab_lib.Role.ENTITY       # 在世界中行动的代理
prefab_lib.Role.GAME_MASTER  # 控制模拟，生成事件
prefab_lib.Role.INITIALIZER  # 运行一次以设置初始状态
```

---

## 内置 Prefabs

### 实体 Prefabs
| Prefab | 描述 |
| :--- | :--- |
| `basic__Entity` | 标准的"三个关键问题"代理。通过询问确定动作：*这是什么情况？我是谁？我会做什么？* |
| `basic_with_plan__Entity` | 通过在行动前生成**计划**来扩展基本代理。 |
| `basic_scripted__Entity` | 使用"三个关键问题"进行内部思考，但遵循预定义脚本进行动作。 |
| `conversational__Entity` | 针对对话优化。明确平衡"聚合"（保持话题）和"发散"（引入新想法）。 |
| `minimal__Entity` | 仅有记忆、指令和观察的基本代理。高度可配置，适用于自定义扩展。 |
| `fake_assistant_with_configurable_system_prompt__Entity` | 使代理表现得像标准AI助手（乐于助人、无害）或任何自定义系统提示的包装器。 |

### 游戏管理员 Prefabs
| Prefab | 描述 |
| :--- | :--- |
| `generic__GameMaster` | 灵活、通用的游戏管理员。自定义模拟的良好起点。 |
| `dialogic__GameMaster` | 专门用于纯对话。支持固定、随机或游戏管理员选择的轮流方式。 |
| `dialogic_and_dramaturgic__GameMaster` | 管理结构化为**场景**的对话（例如，"序言"、"第一集"）。 |
| `situated__GameMaster` | 管理具有特定**位置**的模拟，并跟踪代理所在位置。 |
| `situated_in_time_and_place__GameMaster` | 最复杂的世界模型。跟踪**时间**（时钟）和**位置**，支持昼夜循环和移动。 |
| `formative_memories_initializer__GameMaster` | **初始化器**：在开始时运行一次，为代理生成背景故事和童年记忆。 |
| `interviewer__GameMaster` | 向代理管理多项选择或固定问题问卷。 |
| `open_ended_interviewer__GameMaster` | 管理开放式问卷，使用嵌入向量处理答案。 |
| `game_theoretic_and_dramaturgic__GameMaster` | 专门用于包装在叙事场景中的矩阵游戏（如囚徒困境）。 |
| `marketplace__GameMaster` | 专门用于经济模拟。支持购买、销售和库存管理。 |
| `psychology_experiment__GameMaster` | 用于运行由自定义观察/动作组件定义的心理学实验的通用外壳。 |
| `scripted__GameMaster` | 强制模拟遵循严格的线性事件脚本。 |

---

## 模拟示例

虽然"最小模拟设置"显示了代码结构，但以下是您可能构建的两种常见*类型*的模拟，以及所需的特定 prefabs 和逻辑。

### 1. 叙事模拟（例如，爱丽丝梦游仙境）
**最佳用途：** 讲故事、角色扮演和结果未知的开放式互动。

**关键组件：**

*   **实体：** `basic__Entity`（标准代理）可选 `goals`。
*   **游戏管理员：** `generic__GameMaster`（管理轮流和观察）。
*   **前提：** 设置初始场景（例如，"爱丽丝看到一只白兔..."）。

在此场景中，代理基于其角色描述和 `default_premise` 行动。没有严格的"游戏规则"或分数，只有互动。

```python
# 1. 定义实体
alice = prefab_lib.InstanceConfig(
    prefab='basic__Entity',
    role=prefab_lib.Role.ENTITY,
    params={'name': 'Alice'},
)
rabbit = prefab_lib.InstanceConfig(
    prefab='basic__Entity',
    role=prefab_lib.Role.ENTITY,
    params={
        'name': 'White Rabbit',
        'goal': '准时到达女王那里',
    },
)

# 2. 通用游戏管理员（固定顺序）
gm = prefab_lib.InstanceConfig(
    prefab='generic__GameMaster',
    role=prefab_lib.Role.GAME_MASTER,
    params={
        'name': '默认规则',
        'acting_order': 'fixed', # 选项：'fixed'、'random' 或 'u-go-i-go'（主要用于2个玩家）
    },
)

# 3. 使用通用模拟
config = prefab_lib.Config(
    default_premise="爱丽丝看到一只拿着怀表奔跑的白兔。",
    default_max_steps=10,
    prefabs=prefabs,
    instances=[alice, rabbit, gm],
)
```

### 2. 博弈论模拟（例如，卖饼干）
**最佳用途：** 游戏（囚徒困境）和具有特定"动作"和"收益"的场景。

**关键组件：**

*   **实体：** `basic__Entity` 或自定义代理。
*   **游戏管理员：** `game_theoretic_and_dramaturgic__GameMaster`。这个GM至关重要，因为它可以：
    *   强制执行结构化的**场景**（例如，讨论与决策的特定回合）。
    *   使用 `action_to_scores` 计算**收益**。
    *   通过 `scores_to_observation` 提供反馈。

在此场景中，我们通常有一个"对话"阶段（自由文本）和一个"决策"阶段（受限选择）。

```python
from concordia.typing import scene as scene_lib

# 1. 定义场景
# 对话场景（自由发言）
conversation_scene = scene_lib.SceneTypeSpec(
    name='对话',
    game_master_name='对话规则',
    action_spec=entity_lib.free_action_spec(
        call_to_action=entity_lib.DEFAULT_CALL_TO_SPEECH
    ),
)

# 决策场景（二元选择）
decision_scene = scene_lib.SceneTypeSpec(
    name='决策',
    game_master_name='决策规则',
    action_spec={
        'Alice': entity_lib.choice_action_spec(
            call_to_action='买饼干吗？',
            options=['是', '否'],
        ),
    },
)

# 场景序列
scenes = [
    scene_lib.SceneSpec(
        scene_type=conversation_scene,
        participants=['Alice', 'Bob'],
        num_rounds=4,
        premise={'Alice': ['Bob 向你走来。'], 'Bob': ['你走向 Alice。']},
    ),
    scene_lib.SceneSpec(
        scene_type=decision_scene,
        participants=['Alice'],
        num_rounds=1,
        premise={'Alice': ['决定是否买饼干。']},
    ),
]

# 2. 定义收益（博弈论）
def action_to_scores(joint_action):
    # 如果 Alice 购买（是），她失去金钱（-1），Bob 获得（1）
    if joint_action['Alice'] == '是':
        return {'Alice': -1, 'Bob': 1}
    return {'Alice': 0, 'Bob': 0}

def scores_to_observation(scores):
    return {p: f"最终得分：{s}" for p, s in scores.items()}

# 3. 配置游戏管理员
instances = [
    # ... 实体 Alice 和 Bob ...
    prefab_lib.InstanceConfig(
        prefab='game_theoretic_and_dramaturgic__GameMaster',
        role=prefab_lib.Role.GAME_MASTER,
        params={
            'name': '决策规则',
            'scenes': scenes,
            'action_to_scores': action_to_scores,
            'scores_to_observation': scores_to_observation,
        },
    ),
    prefab_lib.InstanceConfig(
        prefab='dialogic_and_dramaturgic__GameMaster',
        role=prefab_lib.Role.GAME_MASTER,
        params={
            'name': '对话规则',
            'scenes': scenes,
        },
    ),
    # 可选：初始化器以设置初始记忆/上下文
    prefab_lib.InstanceConfig(
        prefab='formative_memories_initializer__GameMaster',
        role=prefab_lib.Role.INITIALIZER,
        params={
            'name': '初始设置规则',
            'next_game_master_name': '对话规则',
            'shared_memories': ["Alice 和 Bob 是邻居。"],
            'player_specific_context': {
                'Alice': "你不喜欢饼干。",
                'Bob': "你是一个饼干推销员。"
            },
        },
    ),
]
```

---

## 创建自定义 Prefab

```python
import dataclasses
from concordia.typing import prefab as prefab_lib
from concordia.agents import entity_agent_with_logging
from concordia.components import agent as agent_components

@dataclasses.dataclass
class MyCustomAgent(prefab_lib.Prefab):
    description: str = "我的模拟的自定义代理"
    
    def build(self, model, memory_bank):
        name = self.params.get("name", "Agent")
        goal = self.params.get("goal", "")
        
        # 创建组件
        memory = agent_components.memory.AssociativeMemory(memory_bank=memory_bank)
        instructions = agent_components.instructions.Instructions(agent_name=name)
        observation = agent_components.observation.LastNObservations(history_length=50)
        
        components = {
            agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY: memory,
            "Instructions": instructions,
            agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY: observation,
        }
        
        act_component = agent_components.concat_act_component.ConcatActComponent(
            model=model,
            component_order=list(components.keys()),
        )
        
        return entity_agent_with_logging.EntityAgentWithLogging(
            agent_name=name,
            act_component=act_component,
            context_components=components,
        )

# 注册自定义 prefab
prefabs["my_custom__Entity"] = MyCustomAgent()
```

---

## 高级代理架构

对于更复杂的行为，您可以将组件链接在一起，其中一个组件的输出成为另一个组件的输入/上下文。这允许代理在行动前"思考"。

### 推理的关键组件

*   **`SituationRepresentation`**：基于最近观察和相关记忆总结当前情况。
*   **`QuestionOfRecentMemories`**：根据记忆向模型提出特定问题。对于"指导原则"或"内心独白"很有用。

### 示例："反思型"代理
该代理首先构建情况表示，然后问自己如何利用它，*然后*决定行动。

```python
from concordia.contrib.components.agent import situation_representation_via_narrative
from concordia.components import agent as agent_components

@dataclasses.dataclass
class ReflectiveAgent(prefab_lib.Prefab):
    def build(self, model, memory_bank):
        name = self.params.get("name", "Agent")
        
        # 1. 基础组件
        instructions = agent_components.instructions.Instructions(agent_name=name)
        observation = agent_components.observation.LastNObservations(history_length=100)
        memory = agent_components.memory.AssociativeMemory(memory_bank=memory_bank)
        
        # 2. 高级组件（思维链）
        
        # 步骤A：总结情况
        situation = situation_representation_via_narrative.SituationRepresentation(
            model=model,
            observation_component_key=agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY,
            declare_entity_as_protagonist=True,
        )
        
        # 步骤B：应用指导原则（使用步骤A的上下文）
        principle = agent_components.question_of_recent_memories.QuestionOfRecentMemories(
            model=model,
            pre_act_label=f"{name}的内心独白",
            question=f"{name}如何在这种情况下最好地实现其目标？",
            answer_prefix=f"{name}想：",
            add_to_memory=False, # 不要用每个想法污染记忆
            components=[
                "Instructions",
                "situation_representation" # <--- 依赖于步骤A
            ],
        )

        # 3. 组装组件（顺序很重要！）
        components = {
            "Instructions": instructions,
            agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY: memory,
            agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY: observation,
            "situation_representation": situation,
            "guiding_principle": principle,
        }
        
        # 动作组件可以看到'components'中的所有内容
        act_component = agent_components.concat_act_component.ConcatActComponent(
            model=model,
            component_order=list(components.keys()),
        )
        
        return entity_agent_with_logging.EntityAgentWithLogging(
            agent_name=name,
            act_component=act_component,
            context_components=components,
        )
```

---

## 初始化代理记忆

推荐的生成代理背景故事和共享上下文的方法是使用 `formative_memories_initializer__GameMaster`。这个 prefab 在模拟开始时运行一次，向代理注入记忆。

```python
# 定义共享事实（世界构建）
shared_memories = [
    "河湾镇是一个田园诗般的乡村小镇。",
    "年份是2024年。",
]

# 定义玩家特定上下文（背景故事）
player_specific_context = {
    "Alice": "Alice 是一个喜欢实验的面包师。她很乐观。",
    "Bob": "Bob 是一个调查当地腐败的怀疑主义记者。",
}

# 将初始化器添加到您的实例列表中
initializer = prefab_lib.InstanceConfig(
    prefab='formative_memories_initializer__GameMaster',
    role=prefab_lib.Role.INITIALIZER,
    params={
        'name': '初始设置规则',
        # 关键：初始化后移交控制权的地方
        'next_game_master_name': '对话规则',
        'shared_memories': shared_memories,
        'player_specific_context': player_specific_context,
    },
)

# 假设'instances'在别处定义，您想将其添加到其中。
# 对于此示例，我们只显示配置。
# instances.append(initializer)
```

### 预加载记忆
```python
from concordia.associative_memory import basic_associative_memory

# 创建记忆库
memory_bank = basic_associative_memory.AssociativeMemoryBank(
    sentence_embedder=embedder
)

# 添加记忆
memory_bank.add("Alice 喜欢在山里徒步旅行。")
memory_bank.add("Alice 是一名软件工程师。")

# 传递给实例配置
instance = prefab_lib.InstanceConfig(
    prefab="basic__Entity",
    role=prefab_lib.Role.ENTITY,
    params={
        "name": "Alice",
        "memory_state": {"buffer": [], "memory_bank": memory_bank.get_state()},
    },
)
```

### 在阶段之间转移记忆
```python
import copy

# 第一阶段后，保存记忆状态
source_entity = phase1_sim.entities[0]
temp_memory = copy.deepcopy(
    source_entity.get_component("__memory__").get_state()
)

# 在第二阶段，应用到相应实体
target_entity = phase2_sim.entities[0]
target_entity.get_component("__memory__").set_state(temp_memory)
```

---

## 触发代理动作

```python
from concordia.typing import entity as entity_lib

# 自由形式的动作提示
action_spec = entity_lib.free_action_spec(
    call_to_action="Alice 接下来做什么？"
)
response = agent.act(action_spec=action_spec)

# 代理观察到某事
agent.observe("Bob 挥手打招呼。")
```

---

## 并行模拟（2个对话并行示例）

```python
from concordia.utils import concurrency
import functools

def run_dyad_task(player_states, model, embedder):
    sim = create_dialog_simulation(player_states, model, embedder)
    return sim.play()

# 创建并行任务
tasks = {
    "alice_bob": functools.partial(run_dyad_task,
        player_states={"Alice": alice_state, "Bob": bob_state},
        model=model, embedder=embedder),
    "carol_dave": functools.partial(run_dyad_task,
        player_states={"Carol": carol_state, "Dave": dave_state},
        model=model, embedder=embedder),
}

# 并行运行所有双人组
results = concurrency.run_tasks(tasks)
```

---

## 多阶段工作流模式

```python
# 第一阶段：市场
marketplace_sim = simulation.Simulation(
    config=marketplace_config, model=model, embedder=embedder
)
marketplace_sim.play()

# 转移到第二阶段
entities_for_phase2 = []
for entity in marketplace_sim.entities:
    entities_for_phase2.append(entity)

# 第二阶段：对话（使用转移的记忆）
daily_dyads = generate_dyads(entities_for_phase2)

for p1, p2 in daily_dyads:
    dyad_sim = create_dialog_simulation(p1, p2, model, embedder)
    # 转移记忆
    for src in [p1, p2]:
        tgt = next(e for e in dyad_sim.entities if e.name == src.name)
        mem = copy.deepcopy(src.get_component("__memory__").get_state())
        tgt.get_component("__memory__").set_state(mem)

    dyad_sim.play() # 参见上面的示例，了解如何并行运行此循环
```

---

## 关键导入参考

```python
# 核心模拟
from concordia.prefabs.simulation import generic as simulation
from concordia.typing import prefab as prefab_lib
from concordia.typing import entity as entity_lib

# Prefab 库
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs import game_master as game_master_prefabs
from concordia.utils import helper_functions

# 代理组件
from concordia.components import agent as agent_components
from concordia.agents import entity_agent_with_logging

# 记忆
from concordia.associative_memory import basic_associative_memory

# 并发
from concordia.utils import concurrency

# 引擎
from concordia.environment.engines import sequential, simultaneous

# 场景管理
from concordia.typing import scene as scene_lib
```

---

## 创建自定义游戏管理员组件

游戏管理员组件控制模拟流程。关键方法是 `pre_act`，它根据不同 `action_spec.output_type` 值被调用来处理不同阶段。游戏管理员组件可以控制一种或多种游戏管理员的动作规范类型，这在游戏管理员 prefab 中指定

```python
components_of_game_master = {
        _get_class_name(instructions): instructions,
        actor_components.memory.DEFAULT_MEMORY_COMPONENT_KEY: (
            actor_components.memory.AssociativeMemory(memory_bank=memory_bank)
        ),
        # 使用自定义游戏管理员组件进行观察
        gm_components.make_observation.DEFAULT_MAKE_OBSERVATION_COMPONENT_KEY: (
            my_gamemaster_component
        ),
        next_actor_key: next_actor,
        # 使用自定义游戏管理员组件作为下一个动作规范
        gm_components.next_acting.DEFAULT_NEXT_ACTION_SPEC_COMPONENT_KEY: (
            my_gamemaster_component
        ),
        # 使用自定义游戏管理员组件解析动作
        gm_components.switch_act.DEFAULT_RESOLUTION_COMPONENT_KEY: (
            my_gamemaster_component
        ),
    }
```

### 基本GM组件结构

```python
import dataclasses
from concordia.typing import entity as entity_lib
from concordia.typing import entity_component

class MyGameMasterComponent(
    entity_component.ContextComponent,
    entity_component.ComponentWithLogging,
):
    def __init__(
        self,
        acting_player_names: list[str],
        components: list[str] = (),
        pre_act_label: str = "\n我的组件",
    ):
        super().__init__()
        self._acting_player_names = acting_player_names
        self._components = components
        self._pre_act_label = pre_act_label
        self._state = {"round": 0}
    
    def get_pre_act_label(self) -> str:
        return self._pre_act_label
    
    def get_pre_act_value(self) -> str:
        return f"当前回合：{self._state['round']}"
    
    def pre_act(self, action_spec: entity_lib.ActionSpec) -> str:
        """处理来自模拟引擎的不同输出类型。"""
        output_type = action_spec.output_type
        
        if output_type == entity_lib.OutputType.MAKE_OBSERVATION:
            return self._handle_make_observation(action_spec)
        elif output_type == entity_lib.OutputType.NEXT_ACTION_SPEC:
            return self._handle_next_action_spec(action_spec)
        elif output_type == entity_lib.OutputType.NEXT_ACTING:
            return self._handle_next_acting()
        elif output_type == entity_lib.OutputType.RESOLVE:
            return self._resolve(action_spec)
        elif output_type == entity_lib.OutputType.NEXT_GAME_MASTER:
            return self._handle_next_gm()
        else:
            return ""
```

### `pre_act` 输出类型

| 输出类型 | 目的 | 返回内容 |
|------------|---------|----------------|
| `MAKE_OBSERVATION` | 生成代理看到的内容 | 代理的观察文本 |
| `NEXT_ACTION_SPEC` | 定义代理的动作格式 | 动作规范字符串（JSON格式等） |
| `NEXT_ACTING` | 确定下一个行动者 | 代理名称字符串 |
| `RESOLVE` | 解析代理动作 | 事件结果文本 |
| `NEXT_GAME_MASTER` | 移交给另一个GM | 下一个GM的名称 |

### 示例：观察处理器（市场风格）

```python
def _handle_make_observation(self, action_spec: entity_lib.ActionSpec) -> str:
    """为当前代理生成观察。"""
    # 从 action_spec 中提取代理名称
    agent_name = None
    for name in self._acting_player_names:
        if name in action_spec.call_to_action:
            agent_name = name
            break
    
    agent = self._agents[agent_name]
    
    # 构建带有代理当前状态的观察字符串
    obs = (
        f"回合：{self._state['round']+1} 开始\n"
        f"现金：{agent.cash:.2f}\n"
        f"{agent_name}的库存：{agent.inventory}\n"
        "提交你的动作。"
    )
    return obs
```

### 示例：动作规范处理器

```python
def _handle_next_action_spec(self, agent_name: str) -> str:
    """定义代理的动作格式。"""
    call_to_action = """
    {name}会做什么？
    以JSON格式输出你的决定：
    {{"action":"buy","item":"ITEM_ID","qty":INTEGER}}
    """
    action_spec = entity_lib.free_action_spec(call_to_action=call_to_action)
    return engine_lib.action_spec_to_string(action_spec)
```

### 示例：初始化器游戏管理员

用于一次性初始化并移交给另一个GM：

```python
class MyInitializer(entity_component.ContextComponent):
    def __init__(self, model, next_game_master_name: str, player_names: list[str]):
        super().__init__()
        self._model = model
        self._next_game_master_name = next_game_master_name
        self._players = player_names
        self._initialized = False
    
    def pre_act(self, action_spec: entity_lib.ActionSpec) -> str:
        # 只响应 NEXT_GAME_MASTER 查询
        if action_spec.output_type != entity_lib.OutputType.NEXT_GAME_MASTER:
            return ""
        
        if self._initialized:
            # 移交给对话/主GM
            return self._next_game_master_name
        
        # 运行初始化逻辑（生成场景，注入观察）
        self._run_initialization()
        self._initialized = True
        
        # 返回自己的名称让其他组件完成此步骤
        return self.get_entity().name
    
    def _run_initialization(self):
        """生成初始场景并注入观察队列。"""
        make_obs = self.get_entity().get_component("__make_observation__")
        
        scene = self._generate_scene_with_llm()
        for player in self._players:
            make_obs.add_to_queue(player, f"[场景] {scene}")
```

### 示例：动作解析

```python
import json
import re

def _resolve(self, action_spec: entity_lib.ActionSpec) -> str:
    """解析代理动作并解析结果。"""
    # 从组件获取假定事件
    component_states = "\n".join(
        [self._component_pre_act_display(key) for key in self._components]
    )
    
    events = []
    for agent_name in self._acting_player_names:
        # 在事件字符串中查找JSON动作
        pattern = re.compile(rf"\b{re.escape(agent_name)}\b.*?(?P<JSON>\{{.*?\}})", re.DOTALL)
        match = pattern.search(component_states)
        
        if match:
            try:
                action = json.loads(match.group("JSON"))
                outcome = self._process_action(agent_name, action)
                events.append(outcome)
            except json.JSONDecodeError:
                events.append(f"{agent_name}的动作解析失败。")
    
    self._state["round"] += 1
    return "\n".join(events)
```

### 状态管理（检查点所需）

```python
def get_state(self) -> entity_component.ComponentState:
    """返回用于检查点的可序列化状态。"""
    return {
        "round": self._state["round"],
        "initialized": self._initialized,
        "agents": {name: dataclasses.asdict(a) for name, a in self._agents.items()},
    }

def set_state(self, state: entity_component.ComponentState) -> None:
    """从检查点恢复状态。"""
    self._state["round"] = state.get("round", 0)
    self._initialized = state.get("initialized", False)
```

---

## 问卷调查

本节介绍运行问卷调查模拟：定义问题、配置代理和采访者，以及运行模拟。

## 步骤1：定义您的问卷

### 使用预定义问卷
Concordia 包含一个示例标准问卷，即抑郁焦虑压力量表(DASS)。

```python
from concordia.contrib.data.questionnaires import depression_anxiety_stress_scale

questionnaire = depression_anxiety_stress_scale.DASSQuestionnaire()
```

### 创建自定义问卷
继承 `QuestionnaireBase` 以创建自定义民意调查。使用 `statement`、`choices` 和可选的 `dimension` 来定义问题以进行聚合。

```python
from typing import Any, Dict, List
from concordia.contrib.data.questionnaires import base_questionnaire
import numpy as np
import pandas as pd

AGREEMENT_SCALE = ["非常不同意", "不同意", "同意", "非常同意"]

class CommunityWellbeingQuestionnaire(base_questionnaire.QuestionnaireBase):
  """测量社区连接感和安全感的4个问题调查。"""

  def __init__(self):
    super().__init__(
        name="社区福祉",
        description="测量社区连接感和安全感。",
        questionnaire_type="多项选择",
        observation_preprompt="{player_name}正在完成一项调查。",
        questions=[
            base_questionnaire.Question(
                statement="我觉得与社区有联系。",
                choices=AGREEMENT_SCALE,
                dimension="community",
            ),
            base_questionnaire.Question(
                statement="我的邻居很支持我。",
                choices=AGREEMENT_SCALE,
                dimension="community",
            ),
            base_questionnaire.Question(
                statement="我在社区里感到安全。",
                choices=AGREEMENT_SCALE,
                dimension="safety",
            ),
            base_questionnaire.Question(
                statement="我相信周围的人。",
                choices=AGREEMENT_SCALE,
                dimension="safety",
            ),
        ],
        dimensions=["community", "safety"],
    )

  def aggregate_results(
      self, player_answers: Dict[str, Dict[str, Any]]
  ) -> Dict[str, Any]:
    """计算每个维度的平均分。"""
    dimension_values: Dict[str, List[float]] = {}
    for question_data in player_answers.values():
      dim = question_data["dimension"]
      val = question_data["value"]
      if val is not None:
        dimension_values.setdefault(dim, []).append(val)
    return {dim: np.mean(vals) for dim, vals in dimension_values.items()}

  def get_dimension_ranges(self) -> Dict[str, tuple[float, float]]:
    """范围0-3对应4点量表（索引0, 1, 2, 3）。"""
    return {"community": (0, 3), "safety": (0, 3)}

  def plot_results(self, results_df: pd.DataFrame, **kwargs) -> None:
    pass
```

---

## 步骤2：配置实体和采访者

### 创建实体（代理）实例

```python
persona_names = ['Alice', 'Bob', 'Charlie']

persona_instances = []
for name in persona_names:
  persona_instances.append(prefab_lib.InstanceConfig(
      prefab='basic__Entity',
      role=prefab_lib.Role.ENTITY,
      params={'name': name},
  ))
```

### 配置采访者游戏管理员
对**多项选择**问卷使用 `interviewer__GameMaster`。

```python
interviewer_config = prefab_lib.InstanceConfig(
    prefab='interviewer__GameMaster',
    role=prefab_lib.Role.GAME_MASTER,
    params={
        'name': '采访者',
        'player_names': persona_names,
        'questionnaires': [questionnaire],  # 您的问卷对象
    },
)
```

对**开放式**问卷使用 `open_ended_interviewer__GameMaster`（需要嵌入器）。

```python
oe_interviewer_config = prefab_lib.InstanceConfig(
    prefab='open_ended_interviewer__GameMaster',
    role=prefab_lib.Role.GAME_MASTER,
    params={
        'name': '采访者',
        'player_names': persona_names,
        'questionnaires': [open_ended_questionnaire],
        'embedder': embedder,  # 开放式问题必需
    },
)
```

---

## 步骤3：运行模拟

### 构建配置
将 prefabs 和 instances 组合成单个 `Config` 对象。

```python
config = prefab_lib.Config(
    default_premise='',
    prefabs=prefabs,
    instances=persona_instances + [interviewer_config],  # 或 oe_interviewer_config
)
```

### 实例化并运行

```python
from concordia.prefabs.simulation import questionnaire_simulation

simulation = questionnaire_simulation.QuestionnaireSimulation(
    config=config,
    model=model,
    embedder=embedder,
)

results_log = simulation.play()
```

---

### 执行模式
在并行（更快）或顺序（上下文相关）执行之间选择。

| 模式 | 引擎 | 最佳用途 |
|------|--------|----------|
| **并行**（默认） | `ParallelQuestionnaireEngine` | 速度，独立答案 |
| **顺序** | `SequentialQuestionnaireEngine` | 依赖先前上下文的答案 |

```python
from concordia.environment.engines import parallel_questionnaire

simulation = questionnaire_simulation.QuestionnaireSimulation(
    config=config,
    model=model,
    embedder=embedder,
    engine=parallel_questionnaire.ParallelQuestionnaireEngine(max_workers=4),
)
```

### 代理选项：随机化选择
为了避免位置偏差，在代理 prefabs 中启用 `randomize_choices`（默认：`True`）。

```python
prefab_lib.InstanceConfig(
    prefab='basic__Entity',
    role=prefab_lib.Role.ENTITY,
    params={
        'name': 'Alice',
        'randomize_choices': False,  # 禁用以进行确定性测试或保持顺序
    },
)
```

---

---

## 常见模式

| 模式 | 实现 |
|---------|----------------|
| 加载所有 prefabs | `helper_functions.get_package_classes(entity_prefabs)` |
| 添加自定义 prefab | `prefabs["myname__Entity"] = MyPrefab()` |
| 获取代理记忆 | `entity.get_component("__memory__").get_state()` |
| 设置代理记忆 | `entity.get_component("__memory__").set_state(state)` |
| 深度复制以转移 | `copy.deepcopy(memory_state)` |
| 运行并行任务 | `concurrency.run_tasks(tasks_dict)` |
| 自由动作提示 | `entity_lib.free_action_spec(call_to_action=...)` |
| 访问其他GM组件 | `self.get_entity().get_component("__make_observation__")` |
| 添加观察到队列 | `make_obs.add_to_queue(player_name, observation_str)` |