"""
Model Router and DMXApi Integration for Werewolf 3.0.
负责多模型路由和 DMXApi 的集成。
"""

from typing import Sequence, Mapping, Any, Collection
from concordia.language_model import language_model
from concordia.contrib.language_models.dmxapi import dmxapi_model
import random
import os

class ModelRouter:
    """
    Routes roles to specific models.
    根据角色路由到不同的模型。
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self._api_key = api_key or os.environ.get("DMXAPI_KEY")
        self._base_url = base_url or os.environ.get("DMXAPI_BASE_URL", 'https://www.dmxapi.com')

        # 定义可用模型池
        # 用户需求：为分别每个身份随机指定一个模型，并给出号码
        self._model_pool = [
            "grok-4",
            "gpt-4-turbo",
            "qwen3-coder-plus",
            "doubao-seed-1-6-flash-250828",
            "deepseek-v3",
            "DeepSeek-R1-0528-128K"
        ]

        # 预定义的角色偏好（可选，如果完全随机可以忽略）
        # 这里我们实现完全随机分配，每个玩家实例化时从池中随机抽取一个模型
        self._default_model = "gpt-3.5-turbo"

        # 创建玩家到模型的映射，确保每个玩家名称对应一个固定的模型
        self._player_model_mapping = {}

    def get_model_for_role(self, role: str) -> language_model.LanguageModel:
        # 如果该角色还没有分配模型，则从模型池中分配一个
        if role not in self._player_model_mapping:
            # 从模型池中随机选择一个模型，但确保不重复（如果模型池大小大于等于玩家数）
            available_models = [model for model in self._model_pool if model not in self._player_model_mapping.values()]
            if available_models:
                model_name = random.choice(available_models)
            else:
                # 如果模型池中的模型都已分配，从已分配的模型中随机选择一个
                model_name = random.choice(self._model_pool)
            self._player_model_mapping[role] = model_name
        else:
            model_name = self._player_model_mapping[role]

        # 为了满足"为对应的模型起名字，并给出号码"的需求，我们可以在这里做一些记录或者直接打印
        # 但LanguageModel接口只接受model_name。
        # 我们这里简单地随机选择，具体的"号码"可能是指我们在日志中区分它们。

        # 如果需要更复杂的逻辑，比如不同角色有不同的随机池：
        # (已移除：完全随机分配)


        # 生成一个随机编号，附加在模型名称后（仅用于显示/区分，实际API调用取决于DMXApi是否支持别名）
        # DMXApi通常只接受标准模型名。这里我们只返回标准名。
        # 用户提到的"给出号码"可能是在上层逻辑分配的。
        # 这里我们打印一下分配结果
        print(f"[ModelRouter] Assigning model {model_name} to role {role}")

        return dmxapi_model.DMXApiLanguageModel(
            model_name=model_name,
            api_key=self._api_key,
            base_url=self._base_url
        )
