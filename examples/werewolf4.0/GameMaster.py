import time
import logging
from typing import List, Dict, Any, Optional
import os
import random

from Neo4jAdapter import Neo4jAdapter
from TheHand import TheHand
from TheEye import TheEye
from LogicEngine import LogicEngine
from PlayerState import PlayerState
from DifyClient import DifyClient
from StrategyModule import StrategyModule

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GameMaster")

class GameMaster:
    """
    GameMaster (游戏管理员) 控制器

    职责:
    1. 游戏流程控制: 管理游戏的各个阶段 (初始化 -> 夜晚 -> 白天 -> 投票 -> 结算)。
    2. 状态协调: 协调 Neo4j (客观事实)、PlayerState (主观状态) 和 Dify (决策大脑)。
    3. 玩家代理: 轮询每个玩家 Agent，调用 Dify 获取行动，并执行相应操作。
    """

    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, dify_api_key, players_config):
        """
        初始化游戏管理员。

        :param neo4j_uri: Neo4j 数据库 URI。
        :param neo4j_user: Neo4j 用户名。
        :param neo4j_password: Neo4j 密码。
        :param dify_api_key: Dify API 密钥。
        :param players_config: 玩家配置列表，例如 [{'id': 'P1', 'name': 'Alice', 'role': 'VILLAGER'}, ...]。
        """
        # 1. 初始化各组件
        self.adapter = Neo4jAdapter(neo4j_uri, neo4j_user, neo4j_password)
        self.hand = TheHand(self.adapter)
        self.eye = TheEye(self.adapter)
        self.logic_engine = LogicEngine()
        self.dify_client = DifyClient(api_key=dify_api_key)
        self.strategy_module = StrategyModule()

        # 2. 初始化玩家状态
        self.players_config = players_config
        self.player_states: Dict[str, PlayerState] = {}
        for p_conf in players_config:
            p_state = PlayerState(p_conf['id'], p_conf['name'], p_conf['role'])
            # 初始化对其他人的怀疑度
            p_state.init_suspicion([p['id'] for p in players_config])
            self.player_states[p_conf['id']] = p_state

        # 3. 游戏元数据
        self.round = 1
        self.phase = "SETUP" # SETUP, NIGHT, DAY, VOTE, END
        self.winner = None

    def setup_game(self):
        """
        游戏初始化阶段：清理数据库，创建玩家节点。
        """
        logger.info("【游戏初始化】正在初始化游戏数据...")
        self.adapter.clear_graph()
        self.adapter.init_game_data(self.players_config)
        logger.info("【游戏初始化】游戏初始化完成。")

    def run_game_loop(self, max_rounds=10):
        """
        运行主游戏循环。

        :param max_rounds: 最大回合数，防止死循环。
        """
        self.setup_game()

        while self.round <= max_rounds and self.winner is None:
            logger.info(f"【游戏开始】=== 第 {self.round} 回合开始 ===")

            # --- 1. 夜晚阶段 ---
            self.phase = "NIGHT"
            self.run_night_phase()

            # --- 2. 白天阶段 ---
            self.phase = "DAY"
            self.run_day_phase()

            # --- 3. 投票阶段 ---
            self.phase = "VOTE"
            voted_out_player = self.run_vote_phase()

            # --- 4. 结算与检查 ---
            self.check_game_over(voted_out_player)
            if self.winner:
                break

            self.round += 1

        logger.info(f"【游戏结束】游戏结束! 获胜者: {self.winner}")

    def run_night_phase(self):
        """
        执行夜晚阶段逻辑：狼人杀人，预言家验人，女巫救人等。
        """
        logger.info(f"【夜晚阶段】--- 第 {self.round} 夜 ---")

        # 遍历所有活着的玩家，询问是否有夜间行动
        # 注意：实际游戏中通常有行动顺序（如：守卫 -> 狼人 -> 女巫 -> 预言家）
        # 这里为了简化，我们假设 Dify 会根据 Role 和 Phase 决定是否行动

        # 1. 狼人行动 (假设所有狼人通过 Dify 协商，或者简化为第一个狼人决策)
        wolves = [p for p in self.players_config if p['role'] == 'WEREWOLF' and self.is_alive(p['id'])]
        if wolves:
            # 让第一个活着的狼人做决策 (简化版)
            actor = wolves[0]
            self.process_player_turn(actor['id'], step_name="NIGHT_KILL")

        # 2. 预言家行动
        seers = [p for p in self.players_config if p['role'] == 'SEER' and self.is_alive(p['id'])]
        if seers:
            actor = seers[0]
            self.process_player_turn(actor['id'], step_name="NIGHT_CHECK")

        # 3. 女巫等其他角色 (暂略)

    def run_day_phase(self):
        """
        执行白天阶段逻辑：公布死讯，轮流发言。
        """
        logger.info(f"【白天阶段】--- 第 {self.round} 天 ---")

        # 1. 公布昨晚死讯 (这里需要从图数据库读取昨晚的 KILL 事件)
        # 简化：假设昨晚一定有人死，或者需要实现结算逻辑。
        # 这里暂时跳过复杂的结算，直接进入发言。

        # 2. 轮流发言
        alive_players = [p for p in self.players_config if self.is_alive(p['id'])]

        # 简单的顺序发言
        for player in alive_players:
            self.process_player_turn(player['id'], step_name="DAY_SPEECH")

    def run_vote_phase(self):
        """
        执行投票阶段逻辑：每人投一票。
        :return: 被投出的玩家 ID (如果平票或无人出局则为 None)
        """
        logger.info(f"【投票阶段】--- 第 {self.round} 轮投票 ---")

        alive_players = [p for p in self.players_config if self.is_alive(p['id'])]
        votes = {} # target_id -> count

        for player in alive_players:
            # 调用 Dify 获取投票决策
            action_result = self.process_player_turn(player['id'], step_name="VOTE")

            # 解析投票结果 (假设 Dify 返回的 action_intent 中包含 target)
            # 注意：process_player_turn 内部已经调用 TheHand 记录了 VOTE 事件
            # 这里我们需要统计票数。为了简单，我们从图数据库查询本轮投票结果
            pass

        # 统计本轮投票
        # 查询 Cypher: MATCH (s)-[r:VOTE]->(t) WHERE r.round = $round RETURN t.id, count(s)
        query = """
        MATCH (s)-[r:VOTE]->(t)
        WHERE r.round = $round
        RETURN t.id as target_id, count(s) as votes
        ORDER BY votes DESC
        """
        results = self.adapter.run_query(query, {'round': self.round})

        if not results:
            logger.info("【投票结果】本轮无人投票。")
            return None

        top_vote = results[0]
        logger.info(f"【投票结果】投票结果: {results}")

        # 简单的票数判定：最高票出局 (需处理平票，这里暂略)
        eliminated_id = top_vote['target_id']
        logger.info(f"【投票结果】玩家 {eliminated_id} 被投票出局。")

        # 标记死亡
        self.kill_player(eliminated_id, reason="VOTE_OUT")
        return eliminated_id

    def process_player_turn(self, player_id: str, step_name: str):
        """
        处理单个玩家的轮次：组装 Payload -> 调用 Dify -> 解析结果 -> 执行动作。

        :param player_id: 玩家 ID
        :param step_name: 当前步骤名称 (如 DAY_SPEECH, NIGHT_KILL)
        :return: Dify 的原始输出或解析后的动作
        """
        player_state = self.player_states[player_id]
        player_name = player_state.player_name

        # 显示当前步骤和说话者
        step_display = self._get_step_display_name(step_name)
        logger.info(f"【游戏进程】第 {self.round} 回合 - {player_name} ({player_id}) 正在执行: {step_display}")

        # 0. 运行策略模块 (如果是夜间行动)
        if self.phase == "NIGHT":
            # 获取玩家视角
            visible_events = self.eye.get_player_view(player_id, player_state.role)
            # 更新战术目标
            self.strategy_module.run_night_strategy(player_state, visible_events)
        elif self.phase == "DAY" and step_name == "DAY_SPEECH":
             # 获取玩家视角
            visible_events = self.eye.get_player_view(player_id, player_state.role)
            # 更新战术目标 (发言策略)
            self.strategy_module.run_day_strategy(player_state, visible_events)

        # 1. 组装 Payload
        game_meta = {
            "game_id": "G_Test",
            "round": self.round,
            "phase": self.phase,
            "step_name": step_name
        }

        payload = self.dify_client.assemble_payload(
            game_meta=game_meta,
            player_state=player_state,
            the_eye=self.eye,
            logic_engine=self.logic_engine
        )

        # 2. 调用 Dify (Brain)
        # 输入变量名需与 Dify Workflow 定义一致，假设为 'context_payload'
        dify_inputs = {
            "query": json.dumps(payload, ensure_ascii=False), # 有些 workflow 用 query 接收
            "context_payload": json.dumps(payload, ensure_ascii=False)
        }

        # 为了演示，如果 Dify 调用失败或未配置，我们可以使用 mock 逻辑
        if self.dify_client.api_key == "MOCK_KEY":
            logger.warning("使用 Mock 逻辑生成行动 (未连接真实 Dify)")
            action_data = self._mock_dify_response(player_id, step_name)
        else:
            player_name = player_state.player_name
            dify_output = self.dify_client.run_workflow(dify_inputs, user_id=player_id, player_name=player_name, step_name=step_name)
            # 假设 Dify 返回的 text 包含 JSON 格式的行动指令
            # 或者 Dify 直接返回结构化 JSON
            # 这里假设输出在 'text' 字段中，并且是 JSON 字符串
            try:
                raw_text = dify_output.get('text', '{}')
                # 清理可能的 markdown 标记和多余文本
                raw_text = raw_text.replace('```json', '').replace('```', '').strip()

                # 尝试查找 JSON 部分（可能在文本中间）
                import re
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    action_data = json.loads(json_str)
                else:
                    action_data = json.loads(raw_text)

                # 检查 action_data 是否包含 action 字段，如果是，则映射到 action_intent
                if 'action' in action_data:
                    # 将 action 映射到 action_intent
                    action_map = {
                        'KILL': 'KILL',
                        'CHECK': 'CHECK',
                        'SPEAK': 'SPEAK',
                        'VOTE': 'VOTE',
                        'PASS': 'PASS'
                    }
                    action_type = action_data['action']
                    if action_type in action_map:
                        action_data['action_intent'] = action_map[action_type]
                        if 'target' in action_data:
                            action_data['target'] = action_data['target']
                        if 'content' in action_data:
                            action_data['content'] = action_data['content']
                # 如果有 speech 字段，映射到 SPEAK 动作
                elif 'speech' in action_data:
                    action_data['action_intent'] = 'SPEAK'
                    action_data['content'] = action_data['speech']
                    if 'vote_target' in action_data:
                        action_data['target'] = action_data['vote_target']
            except json.JSONDecodeError as e:
                logger.error(f"Dify 响应不是有效的 JSON 格式: {e}")
                logger.error(f"原始响应: {raw_text}")
                action_data = {}
            except Exception as e:
                logger.error(f"无法解析 Dify 响应: {e}")
                logger.error(f"原始响应: {raw_text}")
                action_data = {}

        # 3. 执行动作 (The Hand)
        self._execute_action(player_id, action_data, step_name)

        return action_data

    def _get_step_display_name(self, step_name: str) -> str:
        """
        将步骤名称转换为中文显示名称
        """
        step_mapping = {
            "NIGHT_KILL": "夜间杀人",
            "NIGHT_CHECK": "夜间查验",
            "DAY_SPEECH": "白天发言",
            "VOTE": "投票"
        }
        return step_mapping.get(step_name, step_name)

    def _execute_action(self, player_id: str, action_data: Dict[str, Any], step_name: str):
        """
        根据 Dify 返回的意图执行具体动作并写入图数据库。
        """
        intent = action_data.get('action_intent', 'PASS')
        target = action_data.get('target', None)
        content = action_data.get('content', '')

        if intent == 'PASS':
            logger.info(f"【行动执行】玩家 {player_id} 选择跳过/无行动。")
            return

        if step_name == "NIGHT_KILL" and intent == "KILL":
            logger.info(f"【行动执行】玩家 {player_id} 执行夜间杀人，目标: {target}")
            self.hand.log_kill(player_id, target, self.round)
            # 在逻辑层暂时不直接标记死亡，等到天亮结算。
            # 但为了简化，我们这里直接记录 KILL 事件。

        elif step_name == "NIGHT_CHECK" and intent == "CHECK":
            # 预言家查验，需要获取目标真实身份
            real_role = self._get_real_role(target)
            result = "WEREWOLF" if real_role == "WEREWOLF" else "GOOD"
            logger.info(f"【行动执行】玩家 {player_id} 执行夜间查验，目标: {target}，结果: {result}")
            self.hand.log_check(player_id, target, result, self.round)

        elif step_name == "DAY_SPEECH" and intent == "SPEAK":
            logger.info(f"【行动执行】玩家 {player_id} 发言: {content}")
            self.hand.log_speech(player_id, content, "ALL", self.round)

        elif step_name == "VOTE" and intent == "VOTE":
            logger.info(f"【行动执行】玩家 {player_id} 投票，目标: {target}")
            self.hand.log_vote(player_id, target, self.round)

        else:
            logger.warning(f"【行动执行】未知的动作意图: {intent} (Step: {step_name})")

    def _get_real_role(self, player_id: str) -> str:
        """获取玩家真实角色 (Helper)"""
        for p in self.players_config:
            if p['id'] == player_id:
                return p['role']
        return "UNKNOWN"

    def is_alive(self, player_id: str) -> bool:
        """检查玩家是否存活 (需查询 DB 或本地缓存)"""
        # 简单起见，查本地缓存状态 (需在 kill_player 时更新)
        # 或者查 Neo4j: MATCH (p:Player {id: $id}) RETURN p.status
        # 这里为了性能和简化，我们维护一个 set 或 check status
        # 暂时默认都活着，除非被标记
        # 更好的做法是在 self.player_states 中或 players_config 中维护 status
        # 让我们去 Neo4j 查一下最准
        query = "MATCH (p:Player {id: $id}) RETURN p.status as status"
        res = self.adapter.run_query(query, {'id': player_id})
        if res and res[0]['status'] == 'DEAD':
            return False
        return True

    def kill_player(self, player_id: str, reason: str):
        """处决玩家"""
        query = "MATCH (p:Player {id: $id}) SET p.status = 'DEAD'"
        self.adapter.run_query(query, {'id': player_id})
        self.hand.log_public_event("GM", "ANNOUNCE_DEATH", player_id, {"reason": reason, "round": self.round})
        logger.info(f"【玩家死亡】玩家 {player_id} 已确认死亡，原因: {reason}。")

    def check_game_over(self, eliminated_player_id):
        """检查游戏是否结束"""
        # 简单逻辑：狼人全死 -> 好人赢；狼人数量 >= 好人数量 -> 狼人赢

        wolves = 0
        good = 0

        for p in self.players_config:
            if self.is_alive(p['id']):
                if p['role'] == 'WEREWOLF':
                    wolves += 1
                else:
                    good += 1

        logger.info(f"【游戏状态】当前存活: 狼人 {wolves}, 好人 {good}")

        if wolves == 0:
            self.winner = "VILLAGERS"
            logger.info(f"【游戏结束】好人阵营获胜！")
        elif wolves >= good:
            self.winner = "WEREWOLVES"
            logger.info(f"【游戏结束】狼人阵营获胜！")

    def _mock_dify_response(self, player_id: str, step_name: str) -> Dict[str, Any]:
        """
        Mock 响应生成器，用于测试流程。
        """
        import random
        other_players = [p['id'] for p in self.players_config if p['id'] != player_id]
        target = random.choice(other_players) if other_players else "None"

        if step_name == "NIGHT_KILL":
            return {"action_intent": "KILL", "target": target}
        elif step_name == "NIGHT_CHECK":
            return {"action_intent": "CHECK", "target": target}
        elif step_name == "DAY_SPEECH":
            return {"action_intent": "SPEAK", "content": f"我是 {player_id}, 我觉得 {target} 是狼！", "target": "ALL"}
        elif step_name == "VOTE":
            return {"action_intent": "VOTE", "target": target}

        return {"action_intent": "PASS"}

    def close(self):
        self.adapter.close()

import json
