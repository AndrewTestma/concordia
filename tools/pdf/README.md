好的，这是将 **PDF剧本** 清洗为 **结构化文本（Markdown/CSV）** 并存入 Dify 知识库的详细落地执行方案。

这个方案的目标是：**无需人工逐字阅读剧本，利用 LLM 自动将长篇 PDF 拆解为带权限、带逻辑的原子化知识块。**

---

## 安装说明

### 快速安装

1. **安装Python依赖**
```bash
# 使用清华源加速安装
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

2. **OCR支持（可选）**
如果需要处理扫描版PDF，请额外安装：

**Windows系统：**
- Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki 下载并安装
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases/ 下载并解压，将poppler/bin添加到系统PATH
- 中文语言包：安装tesseract时勾选中文语言包

**Ubuntu系统：**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim poppler-utils
```

3. **环境变量配置**
```bash
# 设置DMXAPI相关环境变量
export DMXAPI_KEY="your_api_key_here"
export DMXAPI_BASE_URL="https://www.dmxapi.com"
```

### 依赖说明
- **PyPDF2**: 处理文本型PDF文件
- **pdf2image + pytesseract**: 处理扫描版PDF（OCR）
- **openai**: 调用LLM API进行文本处理
- **concordia**: 项目内部模块，需要正确配置项目路径

---

### 第一阶段：准备工作 (工具链)

你需要以下工具：
1.  **PDF 解析工具**：能将 PDF 转为纯文本（推荐 Python 的 `PyPDF2` 或直接用 Dify/GPT-4o 的文件读取能力）。
2.  **LLM 处理器**：GPT-4o (推荐，处理长文本逻辑最好) 或 Claude 3.5 Sonnet。
3.  **目标格式**：我们将采用 **Markdown 增强版** 格式，因为它比 CSV 更能容纳大段描述，且方便 Dify 进行自定义分段。

---

### 第二阶段：清洗 Prompt 设计 (核心)

我们需要编写一个强大的 Prompt，让 LLM 扮演“剧本拆解师”。

**Prompt 模板：**

```text
# Role
你是一个专业的剧本杀数据架构师。你的任务是将一份非结构化的【人物剧本 PDF】，重构为适合 AI 检索的【结构化知识库文档】。

# Input Data
剧本所属角色：{{role_name}} (例如：任志遥)
剧本内容：
"""
{{pdf_content}}
"""

# Task
请深入理解剧本内容，将其拆解为多个独立的“知识块”。
每个知识块必须包含明确的【权限标记】、【时间】、【地点】和【事实描述】。

# Output Format (Strict Markdown)
请严格遵守以下输出格式。不要输出任何多余的开场白或结束语。
使用 "---" 作为知识块的分隔符。

---
ID: {{role_name}}_Timeline_001
权限: {{role_name}}
标签: 时间线, 案发当晚
内容:
【时间】19:30
【地点】向阳村村口
【事件】我（任志遥）到达村口，遇到了姜宇桓。我们简单寒暄了几句，我注意到他神色慌张。
---
ID: {{role_name}}_Secret_001
权限: {{role_name}}
标签: 秘密, 动机, 过去
内容:
【核心秘密】我其实是当年的幸存者。我回来的真实目的是为了复仇，而不是查案。这件事绝对不能让姜宇桓知道。
---
ID: {{role_name}}_Item_001
权限: {{role_name}}
标签: 物品, 线索
内容:
【物品】生锈的钥匙
【来源】我在老宅的门框上摸到的。
【用途】这把钥匙能打开后山的地下室。目前只有我知道这把钥匙在我身上。
---
ID: {{role_name}}_Public_001
权限: 公共
标签: 背景知识, 传说
内容:
【传说】向阳村流传着关于“山神”的传说。每逢雨夜，山上就会传来哭声。这是所有村民都知道的事情。
---

# Rules
1. **去代词化**：将文中的“我”统一替换为“我（{{role_name}}）”，将“他/她”替换为具体的人名。
2. **权限判断**：
   - 如果是只有该角色知道的心理活动、秘密行动、私有物品 -> 标记为 `{{role_name}}`。
   - 如果是公开的传说、天气、大家都知道的案情 -> 标记为 `公共`。
3. **原子化**：一个知识块只讲一件事。不要把整个晚上的行程写在一个块里，要按时间点拆分。
4. **完整性**：每个块必须包含“权限”字段，防止切片后权限丢失。
```

---

### 第三阶段：执行与自动化 (Python 脚本)

你可以写一个简单的 Python 脚本来批量处理所有角色的 PDF。

```python
import os
from openai import OpenAI  # 假设使用 OpenAI 接口

client = OpenAI(api_key="sk-...")

def clean_pdf_script(pdf_text, role_name):
    """
    调用 LLM 清洗剧本
    """
    prompt = f"""
    (粘贴上面的 Prompt 模板)
    剧本所属角色：{role_name}
    剧本内容：
    {pdf_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一个严谨的数据处理助手。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1  # 低温度保证格式稳定
    )

    return response.choices[0].message.content

# 示例调用
# 1. 读取 PDF (这里简化为读取文本文件，实际可用 PyPDF2)
with open("任志遥剧本.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

# 2. 清洗
cleaned_markdown = clean_pdf_script(raw_text, "任志遥")

# 3. 保存为中间文件
with open("任志遥_cleaned.md", "w", encoding="utf-8") as f:
    f.write(cleaned_markdown)

print("清洗完成！请检查生成的 Markdown 文件。")
```

---

### 第四阶段：Dify 入库配置 (关键步骤)

现在你手里有了一个格式非常完美的 `任志遥_cleaned.md` 文件。接下来在 Dify 里的操作至关重要。

1.  **创建/打开知识库**。
2.  **上传文本文件**：选择刚刚生成的 `任志遥_cleaned.md`。
3.  **分段设置 (Segmentation Settings)**：
    *   **模式**：选择 **“自定义 (Custom)”**。
    *   **分隔符 (Separator)**：输入 `---` (三个短横线)。
    *   **最大字符数**：设置大一点，比如 1000 或 2000（因为我们已经人工分好块了，通常一个块不会超标）。
4.  **点击“保存并处理”**。

**原理验证：**
Dify 会根据 `---` 符号，精准地将每一个知识块切成一段。
*   **切片 1**：
    ```text
    ID: Ren_Timeline_001
    权限: 任志遥
    内容: ...
    ```
*   **切片 2**：
    ```text
    ID: Ren_Secret_001
    权限: 任志遥
    内容: ...
    ```

**结果：** 每一个切片的**开头第一行**绝对是权限标记。这完美解决了直接切片导致的“权限断头”问题。

---

### 第五阶段：Workflow 检索验证

在你的 Dify Workflow (Agent) 中，LLM 裁判的逻辑现在变得非常简单且健壮：

**LLM 裁判 Prompt：**
```text
你是一个权限过滤器。

【输入】
用户角色: {{current_role}} (例如: 姜宇桓)
检索到的内容块:
"""
{{context}}
"""

【规则】
1. 检查内容块开头的 "权限: xxx" 字段。
2. 如果 "权限" == "公共"，允许输出。
3. 如果 "权限" == "{{current_role}}"，允许输出。
4. 否则，禁止输出该块内容。

请输出过滤后的结果。
```

### 为什么这个方案是最佳实践？

1.  **自动化**：除了写脚本那一下，后续来 100 个剧本也是一键跑。
2.  **零风险**：通过 `---` 强制分段，物理上保证了权限标记和内容永远绑定在一起。
3.  **高精度**：Prompt 里的“去代词化”规则（把“我”变成“任志遥”），解决了 RAG 检索中经常出现的指代不清问题。
4.  **易维护**：如果剧本改了，只需要重跑一遍清洗脚本，不需要人工去 Excel 表里一行行改。
