"""
使用Concordia框架实现两个AI模型中文辩论的示例。
"""

import os
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs import game_master as game_master_prefabs
from concordia.prefabs.simulation import generic as simulation
from concordia.typing import prefab as prefab_lib
from concordia.utils import helper_functions
from concordia.contrib import language_models as language_model_utils
import numpy as np
import sentence_transformers
from concordia.environment.engines import sequential

# 1. 设置语言模型
# 使用不同的模型进行辩论
def setup_models():
    """为辩论设置两个不同的语言模型。"""
    # 获取API密钥
    dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY')
    deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')

    # 如果没有设置API密钥，则使用模拟模型进行演示
    if not dashscope_api_key or not deepseek_api_key:
        print("警告：未找到API密钥。使用模拟模型进行演示。")
        from concordia.language_model import no_language_model
        qwen_model = no_language_model.NoLanguageModel()
        deepseek_model = no_language_model.NoLanguageModel()
    else:
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

# 2. 设置嵌入器
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
        embedder = np.ones(3)
    return embedder

# 3. 创建辩论场景配置
def create_debate_config():
    """创建辩论模拟的配置。"""

    # 加载可用的预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(game_master_prefabs),
    }

    # 定义辩论者实例
    instances = [
        # Qwen模型作为正方辩手
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "Qwen支持者",
                "goal": "论证可再生能源是应对气候变化的主要解决方案",
                "traits": "分析性强、数据驱动、环保意识强"
            },
        ),
        # DeepSeek模型作为反方辩手
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "DeepSeek质疑者",
                "goal": "论证核能比可再生能源更能有效解决气候变化问题",
                "traits": "务实、技术导向、注重成本"
            },
        ),
    ]

    # 添加游戏主持人
    instances.append(
        prefab_lib.InstanceConfig(
            prefab="dialogic__GameMaster",
            role=prefab_lib.Role.GAME_MASTER,
            params={
                "name": "辩论主持人",
                "next_game_master_name": "辩论主持人",
                "turn_taking": "u-go-i-go",  # 轮流发言
            },
        )
    )

    # 创建配置
    config = prefab_lib.Config(
        default_premise="两个AI模型正在就'应对气候变化更好的解决方案是可再生能源还是核能？'这一话题进行正式辩论。辩论将包括开场陈述、反驳和结语。每个参与者需要按照{name} -- \"内容\"的格式进行发言。",
        default_max_steps=12,  # 限制最大步数以控制辩论长度
        prefabs=prefabs,
        instances=instances,
    )

    return config

# 4. 运行辩论
def run_debate():
    """运行两个模型之间的辩论模拟。"""

    print("正在设置模型和嵌入器...")
    qwen_model, deepseek_model = setup_models()
    embedder = setup_embedder()

    print("正在创建辩论配置...")
    config = create_debate_config()

    # 由于我们需要两个不同的模型，我们需要创建两个独立的模拟
    # 这是一个简化版本，实际实现可能需要更复杂的设置

    print("正在初始化模拟...")
    try:
        # 创建自定义引擎以提供更明确的辩论流程提示
        custom_engine = sequential.Sequential(
            call_to_next_acting="请在参与者中选择下一位发言者的姓名。",
            call_to_next_action_spec=(
                "根据以上上下文，请生成{name} -- \"...\" 的中文发言内容，"
                "要求符合当前阶段：开场陈述→反驳→结语，且必须使用该格式。"
            ),
            call_to_resolve="请将上一位发言者的句子作为事件写入日志。",
            call_to_check_termination="辩论是否已完成？",
            call_to_next_game_master="请选择下一位主持人。",
        )
        # 创建模拟（使用第一个模型作为主要模型）
        sim = simulation.Simulation(
            config=config,
            model=qwen_model,  # 主要模型
            embedder=embedder,
            engine=custom_engine,
        )

        print("开始辩论...")
        results = sim.play()

        print("\n=== 辩论结果 ===")
        print("辩论成功完成！")
        print(f"总步数: {len(results.steps)}")

        # 打印一些关键结果
        if hasattr(results, 'logs'):
            print("\n=== 辩论日志 ===")
            for i, step in enumerate(results.steps[:5]):  # 只打印前5步
                print(f"步骤 {i+1}: {step}")

        return results

    except Exception as e:
        print(f"辩论过程中出现错误: {e}")
        # 返回模拟结果即使出错
        return None

# 5. 分析辩论结果
def analyze_debate_results(results):
    """分析辩论的结果。"""
    if results is None:
        print("没有结果可供分析。")
        return

    print("\n=== 辩论分析 ===")

    # 统计每个参与者的发言次数
    participant_turns = {}
    if hasattr(results, 'steps'):
        for step in results.steps:
            # 这里需要根据实际结果格式进行调整
            pass

    print("辩论分析完成。")

# 6. 主函数
def main():
    """运行辩论示例的主函数。"""
    print("AI模型中文辩论示例")
    print("=" * 30)

    # 运行辩论
    results = run_debate()

    # 分析结果
    analyze_debate_results(results)

    print("\n辩论示例完成！")

# 高级用法：自定义辩论代理
class DebateAdvocate(prefab_lib.Prefab):
    """具有特定推理模式的辩论倡导者的自定义预制件。"""
    description = "一个用于正式辩论的自定义代理，可以根据指定的立场和主题进行辩论。"

    def __init__(self, position="pro", debate_topic="", **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.debate_topic = debate_topic

    def build(self, model, memory_bank):
        """构建自定义辩论代理。"""
        from concordia.agents import entity_agent_with_logging
        from concordia.components import agent as agent_components

        name = self.params.get("name", "Debater")

        # 创建组件
        memory = agent_components.memory.AssociativeMemory(memory_bank=memory_bank)
        instructions = agent_components.instructions.Instructions(
            agent_name=name,
            instructions=(
                f"您正在参加一场正式辩论。"
                f"您的立场：{self.position}。"
                f"主题：{self.debate_topic}。"
                f"请具有说服力、逻辑性和尊重性。"
                f"用事实和例子支持您的论点。"
                f"请严格按照以下格式回复：{name} -- \"您的论点内容\""
                f"请注意倾听对方的观点并进行有针对性的反驳。"
                f"保持专业和礼貌的态度。"
            )
        )
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

# 使用自定义代理的辩论配置
def create_advanced_debate_config():
    """使用自定义代理创建高级辩论配置。"""

    # 注册自定义预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(game_master_prefabs),
    }
    prefabs["debate_advocate__Entity"] = DebateAdvocate

    # 定义高级辩论者实例
    instances = [
        # 正方辩手（使用自定义代理）
        prefab_lib.InstanceConfig(
            prefab="debate_advocate__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "可再生能源支持者",
                "position": "pro",
                "debate_topic": "可再生能源在应对气候变化方面优于核能"
            },
        ),
        # 反方辩手（使用自定义代理）
        prefab_lib.InstanceConfig(
            prefab="debate_advocate__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "核能支持者",
                "position": "con",
                "debate_topic": "核能在应对气候变化方面优于可再生能源"
            },
        ),
    ]

    # 添加游戏主持人
    instances.append(
        prefab_lib.InstanceConfig(
            prefab="dialogic__GameMaster",
            role=prefab_lib.Role.GAME_MASTER,
            params={
                "name": "辩论主持人",
                "next_game_master_name": "辩论主持人",
            },
        )
    )

    # 创建配置
    config = prefab_lib.Config(
        default_premise="两位专家辩手正在正式辩论比赛中陈述他们的论点。主题是：'应对气候变化更好的解决方案是可再生能源还是核能？'每方将进行开场陈述、反驳并以结语结束。每个参与者需要按照{name} -- \"内容\"的格式进行发言。",
        default_max_steps=15,
        prefabs=prefabs,
        instances=instances,
    )

    return config

if __name__ == "__main__":
    main()
