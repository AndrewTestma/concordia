import requests
import json
import logging
from typing import Dict, Any, Optional, List
import os

# 导入相关模块用于类型提示
if hasattr(__builtins__, 'TYPE_CHECKING') and __builtins__.TYPE_CHECKING:
    from PlayerState import PlayerState
    from TheEye import TheEye
    from LogicEngine import LogicEngine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DifyClient:
    """
    DifyClient (Dify API 客户端)

    职责:
    - 封装与 Dify 平台的 HTTP 通信。
    - 组装用于 Dify 工作流的上下文载荷 (Context Payload)。
    - 处理 Dify 的响应并返回结构化数据。

    该类实现了“认知闭环”中的“大脑”连接部分。
    """

    def __init__(self, api_key: str, base_url: str = "http://117.50.34.101/v1"):
        """
        初始化 Dify 客户端。

        :param api_key: Dify 应用的 API 密钥 (Workflow App Key)。
        :param base_url: Dify API 的基础 URL。默认为 http://117.50.34.101/v1。
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')  # 移除末尾的斜杠

        # 设置请求头
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.info(f"DifyClient 已初始化，Base URL: {self.base_url}")

    def run_workflow(self, inputs: Dict[str, Any], user_id: str, player_name: str = None, step_name: str = None) -> Dict[str, Any]:
        """
        运行 Dify 工作流。

        :param inputs: 传递给工作流的变量字典。对应 Dify 中的 'Start' 节点输入。
        :param user_id: 唯一用户标识符 (用于 Dify 会话隔离)。通常使用 Player ID。
        :param player_name: 玩家姓名，用于输出显示
        :param step_name: 当前步骤名称，用于输出显示
        :return: 工作流执行结果 (JSON 字典)。
        """
        url = f"{self.base_url}/workflows/run"

        payload = {
            "inputs": inputs,
            "response_mode": "blocking",  # 使用阻塞模式等待结果
            "user": user_id
        }

        try:
            # 显示当前步骤和说话者
            player_display = f"{player_name} ({user_id})" if player_name else user_id
            step_display = step_name if step_name else "未知步骤"
            logger.info(f"【DIFY调用】玩家 {player_display} 正在执行 {step_display}...")

            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()  # 检查 HTTP 错误

            result = response.json()

            # 解析 output 字段
            # Dify workflow 的输出通常在 data.outputs 中
            data = result.get('data', {})
            outputs = data.get('outputs', {})

            # 如果状态是 finished，则返回 outputs
            if data.get('status') == 'succeeded':
                logger.info(f"【DIFY完成】玩家 {player_display} 的 {step_display} 执行成功。")
                logger.info(f"【DIFY输出】{player_display} 输出: {json.dumps(outputs, ensure_ascii=False, indent=2)[:500]}...")
                return outputs
            else:
                logger.error(f"【DIFY失败】玩家 {player_display} 的 {step_display} 未成功完成: {result}")
                return {"error": "Workflow failed", "details": result}

        except requests.exceptions.RequestException as e:
            logger.error(f"【DIFY错误】玩家 {player_display} 的 {step_display} API 请求失败: {e}")
            return {"error": "Request failed", "message": str(e)}
        except json.JSONDecodeError:
            logger.error(f"【DIFY错误】玩家 {player_display} 的 {step_display} 无法解析响应 JSON。")
            return {"error": "Invalid JSON response"}

    def assemble_payload(self,
                         game_meta: Dict[str, Any],
                         player_state: 'PlayerState',
                         the_eye: 'TheEye',
                         logic_engine: 'LogicEngine') -> Dict[str, Any]:
        """
        构建发送给 Dify 的完整上下文载荷 (Context Payload)。

        这是连接 Concordia (Body), Neo4j (Logic) 和 Dify (Brain) 的关键桥梁。

        :param game_meta: 游戏元数据 (round, phase, step_name 等)。
        :param player_state: 当前玩家的状态对象 (包含怀疑矩阵、私有记忆)。
        :param the_eye: 视角过滤器实例，用于获取客观事实。
        :param logic_engine: 逻辑引擎实例，用于生成逻辑提示。
        :return: 符合 Dify 输入要求的字典。
        """
        player_id = player_state.player_id
        role = player_state.role

        # 1. 获取视角下的客观事实 (Perception - Objective Facts)
        # 调用 TheEye 获取该玩家可见的图谱子图
        visible_events = the_eye.get_player_view(player_id, role)

        # 使用 LogicEngine 将事件转换为自然语言描述
        # 这里我们直接复用 LogicEngine 的 _process_event 逻辑，或者调用 generate_logic_hints
        # 注意：generate_logic_hints 返回的是 hints 列表
        objective_facts_text = logic_engine.generate_logic_hints(visible_events)

        # 2. 生成逻辑提示 (Perception - Logic Hints)
        # 目前 logic_hints 和 objective_facts 在 LogicEngine 中是合并处理的，
        # 如果有更高级的推理 (如矛盾检测)，可以在这里添加。
        # 暂时将 LogicEngine 的输出视为 objective_facts，逻辑提示可以设为空或额外的分析
        logic_hints_text = [] # 预留给更高级的推理

        # 3. 组装 Subjective State (主观状态)
        subjective_state = {
            "suspicion_matrix": player_state.suspicion_matrix,
            "pending_questions": list(player_state.pending_questions),
            "current_objective": player_state.objective
        }

        # 4. 组装 Player Info (玩家静态信息)
        player_info = {
            "id": player_id,
            "role": role,
            "name": player_state.player_name,
            "status": "ALIVE" # 暂时硬编码，实际应从 Neo4j 或 GM 获取
        }

        # 如果 player_state 中有 model 信息，则添加
        if hasattr(player_state, 'model'):
            player_info['model'] = player_state.model

        # 5. 构建最终 JSON 结构
        # 注意：这里的结构必须与 Dify 工作流中定义的变量名匹配
        # 假设 Dify 接收一个名为 `context_payload` 的大 JSON 字符串，或者分散的变量
        # 根据技术文档，我们组装一个大的 JSON 对象

        full_payload = {
            "meta_info": game_meta,
            "player_info": player_info,
            "perception": {
                "objective_facts": objective_facts_text,
                "logic_hints": logic_hints_text
            },
            "subjective_state": subjective_state
        }

        logger.debug(f"Payload assembled for {player_id}: {json.dumps(full_payload, ensure_ascii=False)}")

        return full_payload

# 使用示例 (仅供测试)
if __name__ == "__main__":
    # 模拟依赖
    class MockPlayerState:
        def __init__(self):
            self.player_id = "P1"
            self.player_name = "TestPlayer"
            self.role = "Villager"
            self.suspicion_matrix = {"P2": 60}
            self.pending_questions = ["P2 is wolf?"]

    class MockTheEye:
        def get_player_view(self, pid, role):
            return [{"source_name": "P2", "action": "VOTE", "target_name": "P3", "properties": {"round": 1}}]

    class MockLogicEngine:
        def generate_logic_hints(self, events):
            return ["P2 voted for P3 in round 1."]

    # 初始化
    client = DifyClient(api_key="TEST_KEY")

    # 组装
    payload = client.assemble_payload(
        game_meta={"round": 1, "phase": "DAY"},
        player_state=MockPlayerState(),
        the_eye=MockTheEye(),
        logic_engine=MockLogicEngine()
    )

    print(json.dumps(payload, indent=2, ensure_ascii=False))
