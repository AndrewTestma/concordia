import logging
from typing import List, Dict, Any
import random

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyModule:
    """
    StrategyModule (夜间策略模块)

    职责:
    - 基于玩家的视角 (TheEye) 和内部状态 (PlayerState)，制定夜间行动的战术目标 (Objective)。
    - 这一目标将作为 Context Payload 的一部分发送给 Dify，指导 LLM 生成具体的行动。
    
    支持角色:
    - Werewolf (狼人): 寻找预言家，击杀高威胁目标。
    - Seer (预言家): 查验高怀疑目标或存疑目标。
    - Witch (女巫): 决定是否使用解药或毒药。
    - Guard (守卫): 决定守护谁。
    """

    def __init__(self):
        pass

    def run_day_strategy(self, player_state: 'PlayerState', visible_events: List[Dict[str, Any]]):
        """
        执行白天策略分析 (发言生成调优)。
        """
        role = player_state.role.upper()
        logger.info(f"正在为 {player_state.player_name} ({role}) 生成白天发言策略...")

        if role == 'WEREWOLF':
            self._werewolf_day_strategy(player_state, visible_events)
        elif role == 'SEER':
            self._seer_day_strategy(player_state, visible_events)
        elif role == 'VILLAGER':
            self._villager_day_strategy(player_state, visible_events)
        else:
            player_state.objective = "策略目标：根据场上局势发言，尽量隐藏身份或找出狼人。"

    def _werewolf_day_strategy(self, player_state, events):
        """
        狼人白天策略 (伪装与攻击):
        1. 伪装 (Camouflage): 如果没有被查杀，尽量表现得像个平民。
        2. 悍跳 (Claim): 如果决定悍跳预言家，需要攻击真预言家。
        3. 煽动 (Incitement): 抓住好人的逻辑漏洞进行攻击。
        """
        # 简单逻辑：检查是否有人跳预言家
        claimed_seers = [e.get('source_name') for e in events if e.get('action') == 'CLAIM' and e.get('properties', {}).get('role') == 'SEER']
        
        # 检查自己是否已经跳过预言家 (在之前的轮次)
        # 这里简化处理，假设 Dify 会根据 memory 知道自己跳没跳。
        # 我们在这里给出的建议是方向性的。

        if not claimed_seers:
            player_state.objective = "发言策略：伪装成平民。表示目前信息不足，不要表现得太有攻击性，以免引起怀疑。"
        else:
            # 如果有人跳预言家，且不是队友（假设队友信息已知，这里简化为所有跳的都是敌人，除非自己跳）
            # 这里的逻辑可以更复杂。
            player_state.objective = "发言策略：场上已有预言家起跳。如果他是真预言家，寻找他的逻辑漏洞（如验人逻辑不通）进行攻击。或者跟票大多数人，避免成为焦点。"

    def _seer_day_strategy(self, player_state, events):
        """
        预言家白天策略 (逻辑攻击):
        1. 报验人 (Report): 必须清晰说出昨晚的查验结果。
        2. 留警徽流 (Badge): 如果有警徽 (本版暂无)，安排后事。
        3. 攻击 (Attack): 号召大家放逐查杀对象，或怀疑对自己有敌意的人。
        """
        # 查找昨晚的查验结果 (从 visible_events 中找 CHECK 事件)
        # 注意：visible_events 是按时间排序的，最近的一次 CHECK 应该是昨晚的。
        my_checks = [e for e in events if e.get('action') == 'CHECK' and e.get('properties', {}).get('visibility') == 'SEER_ONLY']
        
        last_check = my_checks[-1] if my_checks else None
        
        if last_check:
            target = last_check.get('target_name') # 假设是 Name
            result = last_check.get('properties', {}).get('result')
            
            if result == 'WEREWOLF':
                player_state.objective = f"发言策略：【强攻击】昨晚查验 {target} 是狼人！他是查杀！全票出 {target}！不用听他辩解！"
            else:
                player_state.objective = f"发言策略：昨晚查验 {target} 是金水（好人）。先把他保下来。今天我们在剩下的牌里找狼。"
        else:
             player_state.objective = "发言策略：我是预言家，昨晚没有查验信息（或被首刀无法验人）。"

    def _villager_day_strategy(self, player_state, events):
        """
        平民白天策略:
        1. 分析局势，站边预言家。
        """
        player_state.objective = "发言策略：认真听取预言家的发言。如果有人对跳，对比他们的发言状态和验人逻辑。不要轻易做决定，多听多看。"

    def run_night_strategy(self, player_state: 'PlayerState', visible_events: List[Dict[str, Any]]):
        """
        执行夜间策略分析，更新 player_state.objective。

        :param player_state: 玩家状态对象。
        :param visible_events: 玩家可见的事件列表 (从 TheEye 获取)。
        """
        role = player_state.role.upper()
        logger.info(f"正在为 {player_state.player_name} ({role}) 生成夜间策略...")

        if role == 'WEREWOLF':
            self._werewolf_strategy(player_state, visible_events)
        elif role == 'SEER':
            self._seer_strategy(player_state, visible_events)
        elif role == 'WITCH':
            self._witch_strategy(player_state, visible_events)
        elif role == 'GUARD':
            self._guard_strategy(player_state, visible_events)
        elif role == 'VILLAGER':
            # 平民夜间通常无行动，或者是“闭眼玩家”
            player_state.objective = "睡觉，等待天亮。如果有动静，尝试记住声音来源。"
        else:
            player_state.objective = "保持警惕。"

    def _werewolf_strategy(self, player_state, events):
        """
        狼人策略:
        1. 寻找跳预言家的人 (CLAIM SEER)。
        2. 如果有真假预言家对跳，优先刀掉真预言家面大的（这里简化为刀掉声称是预言家的人）。
        3. 如果没有明确目标，刀掉“好人面”高（怀疑度低）的玩家。
        """
        # 1. 分析跳身份的情况
        claimed_seers = []
        for event in events:
            # 检查是否有 CLAIM SEER 事件
            # event 结构参考 TheEye: {'source_name': '...', 'action': '...', 'properties': {...}}
            # 注意：CLAIM 动作通常会有 properties: {'role': 'SEER'}
            action = event.get('action')
            props = event.get('properties', {})
            if action == 'CLAIM' and props.get('role') == 'SEER':
                source_name = event.get('source_name') # 这里可能是 Name，我们需要 ID 吗？
                # TheEye 返回的是 Name，最好能映射回 ID，或者我们在 PlayerState 里直接处理 Name
                # 假设我们能通过 Name 找到 ID，或者 TheEye 返回 source_id (需检查 TheEye 实现)
                # TheEye 实现返回 source.name, type(r), ... 
                # 我们假设暂时用 Name 作为标识，或者假设 PlayerState 的 key 是 ID，这里需要对应。
                # 为了简单，假设 Name 就是 ID，或者在 logic 中不做严格 ID 匹配，只是生成文本提示。
                claimed_seers.append(source_name)

        if claimed_seers:
            target = claimed_seers[0] # 简单策略：刀第一个跳预言家的
            player_state.objective = f"战术目标：击杀自称预言家的 {target}。如果有多人对跳，优先击杀逻辑漏洞大的。"
        else:
            # 2. 刀掉怀疑度最低的（即最像好人的）
            # get_most_suspicious 返回的是怀疑度高的。我们需要怀疑度低的。
            # 这里的 suspicion_matrix 存的是 ID。
            # 我们随机选一个怀疑度 < 50 的作为目标
            low_suspicion_targets = [pid for pid, score in player_state.suspicion_matrix.items() if score < 50]
            if low_suspicion_targets:
                target = random.choice(low_suspicion_targets)
                player_state.objective = f"战术目标：场上没有预言家露面，击杀 {target}，因为他看起来最像好人（威胁大）。"
            else:
                player_state.objective = "战术目标：随机屠城，优先击杀话多的玩家。"

    def _seer_strategy(self, player_state, events):
        """
        预言家策略:
        1. 优先查验怀疑度最高的人 (怀疑他是狼)。
        2. 或者查验“焦点牌” (发言多，带节奏的人)。
        """
        # 获取怀疑度最高的 1 位玩家
        most_suspicious = player_state.get_most_suspicious(1)
        
        if most_suspicious:
            target_id, score = most_suspicious[0]
            player_state.objective = f"战术目标：查验 {target_id}。他对我的威胁最大（怀疑度 {score}），必须验证他的身份。"
        else:
            # 如果没有特别怀疑的（比如第一晚），随机查一个非自己
            # 实际应查验“此时无声胜有声”的人或“乱带节奏”的人
            player_state.objective = "战术目标：查验一名发言活跃但逻辑混乱的玩家，或者查验一名特别沉默的玩家（深水狼）。"

    def _witch_strategy(self, player_state, events):
        """
        女巫策略:
        1. 救人: 如果银水（被刀者）是自己或重要角色（如预言家），使用解药。
        2. 毒人: 如果有确定的狼人（怀疑度 > 80），使用毒药。
        """
        # 女巫能看到狼刀吗？
        # 在我们的规则中，女巫通常在夜间可以看到谁被刀了 (Night Save 阶段)。
        # TheEye 需要支持女巫看到 KILL 事件 (如果规则允许)。
        # 假设 TheEye 还没实现“女巫可见狼刀”，那么女巫只能基于“盲救”或不救。
        # 如果实现了，events 里应该有 action='KILL' 且 visibility='WITCH_ONLY' (假设)
        
        dying_player = None
        for event in events:
            # 假设 GM 会在女巫行动前写入一个临时事件让女巫看到，或者女巫能看到狼人的 KILL
            # 但通常狼刀是 WEREWOLF_TEAM 可见。女巫能看到是因为 GM 告诉她。
            # 这里假设 events 里包含 "Tonight {X} died" 的信息 (通过 LogicHints 或特殊 Event)
            pass

        # 简化策略
        high_suspicion = player_state.get_most_suspicious(1)
        if high_suspicion and high_suspicion[0][1] > 80:
             target_id, score = high_suspicion[0]
             player_state.objective = f"战术目标：使用毒药带走 {target_id}，我非常怀疑他是狼人（怀疑度 {score}）。"
        else:
             player_state.objective = "战术目标：谨慎使用解药。如果是第一晚，可以考虑自救或救人（银水）。没有把握不要开毒。"

    def _guard_strategy(self, player_state, events):
        """
        守卫策略:
        1. 优先守护预言家 (如果已跳)。
        2. 守护自己 (如果觉得自己危险)。
        3. 空守或守护好人 (避免同守同救)。
        """
        claimed_seers = []
        for event in events:
            if event.get('action') == 'CLAIM' and event.get('properties', {}).get('role') == 'SEER':
                claimed_seers.append(event.get('source_name'))
        
        if claimed_seers:
            target = claimed_seers[0]
            player_state.objective = f"战术目标：守护预言家 {target}。他是全村的希望。"
        else:
            player_state.objective = "战术目标：守护自己或者看起来最容易被刀的好人（如发言优秀的村民）。"

