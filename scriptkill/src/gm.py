import logging
import time
from typing import List, Dict, Optional
import json

from src.loader import ScriptManifest, PhaseConfig
from src.agent import UniversalAgent
from src.dify_client import UniversalDifyClient
from src.director import DirectorAgent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GameMaster")

class GameMaster:
    """
    游戏主持人 (PuppetMaster)，负责驱动整个剧本杀流程。
    """
    def __init__(self, manifest: ScriptManifest, dify_client: UniversalDifyClient):
        self.manifest = manifest
        self.dify_client = dify_client
        self.agents: Dict[str, UniversalAgent] = {}
        self.director: Optional[DirectorAgent] = None
        self.current_phase_index = 0
        self.history = [] # 全局历史记录

        # 初始化 Agents 和 Director
        self._initialize_agents()
        self._initialize_director()

    def _initialize_agents(self):
        logger.info("正在初始化所有角色...")
        for char_config in self.manifest.characters:
            agent = UniversalAgent(
                config=char_config,
                dify_client=self.dify_client
            )
            self.agents[char_config.id] = agent
            logger.info(f"角色 [{char_config.name}] 已就绪。")

    def _initialize_director(self):
        logger.info("正在初始化导演系统...")
        self.director = DirectorAgent(
            visual_config=self.manifest.visual_style,
            dify_client=self.dify_client
        )

    def broadcast(self, message: str, sender: str = "GM"):
        """向所有 Agent 广播消息"""
        full_msg = f"{sender}: {message}"
        self.history.append(full_msg)

        # 记录到所有 Agent 的记忆中
        for agent in self.agents.values():
            agent.observe(full_msg)

        # 通知导演
        if self.director:
            self.director.observe(full_msg)

    def _get_current_phase(self) -> Optional[PhaseConfig]:
        if 0 <= self.current_phase_index < len(self.manifest.phases):
            return self.manifest.phases[self.current_phase_index]
        return None

    def run(self):
        """开始游戏主循环"""
        logger.info(f"游戏开始: {self.manifest.meta.name}")

        while self.current_phase_index < len(self.manifest.phases):
            phase = self.manifest.phases[self.current_phase_index]
            self._run_phase(phase)
            self.current_phase_index += 1

        # 游戏结束，通知导演收尾
        if self.director:
            self.director.finalize()
        logger.info("游戏结束。")

    def _run_phase(self, phase: PhaseConfig):
        logger.info(f"\n=== 进入阶段: {phase.label} ({phase.type}) ===")

        # 1. 设置场景
        logger.info(f"当前场景: {phase.scene}")
        for agent in self.agents.values():
            agent.set_scene(phase.scene)

        # 通知导演切换场景
        if self.director:
            self.director.set_scene(phase.scene)

        # 2. 广播阶段指令
        self.broadcast(f"【阶段指令】{phase.instruction}")

        # 3. 根据类型调度
        if phase.type == "SEQUENTIAL_SPEAK":
            self._run_sequential_speak(phase)
        elif phase.type == "FREE_DISCUSSION":
            self._run_free_discussion(phase)
        else:
            logger.warning(f"未知阶段类型: {phase.type}")

    def _run_sequential_speak(self, phase: PhaseConfig):
        """顺序发言模式：每个角色轮流发言一次"""
        for char_id, agent in self.agents.items():
            action_spec = type('obj', (object,), {'call_to_action': f"现在轮到你了。{phase.instruction}"})
            response = agent.act(action_spec)
            self.broadcast(response, sender=agent.name)

    def _run_free_discussion(self, phase: PhaseConfig):
        """自由讨论模式：指定轮数"""
        max_turns = phase.duration_turns or 5
        logger.info(f"自由讨论开始，共 {max_turns} 轮。")

        # 简单策略：轮流发言 (实际可以是抢答或由 LLM 决定谁发言)
        # 这里为了演示，依然使用轮流，但循环多次
        turn = 0
        agent_list = list(self.agents.values())

        while turn < max_turns:
            current_agent = agent_list[turn % len(agent_list)]

            action_spec = type('obj', (object,), {'call_to_action': f"自由讨论阶段。{phase.instruction}"})
            response = current_agent.act(action_spec)
            self.broadcast(response, sender=current_agent.name)

            turn += 1

if __name__ == "__main__":
    print("GameMaster module loaded.")
