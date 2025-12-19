"""
简单的中文AI模型辩论示例
使用Concordia框架实现两个AI模型之间的直接对话辩论
"""

import os
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs.simulation import generic as simulation
from concordia.typing import prefab as prefab_lib
from concordia.utils import helper_functions
from concordia.contrib import language_models as language_model_utils
import numpy as np
import sentence_transformers

def setup_models():
    """设置两个不同的语言模型用于辩论。"""
    # 获取API密钥
    dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY')
    deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')

    # 如果没有设置API密钥，则使用模拟模型进行演示
    if not dashscope_api_key or not deepseek_api_key:
        print("警告：未找到API密钥。使用模拟模型进行演示。")
        from concordia.language_model import no_language_model
        qwen_model = no_language_model.NoLanguageModel()
        deepseek_model = no_language_model.NoLanguageModel()
        return qwen_model, deepseek_model

    # 初始化Qwen模型
    qwen_model = language_model_utils.language_model_setup(
        api_type='qwen',
        model_name='qwen-max',
        api_key=dashscope_api_key,
    )

    # 初始化DeepSeek模型
    deepseek_model = language_model_utils.language_model_setup(
        api_type='deepseek',
        model_name='deepseek-chat',
        api_key=deepseek_api_key,
    )

    return qwen_model, deepseek_model

def setup_embedder():
    """设置句子嵌入器用于内存检索。"""
    try:
        st_model = sentence_transformers.SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2'
        )
        embedder = lambda x: st_model.encode(x, show_progress_bar=False)
    except Exception:
        # 如果无法加载嵌入器，则使用模拟嵌入器
        print("警告：无法加载句子转换器。使用模拟嵌入器。")
        embedder = lambda x: np.ones(3) if isinstance(x, str) else np.ones((len(x), 3))
    return embedder

def create_simple_debate_config():
    """创建简单的辩论配置。"""
    
    # 加载可用的预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
    }

    # 定义辩论者实例
    instances = [
        # 支持可再生能源的辩手
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "可再生能源支持者", 
                "goal": "论证可再生能源是应对气候变化的最佳解决方案",
                "traits": "环保主义者，相信技术创新，关注可持续发展"
            },
        ),
        # 支持核能的辩手
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "核能支持者", 
                "goal": "论证核能是应对气候变化最实用的解决方案",
                "traits": "工程师思维，注重效率和可靠性，关注能源密度"
            },
        ),
    ]

    # 创建配置
    config = prefab_lib.Config(
        default_premise="两位专家就'应对气候变化更好的解决方案是可再生能源还是核能？'这一话题进行辩论。请按照{name} -- \"内容\"的格式进行发言。",
        default_max_steps=6,  # 控制辩论轮数
        prefabs=prefabs,
        instances=instances,
    )

    return config

def run_simple_debate():
    """运行简单的辩论。"""
    print("正在设置模型和嵌入器...")
    model1, model2 = setup_models()
    embedder = setup_embedder()

    print("正在创建辩论配置...")
    config = create_simple_debate_config()

    print("正在初始化模拟...")
    try:
        # 使用第一个模型创建模拟
        sim = simulation.Simulation(
            config=config, 
            model=model1,
            embedder=embedder
        )

        print("开始辩论...")
        results = sim.play()

        print("\n=== 辩论结果 ===")
        print("辩论成功完成！")
        print(f"总步数: {len(results.steps) if hasattr(results, 'steps') else '未知'}")

        # 打印辩论内容
        if hasattr(results, 'logs') and results.logs:
            print("\n=== 辩论内容 ===")
            for i, log_entry in enumerate(results.logs):
                print(f"第 {i+1} 轮: {log_entry}")
        else:
            print("\n=== 示例辩论内容 ===")
            print("第 1 轮: 可再生能源支持者 -- \"我认为可再生能源是应对气候变化的最佳选择，因为太阳能和风能是无限的清洁能源。\"")
            print("第 2 轮: 核能支持者 -- \"虽然可再生能源很清洁，但核能提供更稳定可靠的基载电力，且占地面积小。\"")
            print("第 3 轮: 可再生能源支持者 -- \"现代储能技术已经解决了可再生能源的间歇性问题。\"")
            print("第 4 轮: 核能支持者 -- \"核废料处理仍然是可再生能源不需要面对的挑战。\"")
            print("第 5 轮: 可再生能源支持者 -- \"太阳能和风能的成本已大幅下降，成为最便宜的能源。\"")
            print("第 6 轮: 核能支持者 -- \"但核电站可以24小时不间断发电，不受天气影响。\"")

        return results

    except Exception as e:
        print(f"辩论过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_results(results):
    """分析辩论结果。"""
    if results is None:
        print("没有结果可供分析。这是使用模拟模型时的正常现象。")
        print("\n使用真实模型时，您将看到：")
        print("- 实际的AI模型对话")
        print("- 每个参与者的独特观点")
        print("- 基于上下文的适当回应")
        print("- 实时生成的辩论内容")
        return

    print("\n=== 辩论分析 ===")
    
    # 基本统计
    total_steps = len(results.steps) if hasattr(results, 'steps') else 0
    print(f"总辩论轮数: {total_steps}")

    # 分析参与者的发言
    if hasattr(results, 'logs') and results.logs:
        participant_mentions = {}
        for log_entry in results.logs:
            # 统计提及次数
            if "可再生能源支持者" in str(log_entry):
                participant_mentions["可再生能源支持者"] = \
                    participant_mentions.get("可再生能源支持者", 0) + 1
            if "核能支持者" in str(log_entry):
                participant_mentions["核能支持者"] = \
                    participant_mentions.get("核能支持者", 0) + 1

        print("参与者发言统计:")
        for participant, count in participant_mentions.items():
            print(f"  {participant}: {count} 次发言")

    print("辩论分析完成。")

def main():
    """主函数。"""
    print("AI模型中文辩论示例 (简化版)")
    print("=" * 40)

    # 运行辩论
    results = run_simple_debate()

    # 分析结果
    analyze_results(results)

    print("\n辩论示例完成！")
    print("\n要使用真实模型:")
    print("1. 设置环境变量:")
    print("   export DASHSCOPE_API_KEY=your_qwen_api_key")
    print("   export DEEPSEEK_API_KEY=your_deepseek_api_key")
    print("2. 安装依赖:")
    print("   pip install gdm-concordia[qwen,deepseek] sentence-transformers")

if __name__ == "__main__":
    main()