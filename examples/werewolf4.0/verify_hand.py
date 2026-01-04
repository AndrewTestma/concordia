import os
import time
from Neo4jAdapter import Neo4jAdapter
from TheHand import TheHand
from TheEye import TheEye

def main():
    # 1. 设置连接
    uri = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Asd7535437")

    print("Connecting to Neo4j...")
    adapter = Neo4jAdapter(uri, user, password)
    hand = TheHand(adapter)
    eye = TheEye(adapter)

    try:
        # 2. 清理并初始化
        print("Initializing game data...")
        adapter.clear_graph()

        players = [
            {'id': 'p1', 'name': 'Alice', 'role': 'Villager'},
            {'id': 'p2', 'name': 'Bob', 'role': 'Werewolf'},
            {'id': 'p3', 'name': 'Charlie', 'role': 'Seer'},
            {'id': 'p4', 'name': 'David', 'role': 'Villager'}
        ]
        adapter.init_game_data(players)

        # 3. 测试 TheHand 写入事件
        print("\nTesting TheHand event logging...")

        # 3.1 公开投票 (Alice 投给 Bob)
        print("- Logging Vote: Alice -> Bob")
        hand.log_vote(voter_id='p1', target_id='p2', round_num=1)

        # 3.2 狼人击杀 (Bob 杀 Alice)
        print("- Logging Kill: Bob -> Alice (Werewolf only)")
        hand.log_kill(killer_id='p2', target_id='p1', round_num=1)

        # 3.3 预言家查验 (Charlie 查 Bob)
        print("- Logging Check: Charlie -> Bob (Seer only)")
        hand.log_check(seer_id='p3', target_id='p2', result='Werewolf', round_num=1)

        # 3.4 公开发言
        print("- Logging Speech: David -> All (simulated as p1 for demo)")
        hand.log_speech(speaker_id='p4', text="I suspect Bob is a wolf!", target_id='p1', round_num=1)

        # 4. 验证写入结果 (使用 TheEye 读取)
        print("\nVerifying with TheEye...")

        # 4.1 验证村民视角 (Alice) - 应该看到投票和发言，看不到击杀和查验
        print("\n--- Alice's View (Villager) ---")
        alice_view = eye.get_player_view('p1', 'Villager')
        for event in alice_view:
            print(f"  [{event['visibility']}] {event['source_name']} {event['action']} {event['target_name']}")

        # 4.2 验证狼人视角 (Bob) - 应该看到投票、发言和击杀
        print("\n--- Bob's View (Werewolf) ---")
        bob_view = eye.get_player_view('p2', 'Werewolf')
        for event in bob_view:
            print(f"  [{event['visibility']}] {event['source_name']} {event['action']} {event['target_name']}")

        # 4.3 验证预言家视角 (Charlie) - 应该看到投票、发言和查验
        print("\n--- Charlie's View (Seer) ---")
        charlie_view = eye.get_player_view('p3', 'Seer')
        for event in charlie_view:
            print(f"  [{event['visibility']}] {event['source_name']} {event['action']} {event['target_name']}")

        print("\nVerification Complete!")

    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        adapter.close()

if __name__ == "__main__":
    main()
