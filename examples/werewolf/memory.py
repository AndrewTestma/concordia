"""
狼人杀示例的记忆辅助工具。

Concordia 的 `AssociativeMemoryBank` 需要在调用 `add` 或 `retrieve` 方法之前设置句子嵌入器。
此模块提供：
- 基于种子哈希的简单确定性嵌入器，返回固定宽度的 numpy 向量
- 为玩家和游戏管理员创建记忆库的工厂辅助函数
- 将角色和风格种子注入记忆的便捷初始化器

在狼人杀游戏中，记忆系统对于跟踪游戏状态、玩家身份和历史事件至关重要。
每个玩家和GM都有自己的记忆库，用于存储相关信息。
"""

from __future__ import annotations

import hashlib
import numpy as np

from concordia.associative_memory.basic_associative_memory import (
    AssociativeMemoryBank,
)


def make_deterministic_embedder(dim: int = 64):
    """
    创建一个简单的确定性句子嵌入器。

    此嵌入器通过以下方式将输入字符串映射到固定长度的 numpy 向量：
    - 使用 SHA256 对字符串进行哈希
    - 使用哈希摘要为 RNG 设置种子
    - 从正态分布生成向量并进行 L2 归一化

    注意：这在语义上没有意义。对于需要稳定嵌入来满足记忆库 API 的示例来说，
    这足以在不依赖外部嵌入服务的情况下工作。

    Args:
        dim: 嵌入向量的维度，默认为64

    Returns:
        一个嵌入函数，将文本字符串转换为numpy数组
    """
    def embed(text: str) -> np.ndarray:
        # 计算输入文本的稳定哈希
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # 使用前 8 字节作为种子以确保可重现性
        seed = int.from_bytes(h[:8], byteorder="big", signed=False)
        rng = np.random.default_rng(seed)
        vec = rng.normal(0.0, 1.0, size=(dim,))
        # L2 归一化以避免规模漂移
        norm = np.linalg.norm(vec) or 1.0
        return (vec / norm).astype(np.float32)

    return embed


def create_memory_bank(embedder) -> AssociativeMemoryBank:
    """
    创建一个 `AssociativeMemoryBank` 并设置提供的嵌入器。

    记忆库用于存储和检索游戏中的事件、对话和状态信息。
    每个玩家和GM都有自己的记忆库，用于跟踪游戏进程。

    Args:
        embedder: 用于将文本转换为向量的嵌入器

    Returns:
        配置了嵌入器的关联记忆库实例
    """
    bank = AssociativeMemoryBank()
    bank.set_embedder(embedder)
    return bank


def seed_public_terms(bank: AssociativeMemoryBank, terms_text: str) -> None:
    """
    用狼人杀术语速查表为提供的银行播种。

    这有助于GM和玩家在交流时使用一致的术语。

    Args:
        bank: 要播种的记忆库
        terms_text: 包含狼人杀术语的文本
    """
    bank.add(terms_text)


def seed_role_intro(bank: AssociativeMemoryBank, role: str, player_name: str) -> None:
    """
    为玩家的银行播种一个简短的角色介绍行，以便轻松检索。

    这帮助玩家记住自己的角色和身份。

    Args:
        bank: 玩家的记忆库
        role: 玩家的角色（如狼人、预言家等）
        player_name: 玩家的名称
    """
    bank.add(f"角色：{role}；玩家：{player_name}")


def seed_wolf_teammates(
    bank: AssociativeMemoryBank,
    player_name: str,
    wolf_names: list[str],
) -> None:
    """
    为狼人玩家的银行播种队友名称。

    这使狼人玩家能够知道他们的队友是谁，以便协作。

    Args:
        bank: 狼人玩家的记忆库
        player_name: 当前狼人玩家的名称
        wolf_names: 所有狼人玩家的名称列表（不包括当前玩家）
    """
    teammates_str = ", ".join(wolf_names)
    bank.add(f"{player_name}的队友（狼人）：{teammates_str}")
