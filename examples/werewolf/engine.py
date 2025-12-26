"""
狼人杀示例的引擎配置。

此模块创建顺序（回合制）引擎并公开一个辅助函数，
用于使用提供的 GM 和玩家代理运行简短的模拟循环。

该引擎控制游戏的流程，包括夜晚阶段（狼人行动、预言家验人）和白天阶段（发言、投票）。
"""

from __future__ import annotations

from typing import Sequence

from concordia.environment.engines.sequential import Sequential


def build_engine() -> Sequential:
    """
    创建并返回顺序回合制引擎。
    
    顺序引擎按顺序执行游戏中的每个参与者（包括GM和玩家）的行动，
    确保游戏按照狼人杀的规则有序进行。
    """
    return Sequential()


def run_loop(engine: Sequential, gm_entity, player_agents: Sequence, premise: str = "", max_steps: int = 10) -> None:
    """
    使用提供的 GM 和玩家代理运行引擎循环。

    Args:
        engine: 顺序引擎实例
        gm_entity: 游戏管理员实体
        player_agents: 玩家代理序列
        premise: 游戏前提条件，为GM提供初始上下文
        max_steps: 最大执行步数，限制游戏长度
    
    该函数启动游戏循环，引擎将协调GM和玩家之间的交互，
    执行狼人杀的各个阶段（夜晚行动、白天讨论、投票等）。
    - `premise` 为 GM 播种初始事件上下文
    - `max_steps` 限制此演示运行的回合数
    - `verbose=True` 启用详细输出，便于观察游戏过程
    """
    engine.run_loop(
        game_masters=[gm_entity],
        entities=player_agents,
        premise=premise,
        max_steps=max_steps,
        verbose=True,
    )

