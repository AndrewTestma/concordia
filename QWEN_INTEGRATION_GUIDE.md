# 使用Qwen模型与Concordia

要在Concordia中使用Qwen模型，您可以按照以下步骤操作：

## 1. 安装依赖

首先确保安装了必要的依赖项：

```bash
pip install gdm-concordia[qwen]
```

## 2. 设置API密钥

您需要从阿里云获取DashScope API密钥，并将其设置为环境变量：

```bash
export DASHSCOPE_API_KEY=your_api_key_here
```

在Windows上：
```cmd
set DASHSCOPE_API_KEY=your_api_key_here
```

## 3. 在代码中使用Qwen模型

```python
import os
from concordia.contrib import language_models as language_model_utils

# 初始化Qwen模型
model = language_model_utils.language_model_setup(
    api_type='qwen',
    model_name='qwen3-max',  # 或其他Qwen模型名称
    api_key=os.getenv('DASHSCOPE_API_KEY'),
)

# 使用模型进行文本生成
response = model.sample_text("请写一首关于春天的诗。")
print(response)

# 在Concordia仿真中使用
# 当您运行Concordia示例时，可以指定:
# API_TYPE = 'qwen'
# MODEL_NAME = 'qwen3-max'
```

## 4. 在Jupyter Notebook中使用

如果您在Jupyter Notebook中使用Concordia，可以在模型选择部分这样设置：

```python
# @title Language Model Selection
API_KEY = os.getenv('DASHSCOPE_API_KEY')  # @param {type: 'string'}
API_TYPE = 'qwen'  # @param {type: 'string'}
MODEL_NAME = 'qwen3-max'  # @param {type: 'string'}
DISABLE_LANGUAGE_MODEL = False  # @param {type: 'boolean'}

model = language_model_utils.language_model_setup(
    api_type=API_TYPE,
    model_name=MODEL_NAME,
    api_key=API_KEY,
    disable_language_model=DISABLE_LANGUAGE_MODEL,
)
```

## 支持的Qwen模型

目前集成支持所有兼容DashScope API的Qwen模型，包括但不限于：
- qwen-turbo
- qwen-plus
- qwen-max
- qwen3-max
- qwen3-plus
- qwen3-turbo

## 注意事项

1. 请确保您的API密钥有足够的额度来调用所选模型
2. 不同的Qwen模型可能有不同的性能特征和成本
3. 某些模型可能对输入长度或输出长度有限制
4. 建议先在简单任务上测试模型集成，然后再用于复杂仿真

通过以上步骤，您就可以成功在Concordia中使用Qwen模型了。