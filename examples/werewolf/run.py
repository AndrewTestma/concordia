"""
狼人杀示例的入口点。

此脚本组装：
- 用于离线执行的多种语言模型
- 具有角色特定提示和私有记忆库的六个玩家代理
- 使用通用 GM 预制件和记忆库的一个游戏管理员
- 顺序回合制引擎

然后它运行一个带有详细输出的短循环，以便您可以逐步检查
观察、下一步行动决策和事件解析。
"""

from __future__ import annotations

from concordia.language_model.no_language_model import NoLanguageModel
from concordia.contrib.language_models.openai.gpt_model import GptLanguageModel
from concordia.contrib.language_models.qwen.qwen_model import QwenLanguageModel
from concordia.contrib.language_models.deepseek.deepseek_model import DeepSeekLanguageModel
import os

from .actors import build_actors, build_actors_with_different_models
from .gm import build_gm
from .engine import build_engine, run_loop


def run_game_with_model(model, premise: str = "开局：天黑请闭眼。", max_steps: int = 6) -> None:
    """
    使用指定模型组装 GM + 玩家 + 引擎并运行简短模拟。

    Args:
        model: 用于游戏的语言模型
        premise: 游戏起始前提
        max_steps: 最大游戏步数
    """
    # 使用角色提示和私有记忆库构建玩家代理。
    players = build_actors(model=model)

    # 构建游戏管理员，传递玩家以便 GM 可以列出他们的名称。
    gm = build_gm(model=model, player_agents=players)

    # 创建顺序引擎并运行循环。
    engine = build_engine()
    run_loop(engine=engine, gm_entity=gm, player_agents=players, premise=premise, max_steps=max_steps)


def run_game(premise: str = "开局：天黑请闭眼。", max_steps: int = 6) -> None:
    """
    使用 NoLanguageModel 组装 GM + 玩家 + 引擎并运行简短模拟。
    """
    # 使用最简单的模型以避免外部依赖和 API 密钥。
    model = NoLanguageModel()

    # 使用角色提示和私有记忆库构建玩家代理。
    players = build_actors(model=model)

    # 构建游戏管理员，传递玩家以便 GM 可以列出他们的名称。
    gm = build_gm(model=model, player_agents=players)

    # 创建顺序引擎并运行循环。
    engine = build_engine()
    run_loop(engine=engine, gm_entity=gm, player_agents=players, premise=premise, max_steps=max_steps)


def run_game_with_six_different_player_models(premise: str = "开局：天黑请闭眼。", max_steps: int = 6) -> None:
    """
    为6个玩家使用6种不同的模型运行游戏。

    这个函数演示了如何为每个玩家分配不同的语言模型，以实现多样化的游戏行为。
    每个玩家可能会表现出不同的策略和个性。

    Args:
        premise: 游戏起始前提
        max_steps: 最大游戏步数
    """
    # 获取API密钥
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    dashscope_api_key = os.environ.get("DASHSCOPE_API_KEY")
    deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not openrouter_api_key:
        print("警告: OPENROUTER_API_KEY 环境变量未设置，将使用NoLanguageModel进行演示。")
        # 如果没有API密钥，则使用NoLanguageModel进行演示
        player_models = [
            NoLanguageModel(),  # 玩家1的模型 (Claude)
            NoLanguageModel(),  # 玩家2的模型 (GPT)
            NoLanguageModel(),  # 玩家3的模型 (Grok)
            NoLanguageModel(),  # 玩家4的模型 (Gemini)
            NoLanguageModel(),  # 玩家5的模型 (Qwen)
            NoLanguageModel(),  # 玩家6的模型 (DeepSeek)
        ]
    else:
        # 定义6种不同的模型，通过OpenRouter使用Claude、GPT、Grok、Gemini
        # Qwen和DeepSeek使用各自的API
        player_models = [
            GptLanguageModel(
                model_name="anthropic/claude-3.5-sonnet",
                api_key=openrouter_api_key,
                api_base="https://openrouter.ai/api/v1",
                name="智多星"  # Claude
            ),
            GptLanguageModel(
                model_name="openai/gpt-4o",
                api_key=openrouter_api_key,
                api_base="https://openrouter.ai/api/v1",
                name="逻辑王"  # GPT
            ),
            GptLanguageModel(
                model_name="xai/grok-2-1212",
                api_key=openrouter_api_key,
                api_base="https://openrouter.ai/api/v1",
                name="爆料者"  # Grok
            ),
            GptLanguageModel(
                model_name="google/gemini-pro",
                api_key=openrouter_api_key,
                api_base="https://openrouter.ai/api/v1",
                name="全能手"  # Gemini
            ),
            QwenLanguageModel(
                model_name="qwen-plus",
                api_key=dashscope_api_key,
                name="灵犀者"  # Qwen
            ),
            DeepSeekLanguageModel(
                model_name="deepseek-chat",
                api_key=deepseek_api_key,
                name="洞察者"  # DeepSeek
            ),
        ]

    print("=== 为6个玩家使用6种不同模型运行游戏 ===")

    # 使用不同的模型构建玩家代理
    players = build_actors_with_different_models(player_models)

    # 为游戏管理员使用一个模型（这里使用第一个模型，也可以使用专门的GM模型）
    gm_model = player_models[0]
    gm = build_gm(model=gm_model, player_agents=players)

    # 创建顺序引擎并运行循环。
    engine = build_engine()
    run_loop(engine=engine, gm_entity=gm, player_agents=players, premise=premise, max_steps=max_steps)


def run_game_with_six_models(premise: str = "开局：天黑请闭眼。", max_steps: int = 6) -> None:
    """
    使用6种不同的模型运行游戏（每个游戏使用一个模型）。

    这个函数演示了如何使用不同的语言模型来运行狼人杀游戏。
    每个模型可能会产生不同的游戏行为和策略。

    Args:
        premise: 游戏起始前提
        max_steps: 最大游戏步数
    """
    # 定义6种不同的模型（这里使用NoLanguageModel作为示例，实际应用中可以使用不同的模型）
    # 在实际应用中，您可以替换为不同的语言模型实现
    models = [
        NoLanguageModel(),  # 模型1：无语言模型（用于测试）
        NoLanguageModel(),  # 模型2：无语言模型（用于测试）
        NoLanguageModel(),  # 模型3：无语言模型（用于测试）
        NoLanguageModel(),  # 模型4：无语言模型（用于测试）
        NoLanguageModel(),  # 模型5：无语言模型（用于测试）
        NoLanguageModel(),  # 模型6：无语言模型（用于测试）
    ]

    # 为每个模型运行游戏
    for i, model in enumerate(models, 1):
        print(f"\n=== 运行第 {i} 个模型 ===")
        run_game_with_model(model, premise, max_steps)


if __name__ == "__main__":
    # 运行使用6种不同模型的游戏（每个玩家使用不同模型）
    run_game_with_six_different_player_models()
