# AI模型对话达示例

这个项目展示了如何使用Concordia框架让两个不同的AI模型进行对话辩论。

## 文件说明

1. `model_debate_example.py` - 完整的辩论示例，包含自定义代理类
2. `simple_model_debate.py` - 简化版的对话达示例，更容易理解和运行

## 快速开始

### 使用模拟模型（无需API密钥）

直接运行任一示例文件即可：

```bash
python simple_model_debate.py
```

这将使用Concordia的模拟模型运行，无需任何API密钥。

### 使用真实模型

如果您想使用真实的Qwen和DeepSeek模型，请按以下步骤操作：

1. **获取API密钥**：
   - 从阿里云获取DashScope API密钥用于Qwen模型
   - 从DeepSeek获取API密钥用于DeepSeek模型

2. **设置环境变量**：
   ```bash
   export DASHSCOPE_API_KEY=your_actual_qwen_api_key
   export DEEPSEEK_API_KEY=your_actual_deepseek_api_key
   ```

3. **安装依赖**：
   ```bash
   pip install gdm-concordia[qwen,deepseek] sentence-transformers
   ```

4. **取消注释代码中的真实模型设置部分**

## 自定义辩论主题

您可以轻松修改辩论主题：

1. 更改`default_premise`中的场景描述
2. 修改代理的`goal`和`traits`参数
3. 调整`default_max_steps`控制对话长度

## 示例特点

1. **双模型对话**：展示两个不同模型的交互
2. **结构化流程**：包含轮流发言的对话机制
3. **可扩展性**：提供自定义代理类以支持更复杂的逻辑
4. **结果分析**：包含基本的结果分析功能

## 学习资源

- [Concordia官方文档](https://github.com/google-deepmind/concordia)
- [Concordia Cheat Sheet](examples/concordia_cheat_sheet.md)
- [Concordia技术报告](https://arxiv.org/abs/2312.03664)

## 许可证

该项目遵循Concordia的许可证条款。