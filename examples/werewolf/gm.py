"""
狼人杀示例的游戏管理员组装。

此模块使用 `generic` 预制件构建一个游戏管理员。GM 配置有：
- 从提供的实体代理派生的玩家名称
- 核心 GM 组件 (make_observation, next_acting, next_action_spec,
  event_resolution, 等)
- 具有确定性嵌入器的 GM 记忆库
- 可选的指令行以保持经典主持风格

支持使用不同的语言模型来控制GM的行为。
"""

from __future__ import annotations

from typing import Sequence

from concordia.prefabs.game_master.generic import GameMaster as GameMasterPrefab
from concordia.language_model.no_language_model import NoLanguageModel
from concordia.language_model.language_model import LanguageModel

from .config import GM_LINES
from .memory import make_deterministic_embedder, create_memory_bank, seed_public_terms
from .config import TERMS_CHEATSHEET


def build_gm(model: LanguageModel, player_agents: Sequence) -> object:
    """
    构建并返回单个游戏管理员实体 (EntityAgentWithLogging)。

    预制件需要：
    - `model`: `LanguageModel` 实现（我们使用 `NoLanguageModel`）
    - `memory_bank`: 配置了嵌入器的 `AssociativeMemoryBank`
    - `entities`: 提取玩家名称的玩家代理列表
    """
    embedder = make_deterministic_embedder(dim=64)
    gm_bank = create_memory_bank(embedder=embedder)

    # 将简洁的术语速查表注入 GM 记忆中，以鼓励在生成观察和解析时保持风格一致性。
    seed_public_terms(gm_bank, TERMS_CHEATSHEET)

    # 组装 GM 预制件。我们保留行动顺序的默认值（GM 选择），
    # 但设置一个清晰的名称以反映规则集。
    gm_prefab = GameMasterPrefab(params={"name": "Werewolf GM"}, entities=tuple(player_agents))

    # 构建实际的 GM 实体并添加日志。
    gm_entity = gm_prefab.build(model=model, memory_bank=gm_bank)

    # 用固定指令行作为初始观察来初始化 GM，以便下游组件可以通过记忆/观察上下文检索它们。
    for line in GM_LINES:
        gm_entity.observe(line)

    return gm_entity
