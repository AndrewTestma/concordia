# 狼人杀
> 狼人杀（Werewolf/Mafia）是一种典型的社交演绎游戏（social deduction game），涉及隐藏角色（狼人/村民/神职）、阶段化回合（夜晚行动、白天讨论投票）、欺骗与推理。
## 狼语词典
- 查杀：预言家在查验出狼人后，号召大家投票处决该狼人。
- 挡刀：指为了保护某个身份，某位玩家装作有身份的样子，去骗取狼人信任，晚上给狼人杀，为好人做出贡献。
- 悍跳：指狼人跳好人身份。
- 对跳：两个或以上的角色均声称自己是某种身份由于身份只有一个，对跳的身份里面至多一个是真的。其余的都是假的。但是身份假的并不一定是坏人。
- 认出：声称自己是好人身份，但是不是非常重要的角色，如果不相信，可以把自己投出去也没问题。
- 金水：预言家在查验过后是好人的角色。
- 银水：特指被女巫救过的角色（不一定是好身份）。
- 聊爆：指话语中有明显漏洞，比如不经意间透露了村民不应该知道，但狼人知道的事。包括：存活狼人的人数、死者的死因等。
- 扛推：某位好人玩家在发言环节被人怀疑，被投票出局或将被票出局，为其他玩家扛住了被推出局的风险，简称扛推。
- 归票：通常指最后一个发言的人总结发言，号召大家集中将某人投票出局。
- 前置位：由于发言通常由被杀的人下一位开始轮流发言，所以相对来说先发言的位置称为前置位。
- 后置位：由于发言通常由被杀的人下一位开始轮流发言，所以相对来说后发言的位置称为后置位。
- 贴脸：指的是做出一些威胁、发毒誓，骂人等与游戏剧情无关的发言，以求博得他人的信任的行为，例如 “今天不票出我的查杀，我就死给你看”“昨晚出局的玩家是我最好的朋友，一定不会是我杀的”“我这把拿到狼人的话我就不是人”。由于这种行为带入了场外因素，所以可信度并不高。
- 抿：即猜测某人的身份。举例：如果某人的发言无理由地保另一个人，且十分肯定，狼队可能会猜测他是一名新手预言家，晚上杀死，这一行为可称为 “抿预言刀”。
- 单保：第一夜狼人不能首刀该玩家，刀了的话狼人交牌。
- 双保：第一夜狼人不能首刀该玩家，预言家也不能查验该玩家，刀了的话狼人交牌，查验了的话好人交牌。
- 天毒：第一夜女巫只能毒人，不能救人或自救。
- 天枪：第一夜猎人死亡后，第二天需要带人出局。
- 水包：自认平民的人给出的 2 个或者多个怀疑对象，希望在他们中通过发言来对比身份的好坏从而找出狼人。
- 反水：被预言家（无论真假）验（为好人方的身份）后，不认可对方的验人。如，玩家 A 跳预言家验 B 为好人，B 不认为 A 是预言家。
- 上警：参与警长竞选。
- 警上：参与警长竞选的玩家。
- 警下：不参与警长竞选的玩家。
- 撕警徽：警长出局后不选择其他玩家继承警长。
- 警徽流：警徽流就是警长或想要竞选警长的玩家交待前一天晚上验身份的结果。因为夜晚被杀是没遗言的，所以警长归票前，可以说我要查几号的身份，如果他是好人，警徽会给谁，如果他是坏人，警徽会给谁，这样可以让玩家万一死了也能给其他玩家留下线索。
- 分票：在某人遭到多人质疑的时候，提出另一个人的疑点，试图将投票分散。分票是狼人常用的技巧。
- 绑票：集体把票投给某人，试图靠人数优势将其投出局。
- 掰票：在某人被认为是狼人之后，为其辩解。
- 生推：预言家被杀后，场上村民比发言、无信息量无团队划分的游戏情况。
- 捞：A 玩家认为 B 玩家是好角色，所以要为 B 辩解，简称 “捞”。
## 6人规则
### 身份卡牌
- 预言家 ×1：每晚可以查验一名玩家身份，知道他是狼人还是好人。
- 猎人 ×1：猎人死亡时可开枪射杀一位玩家（俗称 “带走”）。但死于女巫毒药时，不能开枪。
- 村民 ×2：无特殊能力，主要靠推理分析找出狼人。
- 狼人 ×2：每晚可以杀死一名玩家。

### 胜利规则
- 狼人阵营
  胜利条件：杀死所有好人即可获胜。
- 好人阵营
  胜利条件：杀死所有狼人即可获胜。

## 总体设计思路

1. **游戏目标**：完整模拟一局真实 6 人狼人杀，代理能自然使用“狼语词典”术语，进行欺骗、推理、投票，直至一方获胜。
2. **核心原则**：

    - 严格阶段化：夜晚（狼人杀人 + 预言家验人）→ 白天（遗言 + 全员发言 + 投票）。
    - 信息不对称：狼人互相知晓队友；预言家获得验人结果；猎人死亡时可带人；其他人仅通过死亡公告和对话推理。
    - GM 口吻经典：所有阶段切换和行动指令使用标准主持人台词。
3. **简化重点**：无警徽、无平衡机制，纯靠身份能力 + 社交演绎。

## 框架结构（Concordia 组件映射）

1. **环境 (Environment)**

    - **全局共享观察**：

      - 当前阶段（夜晚/白天/遗言/发言/投票）。
      - 存活玩家列表。
      - 死亡公告（“昨夜平安夜”或“昨夜X号玩家死亡”）。
      - 发言顺序（从死亡玩家下一位开始）。
    - **私有观察**：

      - 狼人：知晓所有狼人队友名单。
      - 预言家：每晚收到验人结果（“X号玩家是狼人”或“X号玩家不是狼人”）。
      - 猎人：仅在死亡时收到“可选择带走一人”的私有指令。
2. **代理 (Actors) — 6 个**

    - 每个代理拥有：

      - 身份专属系统提示（包含角色能力 + “狼语词典”核心术语）。
      - 持久记忆（存储验人结果、死亡信息、对话历史）。
    - **典型系统提示示例**：

      - **狼人**：你是狼人，每晚与队友一起选择杀死一名玩家。白天伪装好人，可使用悍跳、分票、贴脸、掰票、聊爆等策略误导他人。
      - **预言家**：你是预言家，每晚可查验一名玩家身份。白天可选择报金水或查杀，可使用归票、水包、扛推等推动好人视角。
      - **猎人**：你是猎人，被刀或票出局时可开枪带走一人（被毒无效在本板无女巫）。白天低调发言，必要时挡刀。
      - **村民**：你是村民，无夜间能力，靠白天发言和投票找出狼人。可使用水包、归票、扛推、捞好人等。
3. **GameMaster (GM) — 主持人核心**

    - **职责**：

      - 发布经典指令，控制全场节奏。
      - 收集并执行夜间行动（狼人杀人、预言家验人）。
      - 处理猎人带人。
      - 管理白天发言顺序和投票。
      - 宣布死亡、平安夜、天亮。
      - 判断胜负并结束游戏。
    - **GM 经典台词列表（严格使用）** ：

      - 开局：“天黑请闭眼。”
      - 狼人阶段：“狼人请睁眼。” → “狼人请行动（选择要刀的玩家）。” → “狼人请闭眼。”
      - 预言家阶段：“预言家请睁眼。” → “预言家请验人（选择要查验的玩家）。” → （GM 私下告知结果） → “预言家请闭眼。”
      - 天亮：“天亮了，请睁眼。” → “昨夜平安夜。” 或 “昨夜X号玩家不幸出局，请留遗言。”
      - 遗言后：“请按顺序发言（从X号玩家开始）。”
      - 发言结束：“请投票（选择要票出的玩家）。”
      - 投票结果：“X号玩家票数最高，出局。”（若猎人触发带人，再私下处理）
4. **时钟 (Clock) 与游戏流程**

    - **完整一轮循环**：

      1. GM：天黑请闭眼。
      2. 夜晚阶段：

          - 狼人阶段（狼人集体选择一人刀）。
          - 预言家阶段（预言家选择一人验）。
      3. GM 计算死亡（若猎人被刀，记录需带人）。
      4. GM：天亮了，请睁眼 + 死亡公告。
      5. 若有人死亡 → 遗言（出局者最后发言）。
      6. 白天发言（按顺序轮流，每人一次）。
      7. 投票阶段（每人投一人，可弃票）。
      8. GM 公布票型 → 最高票出局（平票无人出局或自定义）。
      9. 若出局者是猎人 → GM 私下询问带人 → 执行带走。
      10. 检查胜负条件：

           - 狼人数量 ≥ 好人数量 → 狼人胜利。
           - 狼人数量 \= 0 → 好人胜利。
      11. 未结束 → 返回第1步。

## 狼语词典的应用方式

- **核心术语保留并强化**：查杀、金水、悍跳、对跳、贴脸、分票、掰票、水包、归票、扛推、挡刀、聊爆、捞、抿等。
- **去除无关术语**：所有与警徽流、单保、双保、天毒相关的术语不出现。
- **自然融入**：通过系统提示 + 记忆注入，让代理在白天发言中自发使用。例如：

  - 预言家：“我昨晚验了X号，是金水，今天查杀Y号。”
  - 狼人：“我悍跳预言家，验了Z号是金水，别票我。”
  - 村民：“这个发言有聊爆，我水包X和Y。”

 ## 代码架构设计（与 Concordia 对齐）

 - 环境与引擎
   - 使用 `concordia/environment/engines/sequential.py` 的顺序引擎驱动严格阶段化流程（夜晚→白天→投票）。
   - GM 通过组件链路控制阶段推进：`make_observation` → `next_acting` → `event_resolution` → `switch_act`，结合世界状态与时钟。
 - GM（GameMaster）
   - 采用 `concordia/prefabs/game_master/generic.py` 或 `situated_in_time_and_place.py` 组装标准 GM，固定台词由 GM 提示文档提供。
   - 关键职责：收集夜间行动、生成公共公告、管理发言顺序与投票、判定胜负。
 - 代理（Actors）
   - 采用 `concordia/prefabs/entity/fake_assistant_with_configurable_system_prompt.py` 或 `basic_with_plan.py` 创建 6 个实体代理。
   - 每个代理绑定专属系统提示与私有记忆，并共享公共记忆只读视图。
 - 记忆（Memory）
   - 使用 `concordia/components/agent/memory.py` 组件叠加 `concordia/associative_memory/basic_associative_memory.py` 作为底层库。
   - 公共与私有命名空间：`public:*`（公告、票型、阶段）与 `private:<player_id>:*`（验人结果、队友名单、发言笔记）。
 - 时钟（Clock）
   - 使用 `concordia/clocks/game_clock.py` 的固定/多区间时钟；GM 也可启用 `GenerativeClock`（`components/game_master/world_state.py`）作为叙事时钟。
 - 文档与提示（Prompt/Document）
   - 通过 `concordia/document/document.py` 与 `interactive_document.py` 构建 GM 台词与身份提示；嵌入“狼语词典”作为语言风格指令。

 ### 建议的示例目录结构

 - `examples/werewolf/config.py`：身份枚举、术语字典、阶段配置与胜利条件
 - `examples/werewolf/actors.py`：6 名代理的工厂方法与系统提示绑定
 - `examples/werewolf/gm.py`：GM 组装（组件字典、台词文档、世界状态/时钟）
 - `examples/werewolf/memory.py`：公共/私有记忆命名空间与初始化
 - `examples/werewolf/engine.py`：选择并配置顺序引擎
 - `examples/werewolf/run.py`：将 Actors + GM + Engine 组装成完整仿真并启动

 ### 伪代码示例（接口形状对齐）

 ```python
 # run.py（伪代码）
 from werewolf.actors import build_actors
 from werewolf.gm import build_gm
 from werewolf.engine import build_engine

 def run_game():
     gm = build_gm()
     actors = build_actors()
     engine = build_engine()
     # 顺序驱动直至胜负判定
     engine.run(gm=gm, actors=actors)

 if __name__ == "__main__":
     run_game()
 ```

 ```python
 # actors.py（伪代码）
 from concordia.prefabs.entity.fake_assistant_with_configurable_system_prompt import Entity
 from werewolf.memory import make_private_memory
 from werewolf.config import ROLE_PROMPTS

 def build_actors():
     actors = []
     for player_id, role in enumerate(["狼","狼","预言家","猎人","村民","村民"], start=1):
         system_prompt = ROLE_PROMPTS[role]
         memory = make_private_memory(player_id, role)
         actors.append(Entity(system_prompt=system_prompt, memory=memory))
     return actors
 ```

 ```python
 # gm.py（伪代码）
 from concordia.prefabs.game_master.generic import GameMaster
 from concordia.components.game_master import make_observation, next_acting, event_resolution, switch_act
 from concordia.components.game_master.world_state import GenerativeClock, WorldState
 from concordia.document.document import Document
 from werewolf.memory import public_memory
 from werewolf.config import GM_LINES

 def build_gm():
     gm_doc = Document("\n".join(GM_LINES))
     components = {
         "world_state": WorldState(clock=GenerativeClock()),
         "make_observation": make_observation.Component(public_memory),
         "next_acting": next_acting.Component(),
         "event_resolution": event_resolution.Component(),
         "switch_act": switch_act.Component(),
     }
     return GameMaster(document=gm_doc, components=components)
 ```

 ## 持久记忆与身份专属提示

 - 记忆命名空间设计
   - 公共：`public:phase`、`public:alive_list`、`public:death_announcement`、`public:speaking_order`、`public:vote_result`
   - 私有：`private:<id>:role`、`private:<id>:wolves`、`private:<id>:inspections`、`private:<id>:speech_notes`、`private:<id>:night_actions`
 - 初始化策略
   - 公共记忆初始化为当前阶段与存活列表；夜晚/白天切换由 GM 写入 `public:*`。
   - 狼人私有记忆立即写入队友名单；预言家每夜写入验人结果；猎人记录带人状态。
 - 实现要点
   - 使用 `Memory` 组件包裹 `BasicAssociativeMemory`，统一提供 `add()`、`query()`、`observe()` API。
   - GM 的 `make_observation` 将公共事件写入 `public:*`，并在需要时向特定代理下发私有观察（如验人结果）。

 ```python
 # memory.py（伪代码）
 from concordia.components.agent.memory import Memory
 from concordia.associative_memory.basic_associative_memory import BasicAssociativeMemory

 public_memory = Memory(store=BasicAssociativeMemory(namespace="public"))

 def make_private_memory(player_id: int, role: str):
     mem = Memory(store=BasicAssociativeMemory(namespace=f"private:{player_id}"))
     mem.add("role", role, visibility="private")
     if role == "狼":
         # 狼队知晓队友名单（示意）
         mem.add("wolves", ["1","2"], visibility="private")
     return mem
 ```

 - 身份专属系统提示（示例片段）
   - 狼人：强调“悍跳”“分票”“贴脸”“掰票”“聊爆”等策略；夜晚共识杀人，白天伪装。
   - 预言家：强调“查杀”“金水”“归票”“水包”“扛推”；夜晚验人并在白天策略性披露。
   - 猎人：强调被刀/被票可带走一人；白天以“挡刀”为主；被毒不触发（本板无女巫）。
   - 村民：强调“水包”“归票”“扛推”“捞好人”；依靠公共信息与对话推理。

 ```python
 # config.py（示例片段）
 ROLE_PROMPTS = {
   "狼": """你是狼人。夜晚与队友共识选择一名玩家击杀。
 白天伪装好人，优先使用：悍跳、分票、贴脸、掰票、聊爆。
 切勿泄露队友与狼数。""",
   "预言家": """你是预言家。每晚可查验一名玩家身份。
 白天合理报金水或查杀，并尝试归票、水包、扛推。""",
   "猎人": """你是猎人。若被刀或被票出局，可立即带走一人（被毒不触发）。
 发言偏保守，必要时为关键身份挡刀。""",
   "村民": """你是村民。无夜间能力。
 通过白天发言、归票与水包识别狼。""",
 }

 GM_LINES = [
   "天黑请闭眼。",
   "狼人请睁眼。狼人请行动（选择要刀的玩家）。狼人请闭眼。",
   "预言家请睁眼。预言家请验人（选择要查验的玩家）。预言家请闭眼。",
   "天亮了，请睁眼。",
   "昨夜平安夜。",  # 或 “昨夜X号玩家不幸出局，请留遗言。”
   "请按顺序发言（从X号玩家开始）。",
   "请投票（选择要票出的玩家）。",
   "X号玩家票数最高，出局。",
 ]
 ```

 ## 嵌入“狼语词典”

 - 注入位置
   - 身份提示：在 `ROLE_PROMPTS` 中明确术语与策略动作，作为风格与决策指令。
   - GM 提示：GM 台词固定，杜绝与本板不相关的术语（如警徽相关）。
   - 记忆种子：将“核心术语速查表”以公共记忆只读文档形式注入，便于代理在白天检索引用。
 - 术语选择与过滤
   - 保留：查杀、金水、悍跳、对跳、贴脸、分票、掰票、水包、归票、扛推、挡刀、聊爆、捞、抿。
   - 移除：警徽流、单保、双保、天毒等与本 6 人无警徽规则不相关术语。
 - 使用方式
   - 通过系统提示与公共记忆的“语言风格指南”，让代理在白天发言中自然出现术语，而非生硬拼接。
   - GM 在 `event_resolution` 中可对不合规术语进行软约束（例如建议改述），保持风格一致性。

 ```python
 # 将术语速查表注入公共记忆（伪代码）
 TERMS_CHEATSHEET = """
 查杀：预言家公布狼人并号召投票
 金水：被验为好人
 悍跳：狼人伪装好人身份
 对跳：多人声称同一身份，至多一真
 贴脸/聊爆/分票/掰票/归票/扛推/水包/捞/抿：按本板定义使用
 """
 public_memory.add("style:terms_cheatsheet", TERMS_CHEATSHEET, visibility="public")
 ```

 ### 落地执行顺序（建议）

 - 初始化公共/私有记忆与系统提示
 - GM 发布开局与夜晚阶段台词，收集行动并写入记忆
 - 天亮公告 → 遗言 → 白天发言（代理从记忆检索术语与信息）
 - 投票与出局结算（若猎人触发“带走”，GM 私下处理）
 - 胜负判定 → 未结束则回到“天黑请闭眼”
