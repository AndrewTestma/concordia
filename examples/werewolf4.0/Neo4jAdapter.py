from neo4j import GraphDatabase
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Neo4jAdapter:
    def __init__(self, uri, user, password):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self._connect()

    def _connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            self.verify_connectivity()
            logger.info("Neo4j driver initialized and connected.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed.")

    def verify_connectivity(self):
        """Verifies that the driver can connect to the database."""
        if self.driver:
            self.driver.verify_connectivity()

    def clear_graph(self):
        """Removes all nodes and relationships from the database."""
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self.driver.session() as session:
                session.run(query)
            logger.info("Graph cleared successfully.")
        except Exception as e:
            logger.error(f"Error clearing graph: {e}")
            raise

    def init_game_data(self, players):
        """
        Initializes the game with player nodes.

        :param players: List of dictionaries containing player info.
                        Expected format: [{'id': '1', 'name': 'Alice', 'role': 'Villager'}, ...]
        """
        clear_query = "MATCH (n) DETACH DELETE n"
        create_player_query = """
        CREATE (:Player {
            id: $id,
            name: $name,
            role: $role,
            status: 'ALIVE',
            visibility: 'PUBLIC'
        })
        """

        try:
            with self.driver.session() as session:
                # First ensure clean state? Or should clear_graph be called explicitly?
                # The kanban says "init_game_data" initializes nodes. I'll assume it appends or the user clears first.
                # But to be safe for "init", usually we might want to ensure uniqueness.
                # Let's add constraints if possible, but for now just create.

                for p in players:
                    session.run(create_player_query, id=p['id'], name=p['name'], role=p['role'])
            logger.info(f"Initialized {len(players)} players.")
        except Exception as e:
            logger.error(f"Error initializing game data: {e}")
            raise

    def run_query(self, query, parameters=None):
        """Executes a custom Cypher query."""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters)
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Error running query: {e}")
            raise

if __name__ == "__main__":
    # Test execution
    import sys

    # Default credentials from user input
    URI = os.getenv("NEO4J_URI", "bolt://117.50.34.101:7687")
    USER = os.getenv("NEO4J_USER", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "Asd7535437")

    try:
        adapter = Neo4jAdapter(URI, USER, PASSWORD)
        adapter.clear_graph()

        test_players = [
            {'id': 'p1', 'name': 'Seer_Alice', 'role': 'Seer'},
            {'id': 'p2', 'name': 'Wolf_Bob', 'role': 'Werewolf'}
        ]
        adapter.init_game_data(test_players)

        # Verify
        result = adapter.run_query("MATCH (p:Player) RETURN p.name as name, p.role as role")
        print("Current Players:", result)

        adapter.close()
    except Exception as e:
        print(f"An error occurred: {e}")
