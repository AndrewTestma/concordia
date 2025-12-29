"""
Werewolf 3.0 Agent Implementation.
狼人杀 Agent 实现，组装各个组件。
"""

from typing import List, Dict, Any
import datetime

from concordia.agents import entity_agent_with_logging
from concordia.components.agent import memory as memory_component
from concordia.components.agent import observation as observation_component
from concordia.associative_memory import basic_associative_memory
from concordia.typing import entity_component, entity
from concordia.language_model import language_model
from concordia.utils import measurements

try:
    from .components import (
        RoleIdentityComponent,
        PrivateMemoryComponent,
        DeceptiveThoughtComponent,
        NightActionComponent,
        CognitionCardComponent
    )
except ImportError:
    from components import (
        RoleIdentityComponent,
        PrivateMemoryComponent,
        DeceptiveThoughtComponent,
        NightActionComponent,
        CognitionCardComponent
    )

class WerewolfActComponent(entity_component.ActingComponent):
    """
    Action component that uses CognitionCardComponent to generate speech.
    使用 CognitionCardComponent 生成发言的行动组件。
    """
    def __init__(self,
                 model: language_model.LanguageModel,
                 cognition_component: CognitionCardComponent):
        self._model = model
        self._cognition_component = cognition_component

    def get_action_attempt(
        self,
        contexts: entity_component.ComponentContextMapping,
        action_spec: entity.ActionSpec,
    ) -> str:
        # Combine contexts
        context_str = "\n".join([f"{k}: {v}" for k, v in contexts.items() if v])

        # 1. Update Cognition Card (Think & Refresh)
        self._cognition_component.perform_think_update_cycle(context_str)

        # 2. Generate Speech (Act)
        return self._cognition_component.generate_speech(context_str)

    def get_state(self) -> entity_component.ComponentState:
        return {}

    def set_state(self, state: entity_component.ComponentState) -> None:
        pass

class WerewolfAgent(entity_agent_with_logging.EntityAgentWithLogging):
    """
    Werewolf Agent tailored for the game.
    定制的狼人杀 Agent。
    """
    def __init__(
        self,
        name: str,
        model: language_model.LanguageModel,
        role: str,
        teammates: List[str] | None = None,
        goal: str = "赢得游戏。",
        clock_now: Any = None,
    ):
        # 1. Memory
        # Using AssociativeMemoryBank
        raw_memory = basic_associative_memory.AssociativeMemoryBank(
            sentence_embedder=lambda x: [0.0] * 768 # Mock embedder or use real one if available
        )
        self._memory_component = memory_component.AssociativeMemory(
            memory_bank=raw_memory
        )

        # 2. Custom Components
        self._role_component = RoleIdentityComponent(model, role, teammates, goal)
        self._private_memory = PrivateMemoryComponent(self._memory_component)

        # Cognition Card Component replaces DeceptiveThoughtComponent
        self._cognition_component = CognitionCardComponent(
            model, self._role_component, self._memory_component, name, clock_now
        )

        self._night_component = NightActionComponent(model, role)

        # 3. Observation Components
        # Component to save observations to memory
        observation_saver = observation_component.ObservationToMemory(
            memory_component_key="memory"
        )

        # Component to show recent observations in context
        recent_observations = observation_component.LastNObservations(
            history_length=10,
            memory_component_key="memory"
        )

        # 4. Act Component
        act_component = WerewolfActComponent(model, self._cognition_component)

        # 5. Assemble Context Components
        context_components = {
            "role": self._role_component,
            "memory": self._memory_component,
            "private_memory": self._private_memory, # Helper to show instructions
            "observation_saver": observation_saver,
            "recent_observations": recent_observations,
            "cognition_card": self._cognition_component, # Shows card state
            "night_action": self._night_component, # Shows nothing usually
        }

        super().__init__(
            agent_name=name,
            act_component=act_component,
            context_components=context_components,
        )

        self._role = role

    def get_role(self) -> str:
        return self._role

    def night_action(self, context: str, valid_targets: List[str]) -> Dict[str, Any]:
        """
        Directly call night action component.
        直接调用夜晚行动组件。
        """
        # 增强上下文：尝试从记忆中检索重要信息
        # 特别是对于预言家，需要检索查验结果
        # 简单起见，我们检索最近的几条记忆，以及包含 "查验"、"狼人"、"身份" 关键词的记忆

        # 检索最近记忆 (简化为直接取最近的观察，如果 Memory 组件支持)
        # 这里我们假设 MemoryBank 存了所有东西。
        # 我们构建一个查询
        queries = ["查验结果", "身份是", "狼人是", "我是预言家"]
        retrieved_memories = []

        # 使用 memory_component 的 retrieve (如果支持) 或者直接访问 memory_bank (如果是 BasicAssociativeMemory)
        # 这里的 self._memory_component 是 AssociativeMemory 包装器。
        # 它没有直接暴露 retrieve 方法给外部，但我们可以通过 protected member 或者 extend 接口。
        # 或者，我们可以利用 observation_component.LastNObservations 来获取上下文。
        # 但 LastNObservations 已经在 context 中了 (作为 act 时的 context，但 night_action 是单独调用的)。

        # 让我们手动检索一下
        if hasattr(self._memory_component, '_memory_bank'):
             # Hacky access to memory bank
             bank = self._memory_component._memory_bank
             for q in queries:
                 mems = bank.retrieve_associative(q, k=3)
                 retrieved_memories.extend(mems)

        # 去重
        unique_memories = list(set(retrieved_memories))
        memory_context = "\n".join([f"- {m}" for m in unique_memories])

        full_context = f"{context}\n\n[相关记忆]:\n{memory_context}\n"

        return self._night_component.generate_night_action(full_context, valid_targets)
