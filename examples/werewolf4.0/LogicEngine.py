import logging
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogicEngine:
    """
    Logic Engine (逻辑推理引擎)

    职责:
    - 将从 Neo4j 获取的图数据 (子图) 转换为自然语言提示或逻辑摘要。
    - 帮助 Agent 理解当前的局势，识别矛盾或关键信息。
    """

    def __init__(self):
        pass

    def generate_logic_hints(self, sub_graph: List[Dict[str, Any]]) -> List[str]:
        """
        根据可见的子图生成逻辑提示。

        :param sub_graph: 由 TheEye.get_player_view 返回的事件列表。
                          格式: [{'source_name': '...', 'action': '...', 'target_name': '...', 'properties': {...}}, ...]
        :return: 自然语言提示列表。
        """
        hints = []

        # 按回合分组事件 (可选优化)，目前先按时间顺序处理
        for event in sub_graph:
            hint = self._process_event(event)
            if hint:
                hints.append(hint)

        if not hints:
            hints.append("目前没有观察到任何重要事件。")

        return hints

    def _process_event(self, event: Dict[str, Any]) -> str:
        """
        处理单个事件并转换为文本。
        """
        source = event.get('source_name', 'Unknown')
        target = event.get('target_name', 'Unknown')
        action = event.get('action', 'UNKNOWN_ACTION')
        props = event.get('properties', {})
        round_num = props.get('round', '?')

        # 根据动作类型生成描述
        if action == 'VOTE':
            return f"[第 {round_num} 轮] {source} 投票给了 {target}。"

        elif action == 'KILL':
            return f"[第 {round_num} 轮] {source} (狼人) 袭击了 {target}。"

        elif action == 'CHECK':
            result = props.get('result', 'Unknown')
            return f"[第 {round_num} 轮] 你查验了 {target}，结果是: {result}。"

        elif action == 'SPEAK':
            content = props.get('content', '...')
            # 如果是公开讲话，目标通常是 All 或某人，这里简化显示
            return f"[第 {round_num} 轮] {source} 发言: \"{content}\""

        else:
            return f"[未知事件] {source} 对 {target} 执行了 {action}。"

    def analyze_contradictions(self, sub_graph: List[Dict[str, Any]]) -> List[str]:
        """
        (高级功能) 分析潜在的逻辑矛盾。
        例如: 同一轮次中，某人既投票给了 A，又在发言中保 A (需要更复杂的语义分析)。
        目前作为预留接口。
        """
        return []
