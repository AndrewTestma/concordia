"""
Test script for DeepSeek model integration with Concordia.
"""

import os
from concordia.contrib import language_models as language_model_utils

# Get API key from environment variable
api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    raise ValueError("Please set the DEEPSEEK_API_KEY environment variable")

# Initialize the DeepSeek model
model = language_model_utils.language_model_setup(
    api_type='deepseek',
    model_name='deepseek-chat',
    api_key=api_key,
)

# Test the model with a simple prompt
prompt = "你好，请介绍一下你自己。"
response = model.sample_text(prompt)

print("Prompt:", prompt)
print("Response:", response)

# Test choice selection
prompt = "以下哪个选项最能代表人工智能的未来发展方向？"
choices = [
    "通用人工智能（AGI）",
    "专用人工智能在特定领域的深入应用",
    "人机协作的增强智能",
    "无法预测的发展方向"
]

selected_index, selected_response, logprobs = model.sample_choice(prompt, choices)

print("\nChoice selection test:")
print("Prompt:", prompt)
print("Choices:", choices)
print("Selected index:", selected_index)
print("Selected response:", selected_response)