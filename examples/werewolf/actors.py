"""
狼人杀示例的参与者组装。

此模块使用 `fake_assistant_with_configurable_system_prompt` 预制件构建六个玩家实体。
每个实体都提供：
- 显示名称 (P1..P6)
- 角色特定的系统提示
- 用确定性嵌入器和角色信息播种的私有记忆库
对于狼人玩家，队友名称也会注入到私有记忆中。

支持为每个玩家分配不同的语言模型，以实现多样化的游戏行为。
"""

from __future__ import annotations

from typing import Sequence, List

from concordia.prefabs.entity.fake_assistant_with_configurable_system_prompt import (
    Entity as AssistantEntityPrefab,
)
from concordia.language_model.no_language_model import NoLanguageModel
from concordia.language_model.language_model import LanguageModel

from .config import PLAYER_NAMES, PLAYER_ROLES, ROLE_PROMPTS
from .memory import (
    make_deterministic_embedder,
    create_memory_bank,
    seed_role_intro,
    seed_wolf_teammates,
)


def build_actors(model: LanguageModel) -> Sequence:
    """
    使用单一模型构建并返回六个玩家实体 (EntityAgentWithLogging 实例)。

    预制件需要：
    - `model`: `LanguageModel` 实现（我们使用 `NoLanguageModel` 进行最小化、无依赖的运行）
    - `memory_bank`: 配置了嵌入器的 `AssociativeMemoryBank`
    """
    embedder = make_deterministic_embedder(dim=64)

    # 首先计算狼人玩家名称列表以播种队友知识。
    wolf_names = [
        PLAYER_NAMES[i]
        for i, role in enumerate(PLAYER_ROLES)
        if role == "狼"
    ]

    agents = []
    for idx, (name, role) in enumerate(zip(PLAYER_NAMES, PLAYER_ROLES), start=1):
        # 使用名称和系统提示准备实体预制件。
        system_prompt = ROLE_PROMPTS[role]
        prefab = AssistantEntityPrefab(
            params={"name": name, "system_prompt": system_prompt}
        )

        # 为玩家创建私有记忆库并播种初始内容。
        bank = create_memory_bank(embedder=embedder)
        seed_role_intro(bank, role=role, player_name=name)

        # 如果玩家是狼人，在记忆中播种队友名称。
        if role == "狼":
            other_wolves = [w for w in wolf_names if w != name]
            seed_wolf_teammates(bank, player_name=name, wolf_names=other_wolves)

        # 构建实际的实体代理并添加日志。
        agent = prefab.build(model=model, memory_bank=bank)
        agents.append(agent)

    return agents


def build_actors_with_different_models(models: List[LanguageModel]) -> Sequence:
    """
    使用不同的语言模型为每个玩家构建实体 (EntityAgentWithLogging 实例)。

    Args:
        models: 为每个玩家分配的语言模型列表，长度应为6

    Returns:
        构建的玩家实体序列

    预制件需要：
    - `model`: `LanguageModel` 实现（每个玩家可以使用不同的模型）
    - `memory_bank`: 配置了嵌入器的 `AssociativeMemoryBank`
    """
    if len(models) != len(PLAYER_NAMES):
        raise ValueError(f"模型数量 ({len(models)}) 必须等于玩家数量 ({len(PLAYER_NAMES)})")

    embedder = make_deterministic_embedder(dim=64)

    # 首先计算狼人玩家名称列表以播种队友知识。
    wolf_names = [
        PLAYER_NAMES[i]
        for i, role in enumerate(PLAYER_ROLES)
        if role == "狼"
    ]

    agents = []
    for idx, ((name, role), model) in enumerate(zip(zip(PLAYER_NAMES, PLAYER_ROLES), models), start=1):
        # 使用名称和系统提示准备实体预制件。
        system_prompt = ROLE_PROMPTS[role]
        prefab = AssistantEntityPrefab(
            params={"name": name, "system_prompt": system_prompt}
        )

        # 为玩家创建私有记忆库并播种初始内容。
        bank = create_memory_bank(embedder=embedder)
        seed_role_intro(bank, role=role, player_name=name)

        # 如果玩家是狼人，在记忆中播种队友名称。
        if role == "狼":
            other_wolves = [w for w in wolf_names if w != name]
            seed_wolf_teammates(bank, player_name=name, wolf_names=other_wolves)

        # 使用特定模型构建实际的实体代理并添加日志。
        agent = prefab.build(model=model, memory_bank=bank)
        agents.append(agent)

    return agents
