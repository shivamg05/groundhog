import unittest
from unittest.mock import MagicMock
import sys
import os
import json

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.controller import AgentController
from core.browser import Browser

class TestAgentController(unittest.TestCase):
    
    def setUp(self):
        self.mock_browser = MagicMock()
        self.mock_processor = MagicMock()
        self.mock_model = MagicMock()

        # Default returns
        self.mock_browser.capture_state.return_value = (MagicMock(), "<html>Mock</html>")
        self.mock_processor.process_image.return_value = MagicMock() 
        self.mock_processor.distill_dom.return_value = "[1] <button>Submit</button>"
        self.mock_processor.format_prompt.return_value = "Mock Prompt"

        self.controller = AgentController(
            self.mock_browser, 
            self.mock_processor, 
            self.mock_model
        )

    # --- JSON PARSING ---
    def test_json_extraction_clean(self):
        print("--- Test JSON Parsing ---\n")
        raw_output = '{"action": "click", "element_id": "1", "value": ""}'
        result = self.controller._extract_json(raw_output)
        self.assertEqual(result['action'], "click")

    def test_json_extraction_markdown(self):
        print("--- Test JSON Parsing for markdown ---\n")
        raw_output = '```json\n{"action": "type", "element_id": "5", "value": "hi"}\n```'
        result = self.controller._extract_json(raw_output)
        self.assertEqual(result['element_id'], "5")

    # --- LOGIC FLOW ---

    def test_hallucination_check(self):
        """
        Scenario: Model predicts ID [99], but DOM only has [1].
        Result: RETRY. No execution, No scroll.
        """
        print("--- Test Hallucination ---\n")
        self.mock_processor.distill_dom.return_value = "[1] <button>OK</button>"
        self.mock_model.predict.return_value = json.dumps({
            "action": "click", "element_id": "99", "is_finished": False
        })

        self.controller.run_task("Goal", "http://test.com", max_steps=1)

        # Assert: We caught the hallucination and did nothing (just retried loop)
        self.mock_browser.execute_action.assert_not_called()
        self.mock_browser.scroll.assert_not_called()

    def test_target_not_found_scrolling(self):
        """
        Scenario: Model predicts ID "0" (Target not visible).
        Result: SCROLL.
        """
        print("--- Test element id = 0 --> Scrolling ---\n")
        self.mock_model.predict.return_value = json.dumps({
            "action": "click", "element_id": "0", "is_finished": False
        })

        self.controller.run_task("Goal", "http://test.com", max_steps=1)

        self.mock_browser.execute_action.assert_not_called()
        self.mock_browser.scroll.assert_called_with("down")

    def test_action_scroll_explicit(self):
        """
        Scenario: Model predicts action "scroll".
        Result: SCROLL.
        """
        print("--- Test explicit scroll---\n")
        self.mock_model.predict.return_value = json.dumps({
            "action": "scroll", "element_id": "5", "is_finished": False
        })

        self.controller.run_task("Goal", "http://test.com", max_steps=1)
        self.mock_browser.scroll.assert_called_with("down")

    def test_happy_path_execution(self):
        """
        Scenario: Valid ID [50] exists in DOM.
        Result: EXECUTE.
        """
        print("--- Test Happy Path---\n")
        self.mock_processor.distill_dom.return_value = "[50] <input> Search"
        self.mock_model.predict.return_value = json.dumps({
            "action": "type", "element_id": "50", "value": "Groundhog", "is_finished": False
        })

        self.controller.run_task("Goal", "http://test.com", max_steps=1)

        self.mock_browser.execute_action.assert_called_with("type", "50", "Groundhog")
        self.mock_browser.scroll.assert_not_called()

    def test_task_completion(self):
        """
        Scenario: Model predicts finished.
        Result: STOP.
        """
        print("--- Test goal completion ---\n")
        self.mock_model.predict.return_value = json.dumps({
            "action": "finish", "element_id": "0", "value": "Done", "is_finished": True
        })

        success = self.controller.run_task("Goal", "http://test.com", max_steps=5)
        self.assertTrue(success)
        self.assertEqual(self.mock_model.predict.call_count, 1)

if __name__ == "__main__":
    unittest.main()