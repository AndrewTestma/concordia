import os
import logging
import argparse
from src.loader import ScriptLoader
from src.gm import GameMaster
from src.dify_client import UniversalDifyClient

def main():
    parser = argparse.ArgumentParser(description="通用剧本杀自动化引擎启动器")
    parser.add_argument("--script", type=str, default="data/demo_case.yaml", help="剧本文件路径")
    parser.add_argument("--api_key", type=str, default="YOUR_DIFY_API_KEY", help="Dify API Key")
    parser.add_argument("--mock", action="store_true", help="使用 Mock 模式而不连接真实 API")
    args = parser.parse_args()

    # 1. 加载剧本
    script_path = os.path.join(os.path.dirname(__file__), args.script)
    loader = ScriptLoader(script_path)
    try:
        manifest = loader.load()
    except Exception as e:
        print(f"❌ 剧本加载失败: {e}")
        return

    # 2. 初始化 Dify Client
    if args.mock:
        print("⚠️ 正在使用 Mock Dify Client")
        class MockClient(UniversalDifyClient):
            def __init__(self, api_key): pass
            def query_player(self, player_id, role_profile, task, game_context, memory_summary, knowledge_tag=""):
                return f"[{player_id}] 收到。我的回应是：关于 {task}，我觉得..."
            def query_director(self, **kwargs):
                return {"shots": [{"sd_prompt": "mock prompt"}]}
        
        client = MockClient(args.api_key)
    else:
        client = UniversalDifyClient(api_key=args.api_key)

    # 3. 初始化 Game Master
    gm = GameMaster(manifest, client)

    # 4. 开始游戏
    try:
        gm.run()
    except KeyboardInterrupt:
        print("\n🛑 游戏被用户中断。")

if __name__ == "__main__":
    main()
