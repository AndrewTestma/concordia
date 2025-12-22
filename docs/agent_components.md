## 使用示例

在创建自定义代理时，可以通过以下方式组合这些组件（来自model_debate_example.py的实际示例）：

```python
# 创建组件
memory = agent_components.memory.AssociativeMemory(memory_bank=memory_bank)
instructions_text = (
    f"您正在参加一场正式辩论。"
    f"主题：{debate_topic}。"
    f"您的既定立场为：{stance_text}。"
    f"目标：{goal}。风格：{traits}。"
    f"必须采用针锋相对的辩论风格："
    f"1) 直接针对对方上一轮的关键论点进行反驳，指出漏洞、矛盾或证据不足；"
    f"2) 给出清晰的主张（Claim）、证据（Evidence）与推理（Warrant），避免空泛表态；"
    f"3) 使用数据或权威来源（若无真实数据可概念性引用）来支撑论点；"
    f"4) 适当使用反问与比较来削弱对方论证；"
    f"5) 保持专业，但避免过度礼貌与妥协性措辞。"
    f"务必维护本方主张，不得为对方立场辩护；"
    f"若无上一轮发言（首轮），请进行开场陈述且不得出现‘您刚才’或类似引用措辞；"
    f"若历史发言总数少于2条（首轮与次轮），仍为开场阶段，不得引用对方；"
    f"若上一轮为对方发言，请先以“引用：\"...\"”准确摘取其关键一句，再逐条反驳。"
    f"输出格式严格为：{name} -- \"您的论点内容\""
)
instructions = agent_components.constant.Constant(
    state=instructions_text,
    pre_act_label=agent_components.instructions.DEFAULT_INSTRUCTIONS_PRE_ACT_LABEL,
)
observation = agent_components.observation.LastNObservations(history_length=100)
similar_memories = agent_components.all_similar_memories.AllSimilarMemories(
    model=MODEL_REGISTRY.get(model_key) if model_key and MODEL_REGISTRY.get(model_key) else model,
    memory_component_key=agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY,
    num_memories_to_retrieve=10,
)

components = {
    agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY: memory,
    "Instructions": instructions,
    agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY: observation,
    "SimilarMemories": similar_memories,
}

act_component = agent_components.concat_act_component.ConcatActComponent(
    model=MODEL_REGISTRY.get(model_key) if model_key and MODEL_REGISTRY.get(model_key) else model,
    component_order=[
        agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY,
        agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY,
        "SimilarMemories",
        "Instructions",
    ],
)
```

在这个实际示例中：

1. **Memory组件**：使用`AssociativeMemory`创建，连接到memory_bank
2. **Instructions组件**：使用`Constant`组件提供详细的辩论指导指令
3. **Observation组件**：使用`LastNObservations`跟踪最近100条观察记录
4. **SimilarMemories组件**：使用`AllSimilarMemories`检索相关记忆，支持模型切换
5. **组件组装**：所有组件通过字典组织，并通过`ConcatActComponent`按指定顺序组合

这种设计使得 Concordia 框架具有高度的灵活性和可扩展性，开发者可以根据需要创建自定义组件或组合现有组件来实现特定的代理行为。
