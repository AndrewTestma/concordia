import os
from Neo4jAdapter import Neo4jAdapter

def main():
    # Configuration - using provided credentials as defaults
    uri = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Asd7535437")

    print(f"Connecting to {uri} as {user}...")

    try:
        adapter = Neo4jAdapter(uri, user, password)
        print("Connected.")

        confirm = input("Are you sure you want to CLEAR the entire graph? (y/n): ")
        if confirm.lower() == 'y':
            adapter.clear_graph()
            print("Graph database cleared successfully.")
        else:
            print("Operation cancelled.")

        adapter.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
