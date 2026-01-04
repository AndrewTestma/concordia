import unittest
from unittest.mock import MagicMock, patch
import json
from DifyClient import DifyClient
from PlayerState import PlayerState
from LogicEngine import LogicEngine
from TheEye import TheEye

class TestDifyIntegration(unittest.TestCase):

    def setUp(self):
        self.player_state = PlayerState("P1", "Alice", "Seer")
        self.player_state.update_suspicion("P2", 20, "Looks suspicious")
        self.logic_engine = LogicEngine()
        # Mock TheEye to avoid Neo4j dependency in this test
        self.mock_adapter = MagicMock()
        self.the_eye = TheEye(self.mock_adapter)
        self.dify_client = DifyClient(api_key="mock_key", base_url="http://117.50.34.101/v1")

    def test_payload_assembly(self):
        """测试 Payload 组装逻辑"""
        print("\n--- Testing Payload Assembly ---")

        # Mock TheEye return value
        mock_events = [
            {
                "source_name": "P2",
                "action": "VOTE",
                "target_name": "P3",
                "properties": {"round": 1},
                "visibility": "PUBLIC"
            }
        ]
        self.the_eye.get_player_view = MagicMock(return_value=mock_events)

        game_meta = {
            "game_id": "G_Test",
            "round": 1,
            "phase": "DAY_DISCUSSION",
            "step_name": "P1_SPEAK"
        }

        payload = self.dify_client.assemble_payload(
            game_meta=game_meta,
            player_state=self.player_state,
            the_eye=self.the_eye,
            logic_engine=self.logic_engine
        )

        # Verify structure
        self.assertIn("meta_info", payload)
        self.assertIn("player_info", payload)
        self.assertIn("perception", payload)
        self.assertIn("subjective_state", payload)

        # Verify content
        self.assertEqual(payload["player_info"]["role"], "Seer")
        self.assertEqual(payload["meta_info"]["phase"], "DAY_DISCUSSION")
        # Check if logic engine processed the event
        self.assertTrue(any("P2 投票给了 P3" in hint for hint in payload["perception"]["objective_facts"]))

        print("Payload JSON:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    @patch('requests.post')
    def test_workflow_run(self, mock_post):
        """测试 API 调用 (Mock)"""
        print("\n--- Testing API Call (Mock) ---")

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "status": "succeeded",
                "outputs": {
                    "speech": "我是预言家...",
                    "action": "VOTE P2"
                }
            }
        }
        mock_post.return_value = mock_response

        inputs = {"test": "data"}
        result = self.dify_client.run_workflow(inputs, "P1")

        self.assertEqual(result["speech"], "我是预言家...")
        print("API Result:", result)

if __name__ == '__main__':
    unittest.main()
