import yaml
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ScriptLoader")

@dataclass
class MetaConfig:
    id: str
    name: str
    version: str
    description: Optional[str] = None

@dataclass
class KnowledgeConfig:
    dataset_id: str
    tag_strategy: str

@dataclass
class VisualStyle:
    base_prompt: str
    negative_prompt: str
    character_appearance: Dict[str, str]
    scene_appearance: Dict[str, str]

@dataclass
class CharacterConfig:
    id: str
    name: str
    profile: str
    private_knowledge_tag: str
    objectives: List[str]

@dataclass
class PhaseConfig:
    id: str
    type: str
    label: str
    scene: str
    instruction: str
    next_phase: Optional[str] = None
    default_next: Optional[str] = None
    duration_turns: Optional[int] = None

@dataclass
class ScriptManifest:
    meta: MetaConfig
    knowledge_config: KnowledgeConfig
    visual_style: VisualStyle
    characters: List[CharacterConfig]
    phases: List[PhaseConfig]

class ScriptLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_data = None
        self.manifest: Optional[ScriptManifest] = None

    def load(self) -> ScriptManifest:
        """加载并解析 YAML 剧本文件"""
        logger.info(f"开始加载剧本文件: {self.file_path}")
        
        if not os.path.exists(self.file_path):
            logger.error(f"文件不存在: {self.file_path}")
            raise FileNotFoundError(f"文件未找到: {self.file_path}")

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.raw_data = yaml.safe_load(f)
            
            logger.info("YAML 文件读取成功，开始解析结构...")
            self.manifest = self._parse_manifest(self.raw_data)
            logger.info(f"剧本 '{self.manifest.meta.name}' (ID: {self.manifest.meta.id}) 加载完成")
            return self.manifest
        except yaml.YAMLError as e:
            logger.error(f"YAML 格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"剧本加载失败: {e}")
            raise

    def _parse_manifest(self, data: Dict[str, Any]) -> ScriptManifest:
        try:
            # 1. Meta
            meta_data = data.get('meta', {})
            if not meta_data:
                raise ValueError("缺少 'meta' 字段")
            meta = MetaConfig(**meta_data)

            # 2. Knowledge Config
            know_data = data.get('knowledge_config', {})
            if not know_data:
                raise ValueError("缺少 'knowledge_config' 字段")
            knowledge_config = KnowledgeConfig(**know_data)

            # 3. Visual Style
            vis_data = data.get('visual_style', {})
            if not vis_data:
                raise ValueError("缺少 'visual_style' 字段")
            visual_style = VisualStyle(**vis_data)

            # 4. Characters
            char_list_data = data.get('characters', [])
            if not char_list_data:
                raise ValueError("缺少 'characters' 字段或列表为空")
            characters = [CharacterConfig(**c) for c in char_list_data]

            # 5. Phases
            phase_list_data = data.get('phases', [])
            if not phase_list_data:
                raise ValueError("缺少 'phases' 字段或列表为空")
            phases = [PhaseConfig(**p) for p in phase_list_data]

            return ScriptManifest(
                meta=meta,
                knowledge_config=knowledge_config,
                visual_style=visual_style,
                characters=characters,
                phases=phases
            )
        except TypeError as e:
            logger.error(f"字段类型或参数不匹配: {e}")
            raise ValueError(f"Schema 校验失败: {e}")

if __name__ == "__main__":
    # 简单测试
    try:
        # 假设在 scriptkill 目录下运行
        demo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "demo_case.yaml")
        print(f"尝试加载: {demo_path}")
        loader = ScriptLoader(demo_path)
        manifest = loader.load()
        print(f"\n=== 加载成功 ===")
        print(f"剧本名称: {manifest.meta.name}")
        print(f"视觉风格: {manifest.visual_style.base_prompt[:50]}...")
        print(f"包含角色: {[c.name for c in manifest.characters]}")
        print(f"流程阶段: {[p.id for p in manifest.phases]}")
    except Exception as e:
        print(f"测试失败: {e}")
