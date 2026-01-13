import requests
import json
import logging
import os
import yaml
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DifyClient")

class UniversalDifyClient:
    """
    通用 Dify 客户端，支持 Player (推理) 和 Director (导演) 两种模式。
    支持从 config.yaml 加载配置。
    """
    def __init__(self, api_key: str = None, base_url: str = None, config_path: str = "config.yaml"):
        """
        初始化 Dify 客户端。
        优先使用传入的 api_key/base_url，如果未传入则尝试从配置文件加载。
        """
        self.config = self._load_config(config_path)

        # 确定 Base URL
        self.base_url = base_url or self.config.get("dify", {}).get("base_url", "https://api.dify.ai/v1")
        self.base_url = self.base_url.rstrip('/')

        # 这里的 api_key 仅作为默认 key，实际上 query_player/director 可能使用不同的 key
        self.default_api_key = api_key

        # 获取各 App 的特定 Key
        self.player_api_key = self.config.get("dify", {}).get("player_api_key")
        self.director_api_key = self.config.get("dify", {}).get("director_api_key")

    def _load_config(self, path: str) -> Dict[str, Any]:
        """加载配置文件"""
        # 向上寻找 config.yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        config_file = os.path.join(project_root, path)

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        return {}

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _run_workflow(self, inputs: Dict[str, Any], user_id: str, api_key: str) -> Dict[str, Any]:
        """
        调用 Dify Workflow 执行 API。
        """
        if not api_key or api_key.startswith("YOUR_"):
            # Mock 模式或未配置 Key 的回退逻辑 (仅用于开发测试)
            logger.warning(f"未配置有效的 API Key (User: {user_id})，将返回 Mock 数据。")
            return {"result": f"[Mock] 收到任务。User: {user_id}"}

        url = f"{self.base_url}/workflows/run"
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id
        }

        try:
            logger.debug(f"Calling Dify API: {url}, User: {user_id}")
            response = requests.post(url, headers=self._get_headers(api_key), json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            data = result.get('data', {})

            if data.get('status') == 'succeeded':
                return data.get('outputs', {})
            else:
                logger.error(f"Dify Workflow failed: {result}")
                # 不抛出异常，而是返回错误信息，防止整个游戏崩溃
                return {"error": data.get('error'), "result": "（系统错误：AI 思考超时或失败）"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API request failed: {e}")
            return {"error": str(e), "result": "（系统错误：网络请求失败）"}
        except json.JSONDecodeError:
            logger.error("Invalid JSON response from Dify")
            return {"error": "Invalid JSON", "result": "（系统错误：响应解析失败）"}

    def query_player(self,
                     player_id: str,
                     role_profile: str,
                     task: str,
                     game_context: str,
                     memory_summary: str,
                     knowledge_tag: str = "") -> str:
        """
        调用 Player Reasoner Workflow 进行推理。
        """
        # 优先使用配置中的 player_api_key，否则使用初始化时的 default_api_key
        api_key = self.player_api_key or self.default_api_key

        inputs = {
            "role_profile": role_profile,
            "task": task,
            "game_context": game_context,
            "memory_summary": memory_summary,
            "knowledge_tag": knowledge_tag  # 新增：传递知识库标签供 Dify 过滤
        }

        outputs = self._run_workflow(inputs, user_id=player_id, api_key=api_key)
        return outputs.get('result') or outputs.get('text') or str(outputs)

    def query_director(self,
                       base_style: str,
                       neg_prompt: str,
                       char_map: Dict[str, Any],
                       scene_desc: str,
                       dialogue_text: str) -> Dict[str, Any]:
        """
        调用 Director Studio Workflow 生成分镜。
        """
        api_key = self.director_api_key or self.default_api_key

        inputs = {
            "base_style": base_style,
            "neg_prompt": neg_prompt,
            "char_map": json.dumps(char_map, ensure_ascii=False),
            "scene_desc": scene_desc,
            "dialogue_text": dialogue_text
        }

        outputs = self._run_workflow(inputs, user_id="director_agent", api_key=api_key)

        # 尝试解析返回的 JSON 字符串
        try:
            raw_json = outputs.get('visual_script') or outputs.get('text') or "{}"
            if isinstance(raw_json, dict):
                return raw_json
            # 清理可能的 markdown 标记
            raw_json = raw_json.strip().replace('```json', '').replace('```', '')
            if not raw_json: return {}
            return json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning(f"Director returned invalid JSON: {raw_json}")
            return {"error": "Invalid JSON", "raw": raw_json}

if __name__ == "__main__":
    # 测试代码
    client = UniversalDifyClient()
    print(f"Loaded Config: BaseURL={client.base_url}")
    print(f"Player Key: {client.player_api_key}")
