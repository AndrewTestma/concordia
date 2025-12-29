"""
Entry point for Werewolf 3.0.
运行狼人杀游戏的入口脚本。
"""

import sys
import os

# Ensure we can import from the current directory despite the dot in the name
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# We also need the root concordia package
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from game_master import WerewolfGameMaster
    from model_router import ModelRouter
except ImportError:
    # Fallback if running from root
    from examples.werewolf3_0.game_master import WerewolfGameMaster
    from examples.werewolf3_0.model_router import ModelRouter

def main():
    print("正在初始化狼人杀 3.0...")

    # Initialize Model Router
    router = ModelRouter()

    # Create Game Master
    gm = WerewolfGameMaster(router)

    # Setup Players
    # 6 players required for the new setup
    players = ["grok-4", "gpt-4", "qwen3", "doubao", "gpt-5", "ds-r1"]
    gm.setup_game(players)

    # Run Game
    gm.run_game_loop()

if __name__ == "__main__":
    main()
