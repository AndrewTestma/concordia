import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 可见性常量 (与 TheEye.py 保持一致)
VISIBILITY_PUBLIC = 'PUBLIC'
VISIBILITY_WEREWOLF = 'WEREWOLF_TEAM'
VISIBILITY_SEER = 'SEER_ONLY'
VISIBILITY_PRIVATE = 'PRIVATE'

class TheHand:
    """
    The Hand (事件解析器与写入器)

    职责:
    - 负责将游戏中的事件写入 Neo4j 图数据库。
    - 处理事件的可见性 (Visibility) 和时间戳 (Timestamp)。
    - 提供常用动作 (如投票、击杀、发言) 的辅助方法。
    """

    def __init__(self, adapter):
        """
        初始化 TheHand。

        :param adapter: Neo4jAdapter 实例，用于与数据库交互。
        """
        self.adapter = adapter

    def log_event(self, source_id: str, action: str, target_id: str, visibility: str, properties: Optional[Dict[str, Any]] = None):
        """
        记录一个通用事件到图谱中。

        该方法会在 source (Actor) 和 target (Target) 之间创建一条关系。
        关系类型由 `action` 参数决定 (自动转换为大写)。

        :param source_id: 动作发起者的 Player ID。
        :param action: 动作名称 (例如: "VOTE", "SPEAK", "KILL")。
        :param target_id: 动作目标的 Player ID (或者是 "Game" 节点的 ID)。
        :param visibility: 事件的可见性 (PUBLIC, WEREWOLF_TEAM, SEER_ONLY, PRIVATE)。
        :param properties: 额外的属性字典 (例如: {content: "我是预言家", round: 1})。
        """
        if properties is None:
            properties = {}

        # 确保动作是大写的，符合 Cypher 关系类型的惯例
        rel_type = action.upper()

        # 添加标准属性
        properties['visibility'] = visibility
        properties['timestamp'] = time.time()  # 使用 Unix 时间戳以便排序
        properties['datetime'] = datetime.now().isoformat()

        # 构建 Cypher 查询
        # 注意: 我们使用 MERGE 还是 CREATE?
        # 事件通常是唯一的历史记录，所以应该使用 CREATE。
        # 如果我们使用 MERGE，相同属性的重复事件会被合并，这通常不是我们想要的 (除非完全重复)。
        # 对于日志来说，每次调用都是一个新的事件，所以使用 CREATE。

        query = f"""
        MATCH (s:Player {{id: $source_id}})
        MATCH (t:Player {{id: $target_id}})
        CREATE (s)-[r:{rel_type}]->(t)
        SET r += $props
        RETURN type(r), r.timestamp
        """

        params = {
            "source_id": source_id,
            "target_id": target_id,
            "props": properties
        }

        try:
            self.adapter.run_query(query, params)
            logger.info(f"Logged event: {source_id} -[{rel_type} ({visibility})]-> {target_id}")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            raise

    def log_public_event(self, source_id: str, action: str, target_id: str, properties: Optional[Dict[str, Any]] = None):
        """
        记录一个公开事件 (所有人都可见)。

        :param source_id: 发起者 ID。
        :param action: 动作。
        :param target_id: 目标 ID。
        :param properties: 额外属性。
        """
        self.log_event(source_id, action, target_id, VISIBILITY_PUBLIC, properties)

    def log_private_event(self, source_id: str, action: str, target_id: str, visibility: str, properties: Optional[Dict[str, Any]] = None):
        """
        记录一个私有或受限可见性的事件。

        :param source_id: 发起者 ID。
        :param action: 动作。
        :param target_id: 目标 ID。
        :param visibility: 可见性级别 (例如: WEREWOLF_TEAM, SEER_ONLY)。
        :param properties: 额外属性。
        """
        self.log_event(source_id, action, target_id, visibility, properties)

    # --- 常用动作辅助方法 ---

    def log_vote(self, voter_id: str, target_id: str, round_num: int):
        """
        记录投票行为 (通常是公开的)。
        """
        self.log_public_event(voter_id, "VOTE", target_id, {"round": round_num})

    def log_kill(self, killer_id: str, target_id: str, round_num: int):
        """
        记录狼人击杀行为 (仅狼人团队可见)。
        """
        self.log_private_event(killer_id, "KILL", target_id, VISIBILITY_WEREWOLF, {"round": round_num})

    def log_check(self, seer_id: str, target_id: str, result: str, round_num: int):
        """
        记录预言家查验行为 (仅预言家可见)。

        :param result: 查验结果 (例如: "Werewolf" 或 "Good").
        """
        self.log_private_event(seer_id, "CHECK", target_id, VISIBILITY_SEER, {"round": round_num, "result": result})

    def log_speech(self, speaker_id: str, text: str, target_id: str, round_num: int):
        """
        记录发言 (通常是公开的)。

        注意: 需要指定 target_id。如果是对所有人说话，通常可以指向一个特定的 'Game' 节点或者任意目标，
        或者在业务逻辑中约定 target_id。
        """
        self.log_public_event(speaker_id, "SPEAK", target_id, {"content": text, "round": round_num})
