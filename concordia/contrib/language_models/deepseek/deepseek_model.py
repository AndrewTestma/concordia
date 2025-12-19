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

"""Language Model that uses DeepSeek models via DeepSeek API."""

import os
from collections.abc import Collection
from typing import override

from concordia.language_model import language_model
from concordia.utils.deprecated import measurements as measurements_lib
from openai import OpenAI


class DeepSeekLanguageModel(language_model.LanguageModel):
  """Language Model that uses DeepSeek models via DeepSeek API."""

  def __init__(
      self,
      model_name: str,
      *,
      api_key: str | None = None,
      measurements: measurements_lib.Measurements | None = None,
      channel: str = language_model.DEFAULT_STATS_CHANNEL,
  ):
    """Initializes the instance.

    Args:
      model_name: The language model to use. For more details, see
        https://api.deepseek.com/.
      api_key: The API key to use when accessing the DeepSeek API. If None, will
        use the DEEPSEEK_API_KEY environment variable.
      measurements: The measurements object to log usage statistics to.
      channel: The channel to write the statistics to.
    """
    if api_key is None:
      api_key = os.environ.get('DEEPSEEK_API_KEY')
      if api_key is None:
        raise ValueError(
            'API key must be provided or set in DEEPSEEK_API_KEY environment variable'
        )
    self._api_key = api_key
    self._model_name = model_name
    self._measurements = measurements
    self._channel = channel

    # Create OpenAI client configured for DeepSeek
    self._client = OpenAI(
        api_key=self._api_key,
        base_url='https://api.deepseek.com',
    )

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
    """Samples text from the language model."""
    # Log the API call for measurement purposes
    if self._measurements is not None:
      self._measurements.publish_datum(
          self._channel,
          {'raw_text_length': len(prompt)},
      )

    # Prepare the messages
    messages = [{'role': 'user', 'content': prompt}]

    # Make the API call
    response = self._client.chat.completions.create(
        model=self._model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=terminators,
        stream=False,
        seed=seed,
        top_p=top_p,
    )

    # Extract and return the response text
    return response.choices[0].message.content

  @override
  def sample_choice(
      self,
      prompt: str,
      responses: list[str],
      *,
      seed: int | None = None,
  ) -> tuple[int, str, dict[str, float]]:
    """Samples a choice from a list of responses."""
    # For choice selection, we can use the same approach as other models
    # by asking the model to select the best option
    formatted_prompt = (
        f'{prompt}\n\n'
        f'Please select the best response from the following options:\n'
        f'{chr(10).join([f"{i+1}. {response}" for i, response in enumerate(responses)])}\n\n'
        f'Respond ONLY with the number of the best option (1-{len(responses)}):'
    )

    # Sample text from the model
    response_text = self.sample_text(
        formatted_prompt,
        max_tokens=10,
        temperature=0.0,  # Use low temperature for consistent choice selection
        seed=seed,
    )

    # Try to extract the selected index
    try:
      # Extract the first number from the response
      import re
      numbers = re.findall(r'\d+', response_text)
      if numbers:
        selected_index = int(numbers[0]) - 1  # Convert to 0-based index
        if 0 <= selected_index < len(responses):
          # Return the selected index, response, and empty logprobs
          return selected_index, responses[selected_index], {}
    except (ValueError, IndexError):
      pass

    # If parsing fails, return a random choice
    import random
    selected_index = random.randrange(len(responses))
    return selected_index, responses[selected_index], {}
