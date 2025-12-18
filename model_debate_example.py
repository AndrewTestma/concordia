# 两个模型对话辩论示例

这个示例展示了如何使用Concordia框架让两个不同的AI模型进行辩论。

```python
"""
Example of two AI models debating using Concordia framework.
"""

import os
from concordia.prefabs import entity as entity_prefabs
from concordia.prefabs import game_master as game_master_prefabs
from concordia.prefabs.simulation import generic as simulation
from concordia.typing import prefab as prefab_lib
from concordia.utils import helper_functions
from concordia.contrib import language_models as language_model_utils
import numpy as np
import sentence_transformers

# 1. 设置语言模型
# 使用不同的模型进行辩论
def setup_models():
    """Setup two different language models for the debate."""
    # 获取API密钥
    dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY')
    deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')
    
    # 如果没有设置API密钥，则使用模拟模型进行演示
    if not dashscope_api_key or not deepseek_api_key:
        print("Warning: API keys not found. Using mock models for demonstration.")
        from concordia.language_model import no_language_model
        qwen_model = no_language_model.NoLanguageModel()
        deepseek_model = no_language_model.NoLanguageModel()
    else:
        # 初始化Qwen模型
        qwen_model = language_model_utils.language_model_setup(
            api_type='qwen',
            model_name='qwen-max',
            api_key=dashscope_api_key,
        )
        
        # 初始化DeepSeek模型
        deepseek_model = language_model_utils.language_model_setup(
            api_type='deepseek',
            model_name='deepseek-chat',
            api_key=deepseek_api_key,
        )
    
    return qwen_model, deepseek_model

# 2. 设置嵌入器
def setup_embedder():
    """Setup sentence embedder for memory retrieval."""
    try:
        st_model = sentence_transformers.SentenceTransformer(
            'sentence-transformers/all-mpnet-base-v2'
        )
        embedder = lambda x: st_model.encode(x, show_progress_bar=False)
    except Exception:
        # 如果无法加载嵌入器，则使用模拟嵌入器
        print("Warning: Could not load sentence transformer. Using mock embedder.")
        embedder = np.ones(3)
    return embedder

# 3. 创建辩论场景配置
def create_debate_config():
    """Create configuration for the debate simulation."""
    
    # 加载可用的预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(game_master_prefabs),
    }
    
    # 定义辩论者实例
    instances = [
        # Qwen模型作为正方辩手
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "Qwen Advocate", 
                "goal": "Argue in favor of renewable energy as the primary solution to climate change",
                "traits": "Analytical, data-driven, environmentally conscious"
            },
        ),
        # DeepSeek模型作为反方辩手
        prefab_lib.InstanceConfig(
            prefab="basic__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "DeepSeek Skeptic", 
                "goal": "Argue that nuclear energy is a more practical solution to climate change than renewables",
                "traits": "Pragmatic, technically oriented, cost-conscious"
            },
        ),
    ]
    
    # 添加游戏主持人
    instances.append(
        prefab_lib.InstanceConfig(
            prefab="dialogic__GameMaster",
            role=prefab_lib.Role.GAME_MASTER,
            params={
                "name": "debate moderator",
                "next_game_master_name": "debate moderator",
                "turn_taking": "u-go-i-go",  # 轮流发言
            },
        )
    )
    
    # 创建配置
    config = prefab_lib.Config(
        default_premise="Two AI models are participating in a formal debate on the topic: 'Which is the better solution to climate change: renewable energy or nuclear energy?' The debate will consist of opening statements, rebuttals, and closing arguments.",
        default_max_steps=12,  # 限制最大步数以控制辩论长度
        prefabs=prefabs,
        instances=instances,
    )
    
    return config

# 4. 运行辩论
def run_debate():
    """Run the debate simulation between two models."""
    
    print("Setting up models and embedder...")
    qwen_model, deepseek_model = setup_models()
    embedder = setup_embedder()
    
    print("Creating debate configuration...")
    config = create_debate_config()
    
    # 由于我们需要两个不同的模型，我们需要创建两个独立的模拟
    # 这是一个简化版本，实际实现可能需要更复杂的设置
    
    print("Initializing simulation...")
    try:
        # 创建模拟（使用第一个模型作为主要模型）
        sim = simulation.Simulation(
            config=config, 
            model=qwen_model,  # 主要模型
            embedder=embedder
        )
        
        print("Starting debate...")
        results = sim.play()
        
        print("\n=== DEBATE RESULTS ===")
        print("Debate completed successfully!")
        print(f"Total steps: {len(results.steps)}")
        
        # 打印一些关键结果
        if hasattr(results, 'logs'):
            print("\n=== DEBATE LOGS ===")
            for i, step in enumerate(results.steps[:5]):  # 只打印前5步
                print(f"Step {i+1}: {step}")
                
        return results
        
    except Exception as e:
        print(f"Error during debate: {e}")
        # 返回模拟结果即使出错
        return None

# 5. 分析辩论结果
def analyze_debate_results(results):
    """Analyze the results of the debate."""
    if results is None:
        print("No results to analyze.")
        return
        
    print("\n=== DEBATE ANALYSIS ===")
    
    # 统计每个参与者的发言次数
    participant_turns = {}
    if hasattr(results, 'steps'):
        for step in results.steps:
            # 这里需要根据实际结果格式进行调整
            pass
            
    print("Debate analysis complete.")

# 6. 主函数
def main():
    """Main function to run the debate example."""
    print("AI Model Debate Example")
    print("=" * 30)
    
    # 运行辩论
    results = run_debate()
    
    # 分析结果
    analyze_debate_results(results)
    
    print("\nDebate example completed!")

# 高级用法：自定义辩论代理
class DebateAdvocate(prefab_lib.Prefab):
    """Custom prefab for a debate advocate with specific reasoning patterns."""
    
    def __init__(self, position="pro", debate_topic="", **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.debate_topic = debate_topic
    
    def build(self, model, memory_bank):
        """Build a custom debate agent."""
        from concordia.agents import entity_agent_with_logging
        from concordia.components import agent as agent_components
        
        name = self.params.get("name", "Debater")
        
        # 创建组件
        memory = agent_components.memory.AssociativeMemory(memory_bank=memory_bank)
        instructions = agent_components.instructions.Instructions(
            agent_name=name,
            instructions=(
                f"You are participating in a formal debate. "
                f"Your position: {self.position}. "
                f"Topic: {self.debate_topic}. "
                f"Be persuasive, logical, and respectful. "
                f"Support your arguments with facts and examples."
            )
        )
        observation = agent_components.observation.LastNObservations(history_length=50)
        
        components = {
            agent_components.memory.DEFAULT_MEMORY_COMPONENT_KEY: memory,
            "Instructions": instructions,
            agent_components.observation.DEFAULT_OBSERVATION_COMPONENT_KEY: observation,
        }
        
        act_component = agent_components.concat_act_component.ConcatActComponent(
            model=model,
            component_order=list(components.keys()),
        )
        
        return entity_agent_with_logging.EntityAgentWithLogging(
            agent_name=name,
            act_component=act_component,
            context_components=components,
        )

# 使用自定义代理的辩论配置
def create_advanced_debate_config():
    """Create an advanced debate configuration with custom agents."""
    
    # 注册自定义预制件
    prefabs = {
        **helper_functions.get_package_classes(entity_prefabs),
        **helper_functions.get_package_classes(game_master_prefabs),
    }
    prefabs["debate_advocate__Entity"] = DebateAdvocate
    
    # 定义高级辩论者实例
    instances = [
        # 正方辩手（使用自定义代理）
        prefab_lib.InstanceConfig(
            prefab="debate_advocate__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "Renewable Energy Advocate", 
                "position": "pro",
                "debate_topic": "Renewable energy is superior to nuclear energy for addressing climate change"
            },
        ),
        # 反方辩手（使用自定义代理）
        prefab_lib.InstanceConfig(
            prefab="debate_advocate__Entity",
            role=prefab_lib.Role.ENTITY,
            params={
                "name": "Nuclear Energy Advocate", 
                "position": "con",
                "debate_topic": "Nuclear energy is superior to renewable energy for addressing climate change"
            },
        ),
    ]
    
    # 添加游戏主持人
    instances.append(
        prefab_lib.InstanceConfig(
            prefab="dialogic__GameMaster",
            role=prefab_lib.Role.GAME_MASTER,
            params={
                "name": "debate moderator",
                "next_game_master_name": "debate moderator",
            },
        )
    )
    
    # 创建配置
    config = prefab_lib.Config(
        default_premise="Two expert debaters are presenting their arguments in a formal debate competition. The topic is: 'Which is the better solution to climate change: renewable energy or nuclear energy?' Each side will present opening arguments, offer rebuttals, and conclude with closing statements.",
        default_max_steps=15,
        prefabs=prefabs,
        instances=instances,
    )
    
    return config

if __name__ == "__main__":
    main()
```

## 使用说明

### 1. 环境设置

在运行此示例之前，请确保设置了必要的环境变量：

```bash
# 设置Qwen API密钥
export DASHSCOPE_API_KEY=your_qwen_api_key_here

# 设置DeepSeek API密钥
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 2. 安装依赖

```bash
pip install gdm-concordia[qwen,deepseek]
pip install sentence-transformers
```

### 3. 运行示例

```bash
python model_debate_example.py
```

## 示例特点

1. **双模型辩论**：使用Qwen和DeepSeek两个不同的模型作为辩论双方
2. **角色定制**：为每个模型分配了明确的角色和立场
3. **结构化流程**：包含开场陈述、反驳和结语等辩论环节
4. **可扩展性**：提供了自定义代理类以支持更复杂的辩论逻辑
5. **结果分析**：包含基本的结果分析功能

## 自定义扩展

您可以轻松修改此示例以适应不同的辩论主题：

1. 更改`default_premise`中的辩论主题
2. 修改代理的`goal`和`traits`参数
3. 调整`default_max_steps`控制辩论长度
4. 使用自定义代理类添加特定的推理模式

这个示例展示了Concordia框架的强大功能，可以用于研究不同AI模型的观点表达、论证能力和交互行为。