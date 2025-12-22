import os
import networkx as nx


def build_concordia_architecture_graph() -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()

    # Layers
    layers = {
        "顶层": "外部接口与适配",
        "中层": "应用与协调",
        "底层": "存储与工具",
    }

    # Nodes
    nodes = [
        # 顶层
        {
            "id": "llm_providers",
            "name": "LLM 提供商适配层",
            "layer": "顶层",
            "type": "适配器集合",
            "module": "concordia/contrib/language_models/*",
            "desc": "OpenAI、Google、Amazon、HuggingFace、Mistral、Ollama、Together、VLLM 等统一封装",
        },
        {
            "id": "embedder",
            "name": "Sentence Embedder",
            "layer": "顶层",
            "type": "函数/服务",
            "module": "user-provided callable",
            "desc": "用于关联记忆的句向量嵌入函数",
        },
        # 中层
        {
            "id": "simulation",
            "name": "Simulation",
            "layer": "中层",
            "type": "核心编排",
            "module": "concordia/prefabs/simulation/generic.py",
            "desc": "初始化实体与 GM、运行引擎循环、生成日志与检查点",
        },
        {
            "id": "engines",
            "name": "Engines",
            "layer": "中层",
            "type": "执行引擎",
            "module": "concordia/environment/engines/*",
            "desc": "Sequential/Simultaneous/Questionnaire 等时间与执行流控制",
        },
        {
            "id": "entities",
            "name": "Entities",
            "layer": "中层",
            "type": "参与者",
            "module": "concordia/agents/*",
            "desc": "能够观察世界与采取动作的主体（带组件与日志）",
        },
        {
            "id": "game_masters",
            "name": "Game Masters",
            "layer": "中层",
            "type": "环境协调者",
            "module": "concordia/components/game_master/*",
            "desc": "负责生成观察、定义动作规格、决定下一行动者与解析事件",
        },
        {
            "id": "agent_components",
            "name": "Agent Components",
            "layer": "中层",
            "type": "组件集合",
            "module": "concordia/components/agent/*",
            "desc": "记忆、指令、观察、计划、拼接行动等可组合的上下文组件",
        },
        {
            "id": "prefabs",
            "name": "Prefabs",
            "layer": "中层",
            "type": "构建配方",
            "module": "concordia/prefabs/*",
            "desc": "可复用的实体/GM/仿真配方（basic、dialogic、marketplace 等）",
        },
        {
            "id": "language_model_base",
            "name": "LanguageModel 基类",
            "layer": "中层",
            "type": "抽象接口",
            "module": "concordia/language_model/language_model.py",
            "desc": "统一采样接口（sample_text、sample_choice），供适配层实现",
        },
        # 底层
        {
            "id": "assoc_memory",
            "name": "AssociativeMemoryBank",
            "layer": "底层",
            "type": "内存存储",
            "module": "concordia/associative_memory/basic_associative_memory.py",
            "desc": "基于嵌入的记忆存取，GM 共享一个内存库，实体各自持有",
        },
        {
            "id": "typing",
            "name": "Typing",
            "layer": "底层",
            "type": "类型与协议",
            "module": "concordia/typing/*",
            "desc": "Prefab/Entity/Scene/Simulation 等类型定义与协议约束",
        },
        {
            "id": "utils",
            "name": "Utils",
            "layer": "底层",
            "type": "工具集合",
            "module": "concordia/utils/*",
            "desc": "并发、HTML、JSON、采样、绘图等通用工具",
        },
        # Agent Components 子节点
        {
            "id": "component_instructions",
            "name": "Instructions",
            "layer": "中层",
            "type": "行为指令组件",
            "module": "concordia/components/agent/instructions.py",
            "desc": "为代理提供角色扮演的默认指令，定义代理应该如何表现",
        },
        {
            "id": "component_memory",
            "name": "Memory",
            "layer": "中层",
            "type": "记忆组件",
            "module": "concordia/components/agent/memory.py",
            "desc": "由记忆库支持的组件，用于存储和检索代理的经验",
        },
        {
            "id": "component_observation",
            "name": "Observation",
            "layer": "中层",
            "type": "观察组件",
            "module": "concordia/components/agent/observation.py",
            "desc": "接收和处理代理观察到的信息，将其添加到记忆中",
        },
        {
            "id": "component_all_similar_memories",
            "name": "All Similar Memories",
            "layer": "中层",
            "type": "相似记忆检索组件",
            "module": "concordia/components/agent/all_similar_memories.py",
            "desc": "检索与当前情境相似的记忆，帮助代理做出决策",
        },
        {
            "id": "component_concat_act",
            "name": "Concat Act Component",
            "layer": "中层",
            "type": "行动拼接组件",
            "module": "concordia/components/agent/concat_act_component.py",
            "desc": "将来自不同上下文组件的信息拼接起来，生成代理的行动",
        },
        {
            "id": "component_constant",
            "name": "Constant",
            "layer": "中层",
            "type": "常量组件",
            "module": "concordia/components/agent/constant.py",
            "desc": "返回固定值的简单组件，用于提供不变的上下文信息",
        },
        {
            "id": "component_plan",
            "name": "Plan",
            "layer": "中层",
            "type": "计划组件",
            "module": "concordia/components/agent/plan.py",
            "desc": "帮助代理制定和跟踪长期计划的组件",
        },
        {
            "id": "component_question_of_recent_memories",
            "name": "Question of Recent Memories",
            "layer": "中层",
            "type": "近期记忆问题组件",
            "module": "concordia/components/agent/question_of_recent_memories.py",
            "desc": "基于最近记忆提出问题并回答，增强代理的反思能力",
        },
    ]

    # Add nodes
    for n in nodes:
        g.add_node(
            n["id"],
            name=n["name"],
            layer=n["layer"],
            type=n["type"],
            module=n["module"],
            desc=n["desc"],
        )

    # Edges (交互关系)
    edges = [
        # 仿真编排
        ("simulation", "engines", "uses"),
        ("simulation", "game_masters", "instantiates"),
        ("simulation", "entities", "instantiates"),
        ("simulation", "assoc_memory", "creates_for_gm"),
        # 行为与观察
        ("entities", "game_masters", "act_to"),
        ("game_masters", "entities", "make_observation_for"),
        ("engines", "game_masters", "query_components"),
        # 组件组合
        ("entities", "agent_components", "compose"),
        ("prefabs", "entities", "build"),
        ("prefabs", "game_masters", "build"),
        # 语言模型
        ("entities", "language_model_base", "call"),
        ("llm_providers", "language_model_base", "implement"),
        # 记忆与嵌入
        ("assoc_memory", "embedder", "use"),
        ("entities", "assoc_memory", "own"),
        ("game_masters", "assoc_memory", "share"),
        # 类型与工具
        ("simulation", "typing", "depend"),
        ("game_masters", "typing", "depend"),
        ("entities", "typing", "depend"),
        ("engines", "typing", "depend"),
        ("simulation", "utils", "use"),
        ("engines", "utils", "use"),
        # Agent Components 子节点关系
        ("agent_components", "component_instructions", "contains"),
        ("agent_components", "component_memory", "contains"),
        ("agent_components", "component_observation", "contains"),
        ("agent_components", "component_all_similar_memories", "contains"),
        ("agent_components", "component_concat_act", "contains"),
        ("agent_components", "component_constant", "contains"),
        ("agent_components", "component_plan", "contains"),
        ("agent_components", "component_question_of_recent_memories", "contains"),
        # 组件使用关系
        ("component_instructions", "language_model_base", "use"),
        ("component_all_similar_memories", "language_model_base", "use"),
        ("component_concat_act", "language_model_base", "use"),
        ("component_question_of_recent_memories", "language_model_base", "use"),
        ("component_memory", "assoc_memory", "use"),
        ("component_observation", "component_memory", "add_to"),
        ("component_all_similar_memories", "component_memory", "retrieve_from"),
    ]

    for src, dst, rel in edges:
        g.add_edge(src, dst, relation=rel)

    return g


def export_graph(g: nx.MultiDiGraph, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    outputs = {}

    # GraphML
    graphml_path = os.path.join(out_dir, "architecture.graphml")
    nx.write_graphml(g, graphml_path)
    outputs["graphml"] = graphml_path

    # GEXF
    gexf_path = os.path.join(out_dir, "architecture.gexf")
    nx.write_gexf(g, gexf_path)
    outputs["gexf"] = gexf_path

    return outputs

def export_matplotlib_images(g: nx.MultiDiGraph, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return {}
    pos = nx.multipartite_layout(g, subset_key="layer")
    plt.figure(figsize=(16, 9))
    nx.draw_networkx_nodes(g, pos, node_size=1200)
    nx.draw_networkx_labels(g, pos, labels={node: g.nodes[node].get("name", node) for node in g.nodes})
    nx.draw_networkx_edges(g, pos, arrows=True)
    plt.axis("off")
    png_path = os.path.join(out_dir, "architecture.png")
    svg_path = os.path.join(out_dir, "architecture.svg")
    plt.savefig(png_path, dpi=200, bbox_inches="tight")
    plt.savefig(svg_path, bbox_inches="tight")
    plt.close()
    return {"png": png_path, "svg": svg_path}

def export_graphviz_images(g: nx.MultiDiGraph, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    try:
        from networkx.drawing.nx_pydot import to_pydot
        p = to_pydot(g)
        svg_path = os.path.join(out_dir, "architecture.svg")
        png_path = os.path.join(out_dir, "architecture.png")
        p.write_svg(svg_path)
        p.write_png(png_path)
        return {"png": png_path, "svg": svg_path}
    except Exception:
        return export_matplotlib_images(g, out_dir)

def main():
    g = build_concordia_architecture_graph()
    outputs_a = export_graph(g, out_dir=os.path.join("docs"))
    outputs_b = export_graphviz_images(g, out_dir=os.path.join("docs"))
    for k, v in {**outputs_a, **outputs_b}.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()