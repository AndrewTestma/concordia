import logging
from typing import Dict, List, Any, Optional
from collections import deque

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlayerState:
    """
    PlayerState (玩家状态管理)

    职责:
    - 管理玩家的内存状态，特别是那些不需要或不适合存储在 Neo4j 图数据库中的主观信息。
    - 维护怀疑矩阵 (Suspicion Matrix)，记录对其他玩家的怀疑程度。
    - 维护待办问题队列 (Pending Questions)，记录需要思考或询问的问题。

    设计原则:
    - 状态分离: 主观怀疑和短期记忆保留在 Python 内存中，不直接写入共享的图数据库。
    """

    def __init__(self, player_id: str, player_name: str, role: str):
        """
        初始化玩家状态。

        :param player_id: 玩家 ID
        :param player_name: 玩家名称
        :param role: 玩家角色 (例如: 'Villager', 'Werewolf', 'Seer')
        """
        self.player_id = player_id
        self.player_name = player_name
        self.role = role

        # 怀疑矩阵: 记录对其他玩家的怀疑度。
        # 格式: {target_player_id: score}
        # score 范围通常建议为 0.0 (完全信任) 到 1.0 (确信是狼人)，或者是 -100 到 100 的整数。
        # 这里默认使用 0-100 的整数，初始值为 50 (中立)。
        self.suspicion_matrix: Dict[str, float] = {}

        # 待办问题队列: 记录玩家想要探究的问题。
        # 使用 deque 实现先进先出 (FIFO) 或用作栈。
        self.pending_questions: deque = deque()

        # 当前战术目标 (由夜间策略生成)
        self.objective: str = ""

        logger.info(f"玩家状态已初始化: {self.player_name} ({self.role})")

    def init_suspicion(self, player_ids: List[str]):
        """
        初始化怀疑矩阵。将所有其他玩家的怀疑度设置为默认值 (50)。

        :param player_ids: 游戏中所有玩家的 ID 列表。
        """
        for pid in player_ids:
            if pid != self.player_id:
                self.suspicion_matrix[pid] = 50.0
        logger.info(f"[{self.player_name}] 怀疑矩阵已初始化，包含 {len(self.suspicion_matrix)} 名其他玩家。")

    def update_suspicion(self, target_id: str, delta: float, reason: str = ""):
        """
        更新对某位玩家的怀疑度。

        :param target_id: 目标玩家 ID。
        :param delta: 变化量 (正数增加怀疑，负数减少怀疑)。
        :param reason: 更新原因 (用于日志记录)。
        """
        if target_id not in self.suspicion_matrix:
            logger.warning(f"[{self.player_name}] 尝试更新未知玩家 {target_id} 的怀疑度。")
            return

        old_score = self.suspicion_matrix[target_id]
        new_score = old_score + delta

        # 限制范围在 0 到 100 之间
        new_score = max(0.0, min(100.0, new_score))

        self.suspicion_matrix[target_id] = new_score

        logger.info(f"[{self.player_name}] 更新对 {target_id} 的怀疑: {old_score} -> {new_score} (变化: {delta:+}). 原因: {reason}")

    def get_suspicion(self, target_id: str) -> float:
        """
        获取对某位玩家的怀疑度。

        :param target_id: 目标玩家 ID。
        :return: 怀疑度分数 (0-100)。如果不存在则返回 50。
        """
        return self.suspicion_matrix.get(target_id, 50.0)

    def get_most_suspicious(self, count: int = 1) -> List[tuple]:
        """
        获取最怀疑的几位玩家。

        :param count: 返回的数量。
        :return: (player_id, score) 的列表，按怀疑度降序排列。
        """
        sorted_suspicion = sorted(self.suspicion_matrix.items(), key=lambda item: item[1], reverse=True)
        return sorted_suspicion[:count]

    def add_question(self, question: str, priority: int = 1):
        """
        添加一个待办问题。

        :param question: 问题内容。
        :param priority: 优先级 (目前简单实现，暂不用于排序，仅预留)。
        """
        self.pending_questions.append(question)
        logger.info(f"[{self.player_name}] 添加问题: \"{question}\"")

    def pop_question(self) -> Optional[str]:
        """
        获取并移除下一个待办问题。

        :return: 问题字符串，如果队列为空则返回 None。
        """
        if self.pending_questions:
            q = self.pending_questions.popleft()
            logger.info(f"[{self.player_name}] 取出问题: \"{q}\"")
            return q
        return None

    def get_all_questions(self) -> List[str]:
        """
        获取所有待办问题 (不移除)。
        """
        return list(self.pending_questions)

    def __repr__(self):
        return f"<PlayerState: {self.player_name}, Suspicion Count: {len(self.suspicion_matrix)}, Questions: {len(self.pending_questions)}>"
