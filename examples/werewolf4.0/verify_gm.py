import os
import logging
from GameMaster import GameMaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyGM")

def verify_gm():
    print("=== 开始验证 GameMaster ===")
    
    # 1. 配置测试玩家
    players_config = [
        {'id': 'P1', 'name': 'Seer_Alice', 'role': 'SEER'},
        {'id': 'P2', 'name': 'Wolf_Bob', 'role': 'WEREWOLF'},
        {'id': 'P3', 'name': 'Villager_Charlie', 'role': 'VILLAGER'},
        {'id': 'P4', 'name': 'Villager_Dave', 'role': 'VILLAGER'}
    ]
    
    # 2. 获取环境变量 (使用默认值以方便测试)
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "Asd7535437")
    dify_api_key = "MOCK_KEY" # 使用 Mock 模式
    
    try:
        # 3. 初始化 GameMaster
        gm = GameMaster(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            dify_api_key=dify_api_key,
            players_config=players_config
        )
        
        # 4. 运行游戏循环 (限制为 2 回合以快速验证)
        logger.info("启动游戏循环 (Max Rounds = 2)...")
        gm.run_game_loop(max_rounds=2)
        
        # 5. 验证结束后关闭连接
        gm.close()
        print("=== 验证完成 ===")
        
    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_gm()
