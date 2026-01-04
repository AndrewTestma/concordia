import logging
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Visibility Constants
VISIBILITY_PUBLIC = 'PUBLIC'
VISIBILITY_WEREWOLF = 'WEREWOLF_TEAM'
VISIBILITY_SEER = 'SEER_ONLY'
VISIBILITY_PRIVATE = 'PRIVATE'

class TheEye:
    """
    The Eye (视角过滤器)

    Responsibility:
    - Implements the "Subjective View" logic for agents.
    - Filters graph data based on player role and event visibility.
    - Ensures agents only see what they are allowed to see.
    """

    def __init__(self, adapter):
        """
        :param adapter: Instance of Neo4jAdapter to communicate with the database.
        """
        self.adapter = adapter

    def get_player_view(self, player_id: str, role: str) -> List[Dict[str, Any]]:
        """
        Retrieves the subjective subgraph visible to a specific player.

        Logic:
        1. PUBLIC events are visible to everyone.
        2. WEREWOLF_TEAM events are visible to Werewolves.
        3. SEER_ONLY events are visible to the Seer.
        4. PRIVATE events are visible only to the actor (or target, depending on definition).
           Here we assume PRIVATE means "only the actor knows".

        The query returns paths (Event)-[REL]->(Target) or (Actor)-[REL]->(Event).
        Actually, usually events are nodes linked to players.

        Assumed Schema:
        (Actor:Player)-[:DOES {visibility: '...'}, ...]->(Event:Event)
        (Event)-[:TARGETS]->(Target:Player)

        OR simpler:
        Relationships directly between players? No, we need Events to be nodes to hold history.

        Let's assume a standard Event sourcing style:
        (:Player)-[:PERFORMED]->(:Event)-[:TARGETS]->(:Player)

        The visibility is usually on the Event node or the PERFORMED relationship.
        Let's put `visibility` on the Event node for simplicity in this implementation,
        or check the Kanban: "Verify `visibility` attribute constraints" on relationships.
        Okay, Kanban says "visibility attribute on all relationships".

        So: (Player)-[:ACTION {visibility: '...'}]->(Target) could be one way.
        But for a log, we often have Event nodes.

        Let's support a mixed model or focus on the Relationship visibility as primary filter.

        Query Strategy:
        Match relationships `r` where:
        - r.visibility = 'PUBLIC'
        - OR (r.visibility = 'WEREWOLF_TEAM' AND $role = 'Werewolf')
        - OR (r.visibility = 'SEER_ONLY' AND $role = 'Seer')
        - OR (r.visibility = 'PRIVATE' AND (startNode(r).id = $player_id))

        :param player_id: The ID of the observing player.
        :param role: The role of the observing player (e.g., 'Villager', 'Werewolf', 'Seer').
        :return: A list of dictionaries representing the visible relationships/events.
        """

        # Cypher query to fetch visible relationships
        # We fetch (Subject)-[Action]->(Object) triples.
        query = """
        MATCH (source)-[r]->(target)
        WHERE
            r.visibility = $public
            OR (r.visibility = $werewolf_team AND $role = 'Werewolf')
            OR (r.visibility = $seer_only AND $role = 'Seer')
            OR (r.visibility = $private AND source.id = $player_id)
        RETURN
            source.name AS source_name,
            type(r) AS action,
            r.visibility AS visibility,
            properties(r) AS properties,
            target.name AS target_name,
            labels(source) AS source_labels,
            labels(target) AS target_labels
        ORDER BY r.timestamp ASC
        """

        params = {
            "player_id": player_id,
            "role": role,
            "public": VISIBILITY_PUBLIC,
            "werewolf_team": VISIBILITY_WEREWOLF,
            "seer_only": VISIBILITY_SEER,
            "private": VISIBILITY_PRIVATE
        }

        try:
            results = self.adapter.run_query(query, params)
            logger.info(f"Retrieved {len(results)} visible events for player {player_id} ({role}).")
            return results
        except Exception as e:
            logger.error(f"Error retrieving player view: {e}")
            raise

    def get_public_view(self) -> List[Dict[str, Any]]:
        """
        Helper to get only public events (e.g., for spectators or GM logs).
        """
        query = """
        MATCH (source)-[r]->(target)
        WHERE r.visibility = $public
        RETURN source.name, type(r), target.name, r.timestamp
        ORDER BY r.timestamp ASC
        """
        return self.adapter.run_query(query, {"public": VISIBILITY_PUBLIC})
