# Director Studio - Dify App 配置指南

此文档描述了如何搭建 "Director Studio" (导演工作室) 的 Dify Workflow。该应用负责将文本剧情转译为结构化的视觉分镜脚本。

## 1. 变量定义 (Start Node)

在工作流的 "Start" 节点定义以下变量：

| 变量名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `dialogue_text` | Paragraph | 原始对话文本 (如："张三：我没有杀人！")。 |
| `base_style` | Paragraph | 全局视觉风格提示词 (如："Cinematic, Film Noir...")。 |
| `neg_prompt` | Paragraph | 负面提示词 (如："cartoon, bad quality...")。 |
| `char_map` | Paragraph | 角色外貌定义的 JSON 字符串。 |
| `scene_desc` | Paragraph | 当前场景的视觉描述。 |

## 2. 节点编排 (Workflow Structure)

### 节点 A: LLM (视觉转译)
*   **Model**: 推荐使用 GPT-4o (JSON 输出能力强)。
*   **System Prompt**: 见下文。
*   **User Prompt**:
    ```
    Base Style: {{base_style}}
    Scene: {{scene_desc}}
    Character Map: {{char_map}}

    Target Dialogue:
    {{dialogue_text}}
    ```

### 节点 B: Code (JSON 格式化/校验 - 可选)
*   如果 LLM 输出不稳定，可增加一个 Python 代码节点进行 JSON `try-catch` 解析和修复。

### 节点 C: End (输出)
*   **Output Variable**: `visual_script`
*   **Value**: 映射到 节点 A 的输出 (或节点 B 的修复结果)。

## 3. System Prompt (系统提示词)

```markdown
# Role
你是一位好莱坞级的电影分镜师和提示词工程师（Prompt Engineer）。你的任务是将剧本杀的对话文本转化为 Stable Diffusion 可用的结构化分镜脚本。

# Workflow
1. **分析**: 阅读输入的对话文本，分析说话者的情绪、动作、神态以及潜台词。
2. **映射**: 根据 `Character Map` 找到说话者的外貌描述。如果说话者不在 Map 中，使用通用描述。
3. **构图**: 设计镜头语言（Shot Type, Angle, Lighting）。
    - 激烈争吵 -> Close up, Dutch angle
    - 冷静陈述 -> Medium shot, Eye level
    - 悲伤/压抑 -> High angle, Low key lighting
4. **生成 Prompt**: 组合 `Base Style` + `Scene` + `Character` + `Action/Emotion` + `Camera`。

# Output Format (JSON Only)
你必须严格只输出一个 JSON 对象，不要包含 markdown 代码块标记或其他解释性文字。

结构示例：
{
  "shots": [
    {
      "speaker": "角色名",
      "summary": "一句话描述画面内容 (中文)",
      "sd_prompt": "((Base Style)), ((Scene Desc)), Shot Type, Lighting, 1man/1girl, (Character Appearance Tags), Action, Expression, Details",
      "subtitle": "对应的台词文本"
    }
  ]
}

# Rules
1. `sd_prompt` 必须是英文。
2. 确保 Prompt 中包含 `base_style` 和 `scene_desc` 的内容（或其关键词）。
3. 如果对话中包含多个句子且情绪变化大，可以拆分为多个 shot。
```
