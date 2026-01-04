import os
from Neo4jAdapter import Neo4jAdapter
from TheEye import TheEye
from LogicEngine import LogicEngine

def main():
    # 1. 设置连接
    uri = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Asd7535437")

    print("Connecting to Neo4j...")
    adapter = Neo4jAdapter(uri, user, password)
    eye = TheEye(adapter)
    logic = LogicEngine()

    try:
        # 注意: 这里假设数据库中已经有了数据 (由 verify_hand.py 生成)。
        # 如果没有数据，请先运行 verify_hand.py。
        print("Using existing graph data (please run verify_hand.py first if empty)...")

        # 2. 验证不同角色的逻辑提示

        # 2.1 村民 Alice 的视角
        print("\n--- Logic Hints for Alice (Villager) ---")
        alice_view = eye.get_player_view('p1', 'Villager')
        hints = logic.generate_logic_hints(alice_view)
        for hint in hints:
            print(hint)

        # 2.2 狼人 Bob 的视角
        print("\n--- Logic Hints for Bob (Werewolf) ---")
        bob_view = eye.get_player_view('p2', 'Werewolf')
        hints = logic.generate_logic_hints(bob_view)
        for hint in hints:
            print(hint)

        # 2.3 预言家 Charlie 的视角
        print("\n--- Logic Hints for Charlie (Seer) ---")
        charlie_view = eye.get_player_view('p3', 'Seer')
        hints = logic.generate_logic_hints(charlie_view)
        for hint in hints:
            print(hint)

    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        adapter.close()

if __name__ == "__main__":
    main()
