import os
import time
from Neo4jAdapter import Neo4jAdapter
from TheEye import TheEye, VISIBILITY_PUBLIC, VISIBILITY_WEREWOLF, VISIBILITY_SEER, VISIBILITY_PRIVATE

def setup_test_data(adapter):
    """
    Sets up a scenario with:
    1. Alice (Villager)
    2. Bob (Werewolf)
    3. Charlie (Seer)

    Events:
    1. Alice SPEAKS (Public)
    2. Bob ATTACKS Alice (Werewolf Team Only)
    3. Charlie CHECKS Bob (Seer Only)
    4. Bob WHISPERS to himself (Private - hypothetically, or just a private note)
    """
    print("Setting up test data...")
    adapter.clear_graph()

    # 1. Init Players
    players = [
        {'id': 'p1', 'name': 'Alice', 'role': 'Villager'},
        {'id': 'p2', 'name': 'Bob', 'role': 'Werewolf'},
        {'id': 'p3', 'name': 'Charlie', 'role': 'Seer'}
    ]
    adapter.init_game_data(players)

    # 2. Create Events (Relationships directly between players for simplicity in this test,
    #    matching TheEye's logic: (source)-[r]->(target))

    timestamp = int(time.time())

    queries = [
        # Alice speaks publicly
        """
        MATCH (a:Player {name: 'Alice'}), (b:Player {name: 'Bob'})
        CREATE (a)-[:SPEAKS {visibility: 'PUBLIC', content: 'I am a villager!', timestamp: $t1}]->(b)
        """,
        # Bob attacks Alice (Werewolf view)
        """
        MATCH (b:Player {name: 'Bob'}), (a:Player {name: 'Alice'})
        CREATE (b)-[:ATTACKS {visibility: 'WEREWOLF_TEAM', timestamp: $t2}]->(a)
        """,
        # Charlie checks Bob (Seer view)
        """
        MATCH (c:Player {name: 'Charlie'}), (b:Player {name: 'Bob'})
        CREATE (c)-[:CHECKS {visibility: 'SEER_ONLY', result: 'Werewolf', timestamp: $t3}]->(b)
        """,
        # Bob thinks privately
        """
        MATCH (b:Player {name: 'Bob'})
        CREATE (b)-[:THINKS {visibility: 'PRIVATE', content: 'I must win.', timestamp: $t4}]->(b)
        """
    ]

    with adapter.driver.session() as session:
        for i, q in enumerate(queries):
            session.run(q, t1=timestamp+i, t2=timestamp+i+1, t3=timestamp+i+2, t4=timestamp+i+3)

    print("Test data created.")

def verify_view(eye, player_name, player_id, role, expected_count):
    print(f"\n--- Verifying view for {player_name} ({role}) ---")
    view = eye.get_player_view(player_id, role)

    print(f"Found {len(view)} events.")
    for v in view:
        print(f"  - [{v['visibility']}] {v['source_name']} {v['action']} {v['target_name']}")

    if len(view) == expected_count:
        print(f"✅ PASS: Expected {expected_count}, got {len(view)}")
    else:
        print(f"❌ FAIL: Expected {expected_count}, got {len(view)}")

def main():
    # Configuration
    uri = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Asd7535437")

    adapter = Neo4jAdapter(uri, user, password)
    eye = TheEye(adapter)

    try:
        setup_test_data(adapter)

        # 1. Alice (Villager) should see:
        # - Her own speech (Public)
        # - NOT Bob's attack
        # - NOT Charlie's check
        # - NOT Bob's thought
        # WAIT: My setup for SPEAKS was (Alice)->(Bob). Public.
        # So Alice sees 1 event.
        verify_view(eye, "Alice", "p1", "Villager", 1)

        # 2. Bob (Werewolf) should see:
        # - Alice's speech (Public)
        # - His attack (Werewolf Team)
        # - His thought (Private)
        # - NOT Charlie's check
        # Total: 3
        verify_view(eye, "Bob", "p2", "Werewolf", 3)

        # 3. Charlie (Seer) should see:
        # - Alice's speech (Public)
        # - His check (Seer Only)
        # - NOT Bob's attack
        # - NOT Bob's thought
        # Total: 2
        verify_view(eye, "Charlie", "p3", "Seer", 2)

    finally:
        adapter.close()

if __name__ == "__main__":
    main()
