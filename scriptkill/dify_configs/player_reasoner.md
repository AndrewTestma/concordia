# Player Reasoner - Dify App 配置指南

此文档描述了如何搭建 "Player Reasoner" (玩家推理器) 的 Dify Workflow。

## 1. 变量定义 (Start Node)

在工作流的 "Start" 节点定义以下变量：

| 变量名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `role_profile` | Paragraph | 角色的详细设定、性格、秘密和目标。 |
| `task` | Paragraph | 当前需要完成的任务或指令 (如：回应某人的质问)。 |
| `game_context` | Paragraph | 游戏当前的公开状态 (场景、近期对话历史)。 |
| `memory_summary` | Paragraph | 从关联记忆中检索到的相关私有记忆摘要。 |
| `knowledge_tag` | Text | (新增) 知识库检索标签，用于从知识库中召回该角色的专属背景故事 (如 Timeline)。 |

## 2. 节点编排 (Workflow Structure)

### 节点 A: Knowledge Retrieval (知识库检索)
*   **Query**: 提取`task`和`game_context`中的关键词，加上"时间线"、"背景"等通用词。
*   **Metadata Filter**:
    *   权限字段：`{{knowledge_tag}}` (角色专属) OR "公共" (公开信息)
    *   标签字段：根据任务类型选择"时间线"、"背景"、"计划"等
*   **过滤逻辑**: (权限={{knowledge_tag}} OR 权限=公共) AND 标签包含相关类型
*   **Top K**: 5-10条，给LLM足够的筛选空间

### 节点 B: LLM (推理核心)
*   **Model**: 推荐使用 GPT-4o 或 Claude 3.5 Sonnet。
*   **System Prompt**: 见下文。
*   **User Prompt**:
    ```
    {{role_profile}}

    === 你的专属背景知识 (来自知识库) ===
    {{#context#}} (来自节点 A 的输出)

    === 当前游戏环境 ===
    {{game_context}}

    === 你的近期记忆 ===
    {{memory_summary}}

    === 当前任务 ===
    {{task}}
    ```

### 节点 C: End (输出)
*   **Output Variable**: `result`
*   **Value**: 映射到 节点 B 的输出文本。

## 3. System Prompt (系统提示词)

```markdown
# Role
你现在正在参与一场沉浸式的剧本杀游戏。请完全沉浸在你的角色设定中，像一个真实的人一样思考和行动。

# Constraints
1. **绝对禁止跳戏**：不要提及“作为AI”、“剧本杀”、“扮演”等词汇。
2. **语气口吻**：严格模仿角色设定的说话风格（如方言、口头禅、语速）。
3. **信息隔离**：你只能利用【你的记忆】、【专属背景知识】和【当前游戏环境】中的信息。不要使用任何你角色不应知道的外部知识。
4. **行动一致性**：你的言行必须符合你的【目标】。如果你的目标是隐瞒真相，请撒谎或转移话题。
5. **简洁性**：剧本杀对话通常是口语化的，避免长篇大论，除非角色设定如此。

# Instruction
根据传入的【当前任务】，结合你的【记忆】和【环境】，生成一段第一人称的回复或行动描述。
如果任务是思考，请输出内心独白（用括号包裹）。
如果任务是说话，请直接输出对话内容。
```
