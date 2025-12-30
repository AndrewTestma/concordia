# Copyright 2025 DeepMind Technologies Limited.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import time
from typing import override
from collections.abc import Collection

import requests

from concordia.language_model import language_model
from concordia.utils.deprecated import measurements as measurements_lib


class DMXApiLanguageModel(language_model.LanguageModel):
  def __init__(
      self,
      model_name: str,
      *,
      api_key: str | None = None,
      base_url: str = 'https://www.dmxapi.com',
      measurements: measurements_lib.Measurements | None = None,
      channel: str = language_model.DEFAULT_STATS_CHANNEL,
  ):
    if api_key is None:
      api_key = os.environ.get('DMXAPI_KEY')
      if api_key is None:
        raise ValueError(
            'API key must be provided or set in DMXAPI_KEY environment variable'
        )
    self._api_key = api_key
    self._model_name = model_name
    env_base = os.environ.get('DMXAPI_BASE_URL')
    self._base_url = (env_base or base_url).rstrip('/')
    self._measurements = measurements
    self._channel = channel

  @override
  def sample_text(
      self,
      prompt: str,
      *,
      max_tokens: int = language_model.DEFAULT_MAX_TOKENS,
      terminators: Collection[str] = language_model.DEFAULT_TERMINATORS,
      temperature: float = language_model.DEFAULT_TEMPERATURE,
      timeout: float = language_model.DEFAULT_TIMEOUT_SECONDS,
      seed: int | None = None,
      top_p: float = language_model.DEFAULT_TOP_P,
      top_k: int = language_model.DEFAULT_TOP_K,
  ) -> str:
    if self._measurements is not None:
      self._measurements.publish_datum(
          self._channel,
          {'raw_text_length': len(prompt)},
      )
    # 强制所有模型使用中文输出的系统提示
    system_message = {
        'role': 'system',
        'content': (
            '你是一个狼人杀游戏的AI玩家。'
            '1. 必须全程使用中文。'
            '2. 严禁输出任何环境描写、场景氛围渲染或内心独白。'
            '3. 严禁输出"P1 observed..."或类似的观察日志。'
            '4. 只输出你的具体行动（如"我查验P2"）或发言内容。'
            '5. 保持回答简短直接。'
        )
    }
    url = f'{self._base_url}/v1/chat/completions'
    payload = {
        'model': self._model_name,
        'messages': [
            system_message,
            {'role': 'user', 'content': prompt},
        ],
        'temperature': temperature,
        'max_tokens': max_tokens,
        'top_p': top_p,
        'stream': True,
    }
    # if terminators:
    #   payload['stop'] = list(terminators)
    if seed is not None:
      payload['seed'] = seed
    headers = {
        'Accept': 'application/json',
        'Authorization': self._api_key,
        'User-Agent': 'DMXAPI/1.0.0 ( https://www.dmxapi.com )',
        'Content-Type': 'application/json',
    }
    attempts = 2
    last_error_text = ''
    # Suppress only the single InsecureRequestWarning from urllib3 needed
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for i in range(attempts):
      try:
        resp = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
            verify=False, # 忽略SSL证书验证错误
            stream=True
        )
        resp.raise_for_status()
        break
      except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        last_error_text = getattr(e.response, 'text', '')[:200]
        if status in (429, 503) and i < attempts - 1:
          time.sleep(1.0)
          continue
        raise language_model.InvalidResponseError(
            f'HTTP {status} calling {url}; body: {last_error_text}'
        )
      except requests.exceptions.RequestException as e:
        last_error_text = str(e)
        if i < attempts - 1:
          time.sleep(1.0)
          continue
        raise language_model.InvalidResponseError(
            f'Request error calling {url}: {last_error_text}'
        )

    # 处理流式响应
    full_content = ""
    buffer = ""
    for chunk in resp.iter_content(chunk_size=None):
        if chunk:
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if line.strip() == "":
                    continue
                if line.startswith("data: "):
                    data_line = line[len("data: ") :].strip()
                    if data_line == "[DONE]":
                        break
                    else:
                        try:
                            data = json.loads(data_line)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:  # 只有当内容不为空时才打印和添加
                                    print(content, end="", flush=True)
                                    full_content += content
                        except json.JSONDecodeError:
                            buffer = line + "\n" + buffer
                            break

    if not full_content.strip():
        raise language_model.InvalidResponseError(
            'No content received in streaming response'
        )

    print()  # 添加新行以完成打印
    return full_content

  @override
  def sample_choice(
      self,
      prompt: str,
      responses: list[str],
      *,
      seed: int | None = None,
  ) -> tuple[int, str, dict[str, float]]:
    options = '\n'.join([f'{i+1}. {r}' for i, r in enumerate(responses)])
    formatted_prompt = (
        f'{prompt}\n\n'
        f'Please select the best response from the following options:\n'
        f'{options}\n\n'
        f'Respond ONLY with the number of the best option (1-{len(responses)}):'
    )
    text = self.sample_text(
        formatted_prompt,
        max_tokens=10,
        temperature=0.0,
        seed=seed,
    )
    try:
      import re
      numbers = re.findall(r'\d+', text)
      if numbers:
        idx = int(numbers[0]) - 1
        if 0 <= idx < len(responses):
          return idx, responses[idx], {}
    except Exception:
      pass
    import random
    idx = random.randrange(len(responses))
    return idx, responses[idx], {}
