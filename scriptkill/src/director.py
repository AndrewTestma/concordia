import logging
import json
import os
from typing import List, Dict, Any, Optional
from src.dify_client import UniversalDifyClient
from src.loader import VisualStyle

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DirectorAgent")

class DirectorAgent:
    """
    视觉导演 Agent (Auto-Director)。

    职责：
    1. 旁观游戏进程，监听对话与动作。
    2. 维护一个缓冲池 (Buffer)。
    3. 定期调用 Dify Director Workflow 生成视觉分镜。
    4. 将分镜脚本写入本地 JSON 文件。
    """
    def __init__(self,
                 visual_config: VisualStyle,
                 dify_client: UniversalDifyClient,
                 output_dir: str = "output"):
        self.visual_config = visual_config
        self.dify_client = dify_client
        self.buffer: List[str] = []
        self.output_dir = output_dir
        self.current_scene = "unknown"

        # 缓冲阈值：每积累多少句对话生成一次分镜
        self.buffer_threshold = 2

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 初始化分镜脚本文件
        self.script_file = os.path.join(self.output_dir, "visual_script.json")
        self._init_script_file()

    def _init_script_file(self):
        """初始化或清空分镜脚本文件"""
        with open(self.script_file, 'w', encoding='utf-8') as f:
            json.dump([], f)

    def set_scene(self, scene_name: str):
        """切换场景，这将强制触发一次生成（如果 buffer 非空）"""
        if self.current_scene != scene_name:
            logger.info(f"[导演] 场景切换: {self.current_scene} -> {scene_name}")
            if self.buffer:
                self._generate_and_flush()
            self.current_scene = scene_name

    def observe(self, event_text: str):
        """
        监听事件。

        :param event_text: 事件文本 (如 "李探长: 你昨晚在哪里？")
        """
        # 过滤掉非剧情文本（如系统指令）
        if "【阶段指令】" in event_text:
            return

        self.buffer.append(event_text)
        logger.debug(f"[导演] 已缓冲 {len(self.buffer)}/{self.buffer_threshold} 条事件")

        if len(self.buffer) >= self.buffer_threshold:
            self._generate_and_flush()

    def _generate_and_flush(self):
        """调用 Dify 生成分镜，并写入文件"""
        if not self.buffer:
            return

        dialogue_chunk = "\n".join(self.buffer)
        scene_desc = self.visual_config.scene_appearance.get(self.current_scene, self.current_scene)

        logger.info(f"[导演] 正在为 {len(self.buffer)} 条对话生成分镜...")

        try:
            result = self.dify_client.query_director(
                base_style=self.visual_config.base_prompt,
                neg_prompt=self.visual_config.negative_prompt,
                char_map=self.visual_config.character_appearance,
                scene_desc=scene_desc,
                dialogue_text=dialogue_chunk
            )

            if result and "shots" in result:
                self._append_to_script(result["shots"])
                logger.info(f"[导演] 成功生成 {len(result['shots'])} 个镜头")
            else:
                logger.warning(f"[导演] 生成结果格式异常: {result}")

        except Exception as e:
            logger.error(f"[导演] 生成失败: {e}")
        finally:
            # 无论成功失败，都清空 buffer，防止阻塞后续剧情
            self.buffer = []

    def _append_to_script(self, new_shots: List[Dict[str, Any]]):
        """将新生成的镜头追加到 JSON 文件中"""
        try:
            # 读取现有内容
            if os.path.exists(self.script_file):
                with open(self.script_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []

            # 追加新镜头
            data.extend(new_shots)

            # 写回文件
            with open(self.script_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[导演] 写入分镜文件失败: {e}")

    def finalize(self):
        """游戏结束时的收尾工作"""
        if self.buffer:
            self._generate_and_flush()
        logger.info(f"[导演] 工作结束，分镜脚本已保存至: {self.script_file}")
