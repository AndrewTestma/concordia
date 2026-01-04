import json
import random
import time
import logging
import os
from typing import Dict, Any, List

# Import original classes
from GameMaster import GameMaster
from Neo4jAdapter import Neo4jAdapter
from DifyClient import DifyClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RealGameRunner")

# Define the models
MODELS = [
    "grok-4",
    "deepseek-r1-0528",
    "doubao-pro-128k",
    "gemini-3-pro-preview-thinking",
    "glm-4.6-thinking",
    "claude-sonnet-4-5"
]

# Define roles
ROLES_CONFIG = [
    "WEREWOLF", "WEREWOLF",
    "VILLAGER", "VILLAGER",
    "SEER", "HUNTER"
]

class RealGameMaster(GameMaster):
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, dify_api_key, players_config, model_mapping):
        # Initialize with REAL Dify Key
        super().__init__(neo4j_uri, neo4j_user, neo4j_password, dify_api_key, players_config)

        # Inject model info into player states
        for pid, p_state in self.player_states.items():
            if pid in model_mapping:
                p_state.model = model_mapping[pid]
                logger.info(f"Assigned model {model_mapping[pid]} to player {pid}")

def main():
    # 1. Setup Configuration
    # Shuffle roles and models
    random.shuffle(ROLES_CONFIG)
    random.shuffle(MODELS)

    players_config = []
    model_mapping = {}

    print("=== Game Configuration ===")
    for i in range(6):
        model = MODELS[i]
        model_short = model.split('-')[0]  # 取模型名的第一部分
        role = ROLES_CONFIG[i]
        pid = f"{model_short}_{i}"  # 使用模型名作为ID
        p_name = f"{model_short}_{role}"

        players_config.append({
            "id": pid,
            "name": p_name,
            "role": role
        })
        model_mapping[pid] = model
        print(f"Player {pid} ({p_name}): Role={role}, Model={model}")
    print("==========================\n")

    # 2. Connect to Neo4j & Dify
    NEO4J_URI = "bolt://117.50.34.101:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASS = "Asd7535437"

    # Real Dify Key from .env
    DIFY_KEY = "app-TGmd12riMUntdT3CsxvnopRO"

    try:
        gm = RealGameMaster(NEO4J_URI, NEO4J_USER, NEO4J_PASS, DIFY_KEY, players_config, model_mapping)

        # 3. Run Game
        gm.run_game_loop(max_rounds=10)

        gm.close()

    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
