import logging
import json
from typing import Dict, Any, List, Optional
import numpy as np

# 尝试导入 Concordia 相关模块
try:
    from concordia.associative_memory import basic_associative_memory
    from concordia.typing import entity as entity_lib
except ImportError:
    # 简单的 Mock，防止在没有安装 Concordia 环境下完全无法运行
    class entity_lib:
        class Entity:
            pass
    class basic_associative_memory:
        class AssociativeMemoryBank:
            def __init__(self, sentence_embedder): pass
            def add(self, text): pass
            def retrieve_associative(self, query, k): return []

from src.dify_client import UniversalDifyClient
from src.loader import CharacterConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UniversalAgent")

class MockEmbedder:
    """如果无法加载 sentence_transformers，使用此 Mock"""
    def __call__(self, text: str):
        # 返回随机向量，仅用于跑通流程
        return np.random.rand(768)

def get_embedder():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return lambda x: model.encode(x, show_progress_bar=False)
    except Exception as e:
        logger.warning(f"无法加载 SentenceTransformer ({e})，使用 Mock Embedder。")
        return MockEmbedder()

class UniversalAgent(entity_lib.Entity):
    """
    通用剧本杀 Agent，连接 Concordia 仿真环境与 Dify 认知核心。
    """
    def __init__(self,
                 config: CharacterConfig,
                 dify_client: UniversalDifyClient,
                 embedder=None):
        self.config = config
        self.dify_client = dify_client
        self.name = config.name

        # 初始化记忆库
        self.embedder = embedder or get_embedder()
        self.memory_bank = basic_associative_memory.AssociativeMemoryBank(
            sentence_embedder=self.embedder
        )

        # 初始化短期记忆缓冲 (Observation Buffer)
        self.observation_buffer = []

        # 初始状态
        self.current_scene = "unknown"

    def observe(self, observation: str):
        """
        接收环境观察。
        Concordia 的 GM 会调用此方法通知 Agent 发生了什么。
        """
        if not observation:
            return

        logger.info(f"[{self.name}] 观察到: {observation[:50]}...")

        # 1. 存入短期缓冲
        self.observation_buffer.append(observation)

        # 2. 存入长期关联记忆
        self.memory_bank.add(observation)

    def act(self, action_spec=None) -> str:
        """
        执行行动。
        Concordia 的 GM 会调用此方法获取 Agent 的行动。
        """
        logger.info(f"[{self.name}] 正在思考...")

        # 1. 整理上下文 (Context Assembly)
        # 从短期缓冲中获取最近发生的事件
        recent_context = "\n".join(self.observation_buffer[-5:])

        # 2. 检索长期记忆 (Memory Retrieval)
        # 基于当前任务或最近的事件进行检索
        query = recent_context if recent_context else f"我是{self.name}，现在的状况是？"

        # 使用 retrieve_associative (k=3)
        retrieved_memories = self.memory_bank.retrieve_associative(query, k=3)
        memory_summary = "\n".join(retrieved_memories)

        # 3. 构造 Dify 输入
        # 这里的 task 通常由 GM 通过 observation 或 action_spec 传递
        # 简化起见，我们假设 action_spec 中包含了当前指令
        current_task = "请根据当前情况进行回应。"
        if action_spec and hasattr(action_spec, 'call_to_action'):
            current_task = action_spec.call_to_action

        role_profile = f"你是{self.config.name}。\n{self.config.profile}\n目标：{'; '.join(self.config.objectives)}"

        # 4. 调用 Dify
        response = self.dify_client.query_player(
            player_id=self.config.id,
            role_profile=role_profile,
            task=current_task,
            game_context=f"当前场景：{self.current_scene}\n近期发生：\n{recent_context}",
            memory_summary=memory_summary,
            knowledge_tag=self.config.private_knowledge_tag # 传递知识库标签
        )

        # 5. 解析Dify返回的内容
        try:
            # 处理可能的嵌套JSON响应
            if isinstance(response, str):
                # 如果返回的是JSON字符串，尝试解析并提取result字段
                if response.strip().startswith('{') and response.strip().endswith('}'):
                    parsed_response = json.loads(response.strip())
                    if 'result' in parsed_response:
                        response = parsed_response['result']
                    elif 'text' in parsed_response:
                        response = parsed_response['text']
                    else:
                        # 如果JSON中没有result或text字段，尝试提取第一个字符串值
                        for key, value in parsed_response.items():
                            if isinstance(value, str) and value.strip():
                                response = value.strip()
                                break
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"[{self.name}] 解析Dify响应失败: {e}，使用原始响应")

        # 6. 清理短期缓冲 (可选，视策略而定)
        # self.observation_buffer.clear()
        # 这里不清空，依靠滑动窗口或 GM 的 Context 管理

        logger.info(f"[{self.name}] 决定: {response[:50]}...")
        return response

    def set_scene(self, scene_name: str):
        self.current_scene = scene_name

if __name__ == "__main__":
    # 测试代码
    print("UniversalAgent module loaded.")
