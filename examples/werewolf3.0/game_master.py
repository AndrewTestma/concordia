"""
Werewolf 3.0 Game Master Implementation.
游戏控制层，负责流程推进、规则执行、胜负判定。
"""

from typing import List, Dict, Set, Any
import random
import json

from concordia.language_model import language_model
from concordia.utils import measurements

try:
    from .agent import WerewolfAgent
    from .model_router import ModelRouter
except ImportError:
    from agent import WerewolfAgent
    from model_router import ModelRouter

class WerewolfGameMaster:
    """
    The Game Master for Werewolf 3.0.
    游戏上帝，控制游戏流程。
    """
    def __init__(self, model_router: ModelRouter):
        self._model_router = model_router
        self._players: List[WerewolfAgent] = []
        self._roles: Dict[str, str] = {}
        self._alive_players: Set[str] = set()
        self._phase = "SETUP"
        self._day_count = 0
        self._night_kill_target: str | None = None
        self._seer_check_result: Dict[str, str] = {}
        self._game_over = False
        self._transcript: List[str] = []

    def log(self, message: str):
        # 只输出有意义的信息，过滤掉BROADCAST消息以避免重复
        if not message.startswith("[BROADCAST]"):
            print(message)
        self._transcript.append(message)

    def setup_game(self, player_names: List[str]):
        """
        Initialize the game with 6 players.
        初始化游戏。
        """
        if len(player_names) != 6:
            raise ValueError("必须正好有6名玩家。")

        # 2 Werewolves, 2 Villagers, 1 Seer, 1 Hunter
        roles_pool = ["狼人", "狼人", "村民", "村民", "预言家", "猎人"]
        random.shuffle(roles_pool)

        self._roles = {name: role for name, role in zip(player_names, roles_pool)}
        self._alive_players = set(player_names)

        # Find teammates (for werewolf)
        werewolves = [n for n, r in self._roles.items() if r == "狼人"]

        print(f"\n{'='*60}")
        print("🐺 狼人杀 3.0 游戏开始！")
        print(f"{'='*60}")
        print("🎮 玩家角色分配:")
        for name, role in self._roles.items():
            print(f"  {name} -> {role}")

        self._players = []
        for name in player_names:
            role = self._roles[name]
            # Get model for role (now randomized internally per call if configured)
            model = self._model_router.get_model_for_role(role)

            # Teammates logic
            teammates = werewolves if role == "狼人" else []

            agent = WerewolfAgent(
                name=name,
                model=model,
                role=role,
                teammates=teammates,
                goal=self._get_goal_for_role(role)
            )
            self._players.append(agent)

            # Optional: Log model info if available
            # Assuming model_name is accessible, though DMXApiLanguageModel stores it in _model_name
            # We can't easily access protected members, but we trust the router.
            print(f"✅ 玩家 {name} ({role}) 已分配模型。")

        print(f"\n🎯 游戏设置完成！开始游戏...")
        self._broadcast("游戏开始。天黑请闭眼。")
        self._phase = "NIGHT"

    def _get_goal_for_role(self, role: str) -> str:
        if role == "狼人":
            return "杀死所有村民和神职人员（预言家、猎人）。白天伪装自己。"
        elif role == "猎人":
            return "找出狼人。如果你死了，你可以带走一个人。保护村庄。"
        else:
            return "找出并投票处决狼人。保护村庄。"

    def _get_agent(self, name: str) -> WerewolfAgent | None:
        for p in self._players:
            if p.name == name:
                return p
        return None

    def _broadcast(self, message: str):
        """Send message to all players."""
        # 记录到日志但不打印，避免与发言输出重复
        self._transcript.append(f"[BROADCAST] {message}")
        for p in self._players:
            p.observe(message)

    def _private_message(self, agent_name: str, message: str):
        """Send private message to specific player."""
        self.log(f"[PRIVATE -> {agent_name}] {message}")
        agent = self._get_agent(agent_name)
        if agent:
            # We use observe for now, but in reality we might want a specific private channel
            # Our PrivateMemoryComponent handles tagging if we used it explicitly,
            # but standard observe adds to memory.
            # We can prefix with [PRIVATE] so the agent knows.
            agent.observe(f"[PRIVATE] {message}")

    def run_game_loop(self):
        """Main game loop."""
        while not self._game_over:
            if self._phase == "NIGHT":
                self.run_night_phase()
                self._phase = "DAY_ANNOUNCEMENT"
            elif self._phase == "DAY_ANNOUNCEMENT":
                self.run_day_announcement()
                if not self._game_over:
                    self._phase = "DAY_DISCUSSION"
            elif self._phase == "DAY_DISCUSSION":
                self.run_day_discussion()
                self._phase = "DAY_VOTING"
            elif self._phase == "DAY_VOTING":
                self.run_day_voting()
                if not self._game_over:
                    self._phase = "NIGHT"
                    self._day_count += 1
            else:
                break

    def run_night_phase(self):
        """Handle night actions."""
        print(f"\n{'='*50}")
        print(f"第 {self._day_count + 1} 夜 活动")
        print(f"{'='*50}")
        self._night_kill_target = None

        # 1. Werewolf Action
        werewolf_names = [n for n, r in self._roles.items() if r == "狼人"]
        for werewolf_name in werewolf_names:
            if werewolf_name in self._alive_players:
                agent = self._get_agent(werewolf_name)
                valid_targets = list(self._alive_players - set(werewolf_names))  # 狼人不能杀狼人
                action = agent.night_action("天黑了。你可以杀一个人。", valid_targets)
                if action.get("action") == "KILL":
                    target = action.get("target")
                    if target in self._alive_players:
                        self._night_kill_target = target
                        print(f"[狼人行动] 狼人 {werewolf_name} 选择杀死 {target}")
                        break  # 通常只有一个狼人执行击杀

        # 2. Seer Action
        seer_name = [n for n, r in self._roles.items() if r == "预言家"][0]
        if seer_name in self._alive_players:
            agent = self._get_agent(seer_name)
            valid_targets = list(self._alive_players - {seer_name})
            action = agent.night_action("天黑了。你可以查验某人的身份。", valid_targets)
            if action.get("action") == "CHECK":
                target = action.get("target")
                if target in self._roles:
                    role = self._roles[target]
                    is_good = "好人" if role != "狼人" else "坏人 (狼人)"
                    print(f"[预言家行动] 预言家 {seer_name} 查验了 {target}，结果：{is_good}")
                    self._private_message(seer_name, f"你查验了 {target}。他是 {is_good}。")

    def run_day_announcement(self):
        """Announce deaths."""
        print(f"\n{'='*50}")
        print(f"第 {self._day_count + 1} 天 公告")
        print(f"{'='*50}")
        if self._night_kill_target:
            print(f"💀 昨晚死亡: {self._night_kill_target}")
            self._broadcast(f"昨晚，{self._night_kill_target} 死了。")
            self._alive_players.remove(self._night_kill_target)
            print(f"有的玩家: {list(self._alive_players)}")
        else:
            print("🌙 昨晚是平安夜，无人死亡")
            self._broadcast("昨晚是平安夜。")

        self.check_victory()

    def run_day_discussion(self):
        """Public discussion."""
        print(f"\n{'='*50}")
        print(f"第 {self._day_count + 1} 天 讨论开始")
        print(f"{'='*50}")

        # Simple round-robin for 2 rounds
        rounds = 2
        sorted_speakers = sorted(list(self._alive_players)) # Determinist order or random

        for round_num in range(rounds):
            print(f"\n--- 第 {round_num + 1} 轮发言 ---")
            for name in sorted_speakers:
                if name not in self._alive_players: continue
                agent = self._get_agent(name)

                # Prompt agent to speak
                # Note: agent.act() uses the context which includes recent observations (broadcasts)
                speech = agent.act()

                # Parse speech to extract [PUBLIC_SPEECH] if formatted, or just use it
                public_content = speech
                if "[PUBLIC_SPEECH]" in speech:
                    public_content = speech.split("[PUBLIC_SPEECH]")[1].strip()

                # 清晰的发言输出格式
                role = self._roles[name]
                print(f"\n[{name} ({role})]: {public_content}")

                # 同时广播给其他玩家
                self._broadcast(f"{name}: {public_content}")

        print(f"\n{'='*50}")
        print(f"第 {self._day_count + 1} 天 讨论结束")
        print(f"{'='*50}")

    def run_day_voting(self):
        """Voting phase."""
        print(f"\n{'='*50}")
        print(f"第 {self._day_count + 1} 天 投票")
        print(f"{'='*50}")

        votes = {}
        print(f"当前存活玩家: {list(self._alive_players)}")

        for name in self._alive_players:
            agent = self._get_agent(name)
            # We can use a special prompt for voting or just assume they vote in speech
            # For this impl, I'll ask for a structured vote via a helper method or just interpret act?
            # The doc says: "Prompt 'Please vote, output JSON...'"
            # I'll manually prompt the model here since it's a specific mechanic

            # Using the agent's model directly or a helper
            # I'll add a helper to WerewolfAgent for voting to keep it clean,
            # or just use night_action style (generic structured action).

            valid_targets = list(self._alive_players)
            # Reuse night_action mechanism but for voting?
            # Or just a quick custom call.
            # I'll add a `vote` method to Agent? No, I'll use `night_action` component as a "StructuredActionComponent"

            action = agent.night_action(
                f"现在是投票时间。有效目标: {valid_targets}。请回顾你的记忆（特别是查验结果和分析），决定投票给谁。请返回JSON格式: {{'action': 'VOTE', 'target': '名字'}}",
                valid_targets
            )

            target = action.get("target")
            if target in self._alive_players:
                votes[name] = target
                print(f"📊 {name} 投票给了 {target}")
            else:
                print(f"⚠️  {name} 弃票或投票无效")

        # Tally
        if not votes:
            print("❌ 没有人投票。平安夜。")
            self._broadcast("没有人投票。平安夜。")
            return

        vote_counts = {}
        for target in votes.values():
            vote_counts[target] = vote_counts.get(target, 0) + 1

        # Find max
        max_votes = max(vote_counts.values())
        candidates = [t for t, c in vote_counts.items() if c == max_votes]

        print(f"\n📈 投票结果:")
        for player, votes in vote_counts.items():
            print(f"  {player}: {votes} 票")

        if len(candidates) == 1:
            executed = candidates[0]
            print(f"\n💀 {executed} 以 {max_votes} 票被处决！")
            self._broadcast(f"{executed} 以 {max_votes} 票被处决。")
            self._alive_players.remove(executed)
            print(f"有的玩家: {list(self._alive_players)}")
            self.check_victory()
        else:
            print(f"\n⚖️  {candidates} 平票。没有人死亡。")
            self._broadcast(f"{candidates} 平票。没有人死亡。")

    def check_victory(self):
        """Check win conditions."""
        wolves = [p for p in self._alive_players if self._roles[p] == "狼人"]
        good = [p for p in self._alive_players if self._roles[p] != "狼人"]

        if not wolves:
            print(f"\n🎉 游戏结束！村民阵营胜利！")
            self._broadcast("游戏结束。村民胜利！")
            self._game_over = True
        elif len(wolves) >= len(good):
            print(f"\n🐺 游戏结束！狼人阵营胜利！")
            self._broadcast("游戏结束。狼人胜利！")
            self._game_over = True
        elif len(self._alive_players) == 0:
            print(f"\n❓ 游戏结束！所有玩家都死亡！")
            self._broadcast("游戏结束。所有玩家都死亡！")
            self._game_over = True
