# 通用剧本杀自动化引擎 (Universal ScriptKill Engine)

> **当前版本**: v5.0 (Full-Stack Edition)
> **代号**: PuppetMaster & Director

本项目旨在构建一个图灵完备的剧本杀演绎与生成引擎，支持从标准化 YAML 剧本到自动化 AI 演绎，并实时输出视觉分镜脚本。

## 📁 目录结构

```
scriptkill/
├── config.yaml             # Dify 配置文件 (请在此填入 API Key)
├── data/                   # 剧本数据
│   ├── demo_case.yaml      # 示例剧本 (Schema v2.0)
│   └── xiangyang_case.yaml # "向阳山案件" 剧本
├── dify_configs/           # Dify App 配置文件
│   ├── player_reasoner.md  # 玩家推理器配置指南 (含知识库检索)
│   └── director_studio.md  # 导演工作室配置指南
├── output/                 # 运行产物
│   └── visual_script.json  # 自动生成的视觉分镜脚本
├── src/                    # 源代码
│   ├── agent.py            # UniversalAgent (Player) 实现
│   ├── director.py         # DirectorAgent (Auto-Director) 实现
│   ├── dify_client.py      # Dify API 客户端
│   ├── gm.py               # GameMaster (GM) 核心逻辑
│   ├── loader.py           # 剧本加载器
│   └── __init__.py
├── main.py                 # 启动入口
├── 技术开发文档.md          # 详细技术文档
├── 通用剧本杀自动化引擎 - 开发任务看板.md # 任务进度
└── README.md               # 本文件
```

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+ 及依赖库：

```bash
pip install pyyaml requests numpy pandas
# 可选：如果你需要使用真实的 Embedding 模型
pip install sentence-transformers
```

### 2. Dify 配置

1.  复制 `config.yaml` 并填入你的 Dify API Key 和 Base URL。
2.  参考 `dify_configs/` 下的指南在 Dify 平台创建应用。
    *   **Player Reasoner** 现在支持 `knowledge_tag` 参数，用于从知识库检索角色专属背景。

### 3. 运行引擎

运行最新的“向阳山案件”剧本（Mock 模式）：

```bash
python main.py --script data/xiangyang_case.yaml --mock
```

或者使用真实的 Dify API（需在 `config.yaml` 中配置）：

```bash
python main.py --script data/xiangyang_case.yaml
```

**运行结果**:
1.  控制台将实时显示三位角色（任志遥、丁雨蒙、姜宇恒）的对话与推理。
2.  运行结束后，会在 `output/` 目录下生成 `visual_script.json` 文件。

## 🛠️ 核心模块说明

### 1. 基础设施 (Protocol)
定义了 `ScriptManifest` 和 YAML Schema v2.0，实现了剧本数据的标准化加载。

### 2. 仿真引擎 (Simulation)
- **GameMaster**: 基于状态机调度游戏流程。
- **UniversalAgent**: 集成 Concordia 关联记忆，拥有长期记忆能力。
- **DirectorAgent**: 旁观游戏进程，监听事件流，维护对话缓冲池，并定期调用 Dify 生成分镜。

### 3. 认知层 (Cognition)
通过 `UniversalDifyClient` 将推理外包给 Dify Workflow。
- **Player Reasoner**: 负责角色的思考与对话，支持 **知识库检索 (RAG)**，通过 `knowledge_tag` 召回角色专属记忆。
- **Director Studio**: 负责将对话实时转译为 Stable Diffusion 提示词 (JSON)。

### 4. 输出层 (Output)
- **visual_script.json**: 包含时间戳、场景描述、角色动作、SD Prompt 的结构化数据，可直接用于 ComfyUI 视频生成。

## 📅 开发进度

- [x] **基础设施**: YAML Schema, ScriptLoader
- [x] **仿真引擎**: GM, Agent, Director, Memory
- [x] **认知层配置**: Dify Prompt Templates (支持 Knowledge Tag)
- [x] **视觉系统**: 自动分镜生成与导出
- [ ] **视觉闭环**: ComfyUI 桥接脚本 (可选)

更多详情请查看 [开发任务看板](通用剧本杀自动化引擎%20-%20开发任务看板.md)。
