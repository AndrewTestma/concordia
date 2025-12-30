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
                "emotional_state": "Calm",
                "hypotheses_about_death": "尚未建立假设",
                "pressure_plan": "避免划水，提出质询"
            },
            "active_strategy": {
                "current_plan": "试探性发言",
                "tactical_steps": ["分析死者出局影响", "对后续发言者施压，要求输出干货", "观察谁在复读‘听发言’"],
                "speech_style": "逻辑分析型",
                "anti_silence_rules": ["禁止只说‘听发言’", "必须给出至少一个假设或问题", "点名至少一位需要回应的玩家"],
                "question_targets": []
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
        # 0. Sync facts
        # Parse Night Results from context (Private Message)
        # Format: [PRIVATE] 你查验了 {target}。他是 {is_good}。
        night_result_match = re.search(r"\[PRIVATE\].*?查验了 (.*?)。他是 (.*?)。", context)
        if night_result_match:
            target, identity = night_result_match.groups()
            self._card["critical_facts"]["night_results"] = f"查验了 {target}，身份是 {identity}"

        # Parse Death from context (Broadcast)
        # Format: [BROADCAST] 昨晚，{target} 死了。
        death_match = re.search(r"\[BROADCAST\].*?昨晚，(.*?) 死了。", context)
        if death_match:
            dead_player = death_match.group(1)
            self._card["critical_facts"]["death_toll"] = f"{dead_player} 死亡"

        # Detect passive patterns in context to trigger anti-silence mode
        passive_patterns = ["没有明确信息", "暂时没有信息", "继续听大家发言", "听发言"]
        if any(pat in context for pat in passive_patterns):
            self._card["active_strategy"]["current_plan"] = "主动试探并施压"
            self._card["active_strategy"]["speech_style"] = "猎人施压型"
            self._card["active_strategy"]["tactical_steps"] = [
                "分析首夜死亡可能原因并提出至少一个假设",
                "对后续发言者提出具体问题",
                "标记复读‘听发言’的玩家为可疑"
            ]

        chain = interactive_document.InteractiveDocument(self._model)
        chain.statement(f"背景信息:\n{context}")
        chain.statement(f"当前认知卡状态:\n```json\n{json.dumps(self._card, ensure_ascii=False, indent=2)}\n```")

        # Step 1: Perceive & Analyze
        chain.statement("任务 1: 感知与评估 (Perceive & Analyze)")
        chain.statement("请结合你的人设和已知事实，分析刚才这段发言对局势的影响，并更新你的认知卡中的 'inner_thought_process' 部分。")
        chain.statement("必须包含字段：observation_analysis、self_reflection、emotional_state、hypotheses_about_death。请给出至少一个关于死者的假设。")

        inner_thought_json = chain.open_question(
            "请以 JSON 格式返回更新后的 inner_thought_process（包含 hypotheses_about_death）:",
            max_tokens=600
        )
        self._update_card_section("inner_thought_process", inner_thought_json)

        # Step 2: Card Refresh
        chain.statement(f"更新后的思考:\n{json.dumps(self._card['inner_thought_process'], ensure_ascii=False, indent=2)}")
        chain.statement("任务 2: 策略更新 (Card Refresh)")
        chain.statement("基于最新的思考，调整你的策略 'active_strategy'。必须包含字段：current_plan、tactical_steps、speech_style、anti_silence_rules、question_targets。")

        # Special Instruction for Seer
        if self._role_component.get_role() == "预言家" and "查验" in self._card["critical_facts"].get("night_results", ""):
             chain.statement("!!! 重要提示 !!! 你是预言家且已经有了查验结果。为了好人阵营的胜利，你的策略必须包括：尽快在发言中明确报出查验结果，不要隐瞒！")

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
        card_json = json.dumps(self._card, ensure_ascii=False, indent=2)
        chain.statement(f"你现在的完整认知卡:\n```json\n{card_json}\n```")
        chain.statement(f"当前对话:\n{context}")

        chain.statement("任务 3: 执行输出 (Execute Speech)")
        chain.statement("请根据你当前的状态卡（包含人设、最新思考和策略），生成你这一轮的公开发言。")
        chain.statement("确保你的语气符合人设，逻辑符合策略。禁止只说‘听发言’或‘没有信息’，必须：1) 给出至少一个关于昨夜死亡的假设；2) 提出至少一个针对具体玩家的问题；3) 表达对‘划水’行为的明确态度。")

        # Enforce Seer Reveal
        if self._role_component.get_role() == "预言家" and "查验" in self._card["critical_facts"].get("night_results", ""):
            chain.statement("!!! 警告 !!! 你是预言家，你必须直接、明确地报出你的查验信息（谁是金水/好人，谁是查杀/狼人）。不要含糊其辞！")
        elif self._role_component.get_role() == "狼人":
             chain.statement("如果你是狼人，请伪装成好人。")

        speech = chain.open_question(
            "请生成发言内容 (直接输出内容，不需要JSON):",
            max_tokens=600
        )

        # Output to terminal as requested: Card -> Thoughts -> Speech
        print(f"\n[{self._player_name} 的思考过程]")
        print("-" * 30)
        print(f"1. 认知卡 (Cognition Card):\n{card_json}")
        print(f"2. 思考 (Thoughts):\n{json.dumps(self._card['inner_thought_process'], ensure_ascii=False, indent=2)}")
        print(f"3. 发言 (Speech):\n{speech}")
        print("-" * 30 + "\n")

        return speech
