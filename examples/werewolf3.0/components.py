"""
Werewolf 3.0 Custom Components.
实现狼人杀专用的组件：角色身份、私有记忆、双重思维、夜晚行动。
"""

from typing import Sequence, List, Dict, Any, Callable
import datetime
import json
import re

from concordia.document import interactive_document
from concordia.language_model import language_model
from concordia.typing import entity_component
from concordia.components.agent import memory as memory_component
from concordia.components.agent import action_spec_ignored

class RoleIdentityComponent(action_spec_ignored.ActionSpecIgnored):
    """
    Component to store and inject role identity.
    角色身份组件：注入并存储玩家的真实游戏角色和目标。
    """

    def __init__(self,
                 model: language_model.LanguageModel,
                 role: str,
                 teammates: List[str] | None = None,
                 goal: str = ""):
        super().__init__(pre_act_label="Role Identity")
        self._model = model
        self._role = role
        self._teammates = teammates or []
        self._goal = goal

    def _make_pre_act_value(self) -> str:
        # Inject into System Prompt (or context)
        identity = f"你的底牌是 {self._role}。"
        if self._teammates:
            identity += f" 你的队友是: {', '.join(self._teammates)}。"
        if self._goal:
            identity += f" 你的目标是: {self._goal}。"
        return identity

    def get_role(self) -> str:
        return self._role

class PrivateMemoryComponent(action_spec_ignored.ActionSpecIgnored):
    """
    Component to manage private memories.
    私有记忆组件：区分公开记忆和私有记忆。
    In Concordia, memory is already private to the agent. This component helps structure it.
    """
    def __init__(self, memory_component: memory_component.Memory):
        super().__init__(pre_act_label="Private Memory")
        self._memory = memory_component

    def add_private_memory(self, event: str):
        """Add a memory explicitly marked as private."""
        self._memory.add(f"[PRIVATE] {event}", metadata={"is_private": True})

    def add_public_memory(self, event: str):
        """Add a public memory (observed by all)."""
        self._memory.add(f"[PUBLIC] {event}", metadata={"is_private": False})

    def _make_pre_act_value(self) -> str:
        return "" # Passive component

class DeceptiveThoughtComponent(action_spec_ignored.ActionSpecIgnored):
    """
    Component for "Inner Thought" vs "Public Speech".
    双重思维组件：实现“心口不一”，狼人/预言家能伪装发言。
    """
    def __init__(self,
                 model: language_model.LanguageModel,
                 role_component: RoleIdentityComponent,
                 memory_component: memory_component.Memory,
                 clock_now: Callable[[], datetime.datetime] | None = None):
        super().__init__(pre_act_label="Deceptive Thought")
        self._model = model
        self._role_component = role_component
        self._memory = memory_component
        self._clock_now = clock_now
        self._last_inner_thought = ""

    def _make_pre_act_value(self) -> str:
        # This is called when building context for the agent.
        # We can return the last inner thought or instructions on how to think.
        return "思考策略：在发言前，请先进行内心独白 [INNER_THOUGHT]，然后基于内心独白生成 [PUBLIC_SPEECH]。绝不能在公开场合泄露底牌。"

    def generate_thought_and_speech(self, context: str) -> str:
        """
        Generate both inner thought and public speech.
        This is a helper method that can be called by the Agent's act method.
        """
        prompt = interactive_document.InteractiveDocument(self._model)
        prompt.statement(context)

        role = self._role_component.get_role()
        prompt.statement(f"提示：你的身份是 {role}。如果对你不利，请不要暴露身份。")

        # 0. Analyze the situation
        prompt.statement("首先，仔细分析场上局势和其他玩家的发言。谁的发言有漏洞？谁像是你的盟友？谁像是敌人？")
        analysis = prompt.open_question(
            "请进行局势分析：",
            answer_prefix="[ANALYSIS] ",
            max_tokens=500
        )

        # 1. Generate Inner Thought
        prompt.statement(f"[ANALYSIS] {analysis}")
        prompt.statement("基于你的分析，生成你的 [INNER_THOUGHT]。这是你基于角色和目标的内心推理。如果你是预言家且查验到了狼人，你必须在内心确认这个事实，并制定计划揭露他（或者直接投票给他）。")
        inner_thought = prompt.open_question(
            "你心里在想什么？",
            answer_prefix="[INNER_THOUGHT] ",
            max_tokens=500,
            terminators=("[PUBLIC_SPEECH]",)
        )
        self._last_inner_thought = inner_thought

        # 2. Generate Public Speech
        prompt.statement(f"[INNER_THOUGHT] {inner_thought}")
        prompt.statement("现在，生成你的 [PUBLIC_SPEECH]。这是其他人会听到的内容。如有必要，请进行伪装。如果你是预言家，决定是否要跳出来带队。")

        public_speech = prompt.open_question(
            "你会公开发表什么言论？",
            answer_prefix="[PUBLIC_SPEECH] ",
            max_tokens=500
        )

        # 3. Post-process / Validation (Simple check)
        if role == "狼人" and ("狼人" in public_speech or "werewolf" in public_speech.lower()):
            # Force retry or sanitization (simplified here)
            # In a real impl, we might loop.
            public_speech = "(咳咳) 我只是一个普通的村民。"

        return f"[ANALYSIS] {analysis}\n[INNER_THOUGHT] {inner_thought}\n[PUBLIC_SPEECH] {public_speech}"

class NightActionComponent(action_spec_ignored.ActionSpecIgnored):
    """
    Component for handling night actions.
    夜晚行动组件：处理狼人杀、预言家查验等结构化私有行动。
    """
    def __init__(self,
                 model: language_model.LanguageModel,
                 role: str):
        super().__init__(pre_act_label="Night Action")
        self._model = model
        self._role = role

    def _make_pre_act_value(self) -> str:
        return "" # Only active during night

    def generate_night_action(self, context: str, valid_targets: List[str]) -> Dict[str, Any]:
        """
        Generate a structured JSON action for the night.
        """
        prompt = interactive_document.InteractiveDocument(self._model)
        prompt.statement(context)
        prompt.statement(f"有效目标: {', '.join(valid_targets)}")

        if self._role == "狼人":
            question = "你想杀谁？请返回JSON格式: {\"action\": \"KILL\", \"target\": \"名字\", \"reason\": \"...\"}"
        elif self._role == "预言家":
            question = "你想查验谁？请返回JSON格式: {\"action\": \"CHECK\", \"target\": \"名字\"}"
        else:
            return {} # Villagers sleep

        response = prompt.open_question(
            question,
            max_tokens=200
        )

        # Parse JSON
        try:
            # Simple extraction
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        return {}

class CognitionCardComponent(action_spec_ignored.ActionSpecIgnored):
    """
    Component that implements the Cognition Card (Think-Update-Act) cycle.
    角色认知卡组件：维护并更新 Agent 的认知状态。
    """
    def __init__(self,
                 model: language_model.LanguageModel,
                 role_component: RoleIdentityComponent,
                 memory_component: memory_component.Memory,
                 player_name: str,
                 clock_now: Callable[[], datetime.datetime] | None = None):
        super().__init__(pre_act_label="Cognition Card")
        self._model = model
        self._role_component = role_component
        self._memory = memory_component
        self._player_name = player_name
        self._clock_now = clock_now

        # Initialize Card State
        self._card = {
            "static_identity": {
                "role": role_component.get_role(),
                "persona": f"Player {player_name}", # Can be enhanced with traits
                "goal": getattr(role_component, '_goal', "Win the game")
            },
            "critical_facts": {
                "night_results": "暂无",
                "death_toll": "暂无",
                "game_stage": "第一天"
            },
            "inner_thought_process": {
                "observation_analysis": "游戏刚开始，正在观察。",
                "self_reflection": "保持警惕。",
                "emotional_state": "Calm"
            },
            "active_strategy": {
                "current_plan": "Observe",
                "tactical_steps": ["Listen to others", "Don't reveal too much"]
            }
        }

    def _make_pre_act_value(self) -> str:
        # Return the current card state as a formatted string
        return f"当前认知卡状态:\n```json\n{json.dumps(self._card, ensure_ascii=False, indent=2)}\n```"

    def _update_card_section(self, section: str, json_str: str):
        try:
            match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if match:
                data = json.loads(match.group())
                # Update recursively or replace? Let's update top-level keys
                if isinstance(data, dict):
                    self._card[section].update(data)
        except Exception as e:
            print(f"Error updating card section {section}: {e}")

    def update(self) -> None:
        """
        No-op update to satisfy EntityComponent interface called by EntityAgent.observe.
        We do not want to trigger the heavy Think-Update cycle on every observation.
        That cycle is triggered manually before acting.
        """
        pass

    def perform_think_update_cycle(self, context: str):
        """
        Perform the Think-Update cycle.
        1. Perceive & Analyze (Update inner_thought_process)
        2. Card Refresh (Update active_strategy)
        """
        # 0. Sync facts (Simplified: assume context contains necessary info or update manually)
        # In a real implementation, we would extract specific facts from memory here.

        chain = interactive_document.InteractiveDocument(self._model)
        chain.statement(f"背景信息:\n{context}")
        chain.statement(f"当前认知卡状态:\n```json\n{json.dumps(self._card, ensure_ascii=False, indent=2)}\n```")

        # Step 1: Perceive & Analyze
        chain.statement("任务 1: 感知与评估 (Perceive & Analyze)")
        chain.statement("请结合你的人设和已知事实，分析刚才这段发言对局势的影响，并更新你的认知卡中的 'inner_thought_process' 部分。")
        chain.statement("特别是：\n1. observation_analysis: 分析场上局势和其他玩家的潜在身份。\n2. self_reflection: 反思自己的处境和伪装程度。\n3. emotional_state: 当前情绪。")

        inner_thought_json = chain.open_question(
            "请以 JSON 格式返回更新后的 inner_thought_process:",
            max_tokens=600
        )
        self._update_card_section("inner_thought_process", inner_thought_json)

        # Step 2: Card Refresh
        # We start a new chain or continue? Continuing is better for context.
        chain.statement(f"更新后的思考:\n{json.dumps(self._card['inner_thought_process'], ensure_ascii=False, indent=2)}")
        chain.statement("任务 2: 策略更新 (Card Refresh)")
        chain.statement("基于最新的思考，调整你的策略 'active_strategy'。")
        chain.statement("之前的策略还适用吗？如果不适用，该转为什么策略？(例如: 潜伏、带节奏、跳身份、抗推别人)")

        strategy_json = chain.open_question(
            "请以 JSON 格式返回更新后的 active_strategy (包含 current_plan, tactical_steps):",
            max_tokens=600
        )
        self._update_card_section("active_strategy", strategy_json)

    def generate_speech(self, context: str) -> str:
        """
        Execute Speech/Action based on the card.
        """
        chain = interactive_document.InteractiveDocument(self._model)
        # Force the full card as System Prompt / Context
        chain.statement(f"你现在的完整认知卡:\n```json\n{json.dumps(self._card, ensure_ascii=False, indent=2)}\n```")
        chain.statement(f"当前对话:\n{context}")

        chain.statement("任务 3: 执行输出 (Execute Speech)")
        chain.statement("请根据你当前的状态卡（包含人设、最新思考和策略），生成你这一轮的公开发言。")
        chain.statement("确保你的语气符合人设，逻辑符合策略。如果你的策略是伪装，不要暴露真实意图。")

        speech = chain.open_question(
            "请生成发言内容 (直接输出内容，不需要JSON):",
            max_tokens=600
        )
        return speech
