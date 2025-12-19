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

def _parse_event_summary(summary: str):
    import re
    if '---' not in summary:
        return None, None
    event_part = summary.split('---', 1)[1].strip()
    if event_part.startswith('Event:'):
        event_part = event_part[len('Event:'):].strip()
    m = re.match(r'^(.*?)\s*--\s*"(.*)"', event_part)
    if not m:
        return None, None
    return m.group(1).strip(), m.group(2).strip()

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
        embedder = lambda texts: np.ones((len(texts), 3))
    return embedder

# 3. 创建辩论场景配置
def create_debate_config():
    """创建辩论模拟的配置。"""

    # 加载可用的预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(game_master_prefabs),
    }
    # 注册自定义辩论代理
    prefabs["debate_advocate__Entity"] = DebateAdvocate()

    # 定义辩论者实例
    instances = [
        # 正方辩手（使用自定义代理，明确立场与风格）
        prefab_lib.InstanceConfig(
            prefab="debate_advocate__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "Qwen支持者",
                "position": "pro",
                "debate_topic": "可再生能源优于核能来应对气候变化",
                "goal": "用数据和事实支持可再生能源优先",
                "traits": "强势、逻辑严密、直击对方弱点"
            },
        ),
        # 反方辩手（使用自定义代理，明确立场与风格）
        prefab_lib.InstanceConfig(
            prefab="debate_advocate__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "DeepSeek质疑者",
                "position": "con",
                "debate_topic": "核能优于可再生能源来应对气候变化",
                "goal": "强调稳定、低碳与可扩展性",
                "traits": "果断、批判性强、善于指出逻辑漏洞"
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
                "acting_order": "fixed",
                "can_terminate_simulation": False,
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
        # 流式输出：通过状态回调在每步结束时打印当轮事件
        def _stream_callback(state: dict):
            raw_log = state.get("raw_log", [])
            if not raw_log:
                return
            entry = raw_log[-1]
            summary = entry.get("Summary", "")
            speaker, content = _parse_event_summary(summary)
            if speaker and content:
                print(f"[流式] {speaker}：{content}")
            elif summary:
                print(f"[流式] {summary}")

        results = sim.play(
            return_html_log=False,
            get_state_callback=_stream_callback,
            checkpoint_path=None,
        )

        print("\n=== 辩论结果 ===")
        print("辩论成功完成！")
        print(f"总步数: {len(results) if isinstance(results, list) else '未知'}")

        # 打印一些关键结果
        if isinstance(results, list) and results:
            print("\n=== 辩论日志（前5步摘要） ===")
            for i, entry in enumerate(results[:5]):
                summary = entry.get('Summary', f'Step {i+1}')
                print(summary)
            print("\n=== 友好输出（前5轮） ===")
            for i, entry in enumerate(results[:5]):
                summary = entry.get('Summary', '')
                speaker, content = _parse_event_summary(summary)
                if speaker and content:
                    print(f"第 {i+1} 轮: {speaker}：{content}")
                else:
                    print(f"第 {i+1} 轮: {summary}")

        return results

    except Exception as e:
        print(f"辩论过程中出现错误: {e}")
        # 返回模拟结果即使出错
        return None

# 5. 分析辩论结果
def analyze_debate_results(results):
    """分析辩论的结果。"""
    if results is None or not isinstance(results, list):
        print("没有结果可供分析。")
        return

    print("\n=== 辩论分析 ===")

    # 统计每个参与者的发言次数
    participant_turns = {}
    for entry in results:
        summary = entry.get('Summary', '')
        speaker, content = _parse_event_summary(summary)
        if speaker:
            participant_turns[speaker] = participant_turns.get(speaker, 0) + 1

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
        position = self.params.get("position", "pro")
        debate_topic = self.params.get("debate_topic", "")

        # 创建组件
        memory = agent_components.memory.AssociativeMemory(memory_bank=memory_bank)
        instructions_text = (
            f"您正在参加一场正式辩论。"
            f"立场：{position}；主题：{debate_topic}。"
            f"必须采用针锋相对的辩论风格："
            f"1) 直接针对对方上一轮的关键论点进行反驳，指出漏洞、矛盾或证据不足；"
            f"2) 给出清晰的主张（Claim）、证据（Evidence）与推理（Warrant），避免空泛表态；"
            f"3) 使用数据或权威来源（若无真实数据可概念性引用）来支撑论点；"
            f"4) 适当使用反问与比较来削弱对方论证；"
            f"5) 保持专业，但避免过度礼貌与妥协性措辞。"
            f"输出格式严格为：{name} -- \"您的论点内容\""
        )
        instructions = agent_components.constant.Constant(
            state=instructions_text,
            pre_act_label=agent_components.instructions.DEFAULT_INSTRUCTIONS_PRE_ACT_LABEL,
        )
        observation = agent_components.observation.LastNObservations(history_length=100)
        similar_memories = agent_components.all_similar_memories.AllSimilarMemories(
            model=model,
            memory_component_key=agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY,
            num_memories_to_retrieve=10,
        )

        components = {
            agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY: memory,
            "Instructions": instructions,
            agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY: observation,
            "SimilarMemories": similar_memories,
        }

        act_component = agent_components.concat_act_component.ConcatActComponent(
            model=model,
            component_order=[
                agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY,
                agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY,
                "SimilarMemories",
                "Instructions",
            ],
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
    prefabs["debate_advocate__Entity"] = DebateAdvocate()

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
