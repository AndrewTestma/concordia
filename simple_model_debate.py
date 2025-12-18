"""
Simple example of two AI models having a debate conversation using Concordia.
"""

import os
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs import game_master as game_master_prefabs
from concordia.prefabs.simulation import generic as simulation
from concordia.typing import prefab as prefab_lib
from concordia.utils import helper_functions
from concordia.contrib import language_models as language_model_utils
import numpy as np

def create_simple_debate_simulation():
    """Create a simple debate simulation between two models."""

    # 1. 设置语言模型（这里使用模拟模型，实际使用时替换为真实模型）
    print("Setting up language models...")
    try:
        #如果有API密钥，可以取消注释下面的代码来使用真实的模型
        qwen_model = language_model_utils.language_model_setup(
            api_type='qwen',
            model_name='qwen-max',
            api_key=os.environ.get('DASHSCOPE_API_KEY'),
        )
        deepseek_model = language_model_utils.language_model_setup(
            api_type='deepseek',
            model_name='deepseek-chat',
            api_key=os.environ.get('DEEPSEEK_API_KEY'),
        )

        # 为了演示目的，我们使用模拟模型
        from concordia.language_model import no_language_model
        qwen_model = no_language_model.NoLanguageModel()
        deepseek_model = no_language_model.NoLanguageModel()
        print("Using mock models for demonstration.")

    except Exception as e:
        print(f"Could not setup real models: {e}")
        from concordia.language_model import no_language_model
        qwen_model = no_language_model.NoLanguageModel()
        deepseek_model = no_language_model.NoLanguageModel()

    # 2. 设置嵌入器（用于记忆检索）
    print("Setting up embedder...")
    try:
        import sentence_transformers
        st_model = sentence_transformers.SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2'
        )
        embedder = lambda x: st_model.encode(x, show_progress_bar=False)
    except Exception:
        print("Could not load sentence transformer. Using mock embedder.")
        embedder = lambda x: np.ones(3) if isinstance(x, str) else np.ones((len(x), 3))

    # 3. 创建代理配置
    print("Creating agent configurations...")

    # 加载预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(game_master_prefabs),
    }

    # 定义辩论参与者
    instances = [
        # 支持可再生能源的代理
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "RenewableEnergySupporter",
                "goal": "Argue that renewable energy is the best solution for climate change",
                "traits": "Environmentally conscious, optimistic about technology, believes in sustainability"
            },
        ),
        # 支持核能的代理
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "NuclearEnergySupporter",
                "goal": "Argue that nuclear energy is the most practical solution for climate change",
                "traits": "Pragmatic, focused on reliability and scalability, concerned about energy density"
            },
        ),
    ]

    # 添加对话主持人
    instances.append(
        prefab_lib.InstanceConfig(
            prefab="dialogic__GameMaster",
            role=prefab_lib.Role.GAME_MASTER,
            params={
                "name": "debate_moderator",
                "next_game_master_name": "debate_moderator",
                "turn_taking": "u-go-i-go",  # 轮流发言
            },
        )
    )

    # 4. 创建模拟配置
    config = prefab_lib.Config(
        default_premise="Two experts are having a structured debate about energy solutions for climate change. They will take turns presenting their arguments and responding to each other.",
        default_max_steps=8,  # 控制对话长度
        prefabs=prefabs,
        instances=instances,
    )

    # 5. 初始化并运行模拟
    print("Initializing simulation...")
    try:
        sim = simulation.Simulation(
            config=config,
            model=qwen_model,  # 使用第一个模型作为主模型
            embedder=embedder
        )

        print("Starting debate conversation...")
        results = sim.play()

        print("\n=== DEBATE CONVERSATION RESULTS ===")
        print("Debate completed successfully!")
        print(f"Total conversation steps: {len(results.steps) if hasattr(results, 'steps') else 'Unknown'}")

        # 显示一些结果
        if hasattr(results, 'logs') and results.logs:
            print("\n=== SAMPLE CONVERSATION ===")
            # 只显示前几个对话轮次
            for i, log_entry in enumerate(results.logs[:6]):
                print(f"Turn {i+1}: {log_entry}")
        else:
            print("No detailed logs available in results.")

        return results

    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_conversation_results(results):
    """Analyze the conversation results."""
    if results is None:
        print("No results to analyze.")
        return

    print("\n=== CONVERSATION ANALYSIS ===")

    # 基本统计
    total_steps = len(results.steps) if hasattr(results, 'steps') else 0
    print(f"Total conversation steps: {total_steps}")

    # 分析参与者的互动
    if hasattr(results, 'logs'):
        participant_mentions = {}
        for log_entry in results.logs:
            # 简单的提及计数
            if "RenewableEnergySupporter" in str(log_entry):
                participant_mentions["RenewableEnergySupporter"] = \
                    participant_mentions.get("RenewableEnergySupporter", 0) + 1
            if "NuclearEnergySupporter" in str(log_entry):
                participant_mentions["NuclearEnergySupporter"] = \
                    participant_mentions.get("NuclearEnergySupporter", 0) + 1

        print("Participant mentions:")
        for participant, count in participant_mentions.items():
            print(f"  {participant}: {count} mentions")

    print("Conversation analysis complete.")

def main():
    """Main function to run the conversation example."""
    print("AI Models Conversation Debate Example")
    print("=" * 40)

    # 运行对话辩论
    results = create_simple_debate_simulation()

    # 分析结果
    analyze_conversation_results(results)

    print("\nConversation example completed!")

# 额外示例：如何使用真实模型（如果API密钥可用）
def setup_real_models_example():
    """
    Example of how to set up real models if API keys are available.
    This is commented out for demonstration purposes.
    """
    """
    # 设置环境变量
    os.environ['DASHSCOPE_API_KEY'] = 'your_qwen_api_key_here'
    os.environ['DEEPSEEK_API_KEY'] = 'your_deepseek_api_key_here'

    # 安装必要的依赖
    # pip install gdm-concordia[qwen,deepseek] sentence-transformers

    # 初始化真实模型
    qwen_model = language_model_utils.language_model_setup(
        api_type='qwen',
        model_name='qwen-max',
        api_key=os.environ.get('DASHSCOPE_API_KEY'),
    )

    deepseek_model = language_model_utils.language_model_setup(
        api_type='deepseek',
        model_name='deepseek-chat',
        api_key=os.environ.get('DEEPSEEK_API_KEY'),
    )

    # 然后在模拟中使用这些模型
    # sim = simulation.Simulation(config=config, model=qwen_model, embedder=embedder)
    """

if __name__ == "__main__":
    main()
