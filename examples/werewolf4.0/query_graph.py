import os
import sys
from Neo4jAdapter import Neo4jAdapter

def main():
    # Configuration - using provided credentials as defaults
    uri = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Asd7535437")

    try:
        adapter = Neo4jAdapter(uri, user, password)

        # Default query or argument
        if len(sys.argv) > 1:
            query = sys.argv[1]
        else:
            print("No query provided. Running default: MATCH (n) RETURN n LIMIT 25")
            query = "MATCH (n) RETURN n LIMIT 25"

        print(f"Executing query: {query}")
        results = adapter.run_query(query)

        print(f"Found {len(results)} records:")
        for r in results:
            print(r)

        adapter.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
