import unittest
import sys
import os
import time
from bs4 import BeautifulSoup

# Add the project root to sys.path so we can import the agent modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.browser import Browser

class TestBrowserIntegration(unittest.TestCase):
    
    def setUp(self):
        """Runs before every test. Sets up the browser."""
        # We use headless=True so it doesn't pop up a window while testing,
        # but set it to False if you want to watch it happen.
        self.browser = Browser(headless=True)

    def tearDown(self):
        """Runs after every test. Closes the browser."""
        self.browser.quit()

    #integration tests
    def test_navigation_and_stamping(self):
        """
        Verifies that we can navigate to a page and that our 
        JS script successfully stamps 'data-m2w-id' on elements
        """
        print("\n--- Testing Navigation & Stamping ---")
        url = "https://example.com"
        self.browser.navigate(url)

        # Capture state
        screenshot, raw_html = self.browser.capture_state()

        # 1. Check Screenshot
        self.assertIsNotNone(screenshot)
        self.assertTrue(screenshot.size[0] > 0, "Screenshot should have width")
        print("✅ Screenshot captured.")

        # 2. Check HTML for our custom attribute
        # This confirms stamp_page.js loaded and executed
        self.assertIn("data-m2w-id", raw_html, "The HTML should contain injected IDs")
        print("✅ HTML contains stamped IDs.")

    def test_execution_flow(self):
        """
        Verifies we can find an ID from the HTML and click it.
        """
        print("\n--- Testing Action Execution ---")
        self.browser.navigate("https://example.com")
        
        _, raw_html = self.browser.capture_state()
        soup = BeautifulSoup(raw_html, "html.parser")

        # Find the "More information..." link on example.com
        # In a real run, the VLM would do this selection. 
        # Here, we simulate the VLM by finding the tag manually.
        target_link = soup.find("a") 
        
        # Get the ID our script assigned to it
        target_id = target_link.get("data-m2w-id")
        print(f"Target found: <a href='...'> (ID: {target_id})")

        self.assertIsNotNone(target_id, "Target link must have a stamped ID")

        # Execute Click
        result = self.browser.execute_action("click", target_id)
        self.assertTrue(result, "Action execution should return True")

        # Verify the click actually worked (URL should change to iana.org)
        # execute_action has a built-in sleep, so the URL might have changed already
        current_url = self.browser.driver.current_url
        print(f"URL after click: {current_url}")
        
        self.assertIn("iana.org", current_url, "Browser should have navigated to IANA after click")
        print("✅ Click action successful.")


    def test_processor_integration(self):
        """
        Verifies that the Processor can distill the HTML captured by the Browser.
        """
        from core.processor import Processor
        
        print("\n--- Testing Processor Integration ---")
        self.browser.navigate("https://socialmuse.dev")
        _, raw_html = self.browser.capture_state()
        
        processor = Processor()
        dom_text = processor.distill_dom(raw_html)
        
        print("Distilled DOM snippet:")
        print(dom_text[:1000] + "...") # Print first 300 chars
        
        # Check for Sentinel
        self.assertIn("[0] <option>", dom_text)
        
        # Generic check for [Number] <tagname>
        self.assertRegex(dom_text, r"\[\d+\] <\w+")
        print("✅ Processor successfully distilled HTML.")


    #robustness logic tests
    def test_01_id_exceeds_max(self):
        print("\n--- Test: ID Exceeds Max ---")
        # Simulate a state where we found 10 elements
        self.browser.max_id = 10
        
        # Try ID 9999
        result = self.browser.execute_action("click", "9999")
        self.assertFalse(result, "Should return False because 9999 > 10")

    def test_02_invalid_id_format(self):
        print("\n--- Test: Invalid ID Format ---")
        # max_id doesn't matter here, ValueError happens first
        invalid_ids = ["None", "NaN", "undefined", "garbage"]
        for bad_id in invalid_ids:
            result = self.browser.execute_action("click", bad_id)
            self.assertFalse(result, f"Should fail for ID: {bad_id}")

    def test_03_invalid_action_type(self):
        print("\n--- Test: Invalid Action Type ---")
        # Mock max_id so we pass the ID check
        self.browser.max_id = 100
        valid_id = "1"
        
        result = self.browser.execute_action("dance", valid_id)
        self.assertFalse(result, "Should fail because 'dance' is not a valid action")

    def test_04_missing_value_for_type(self):
        print("\n--- Test: Missing Value for Input ---")
        # Mock max_id so we pass the ID check
        self.browser.max_id = 100
        valid_id = "1"
        
        # Test None value
        result = self.browser.execute_action("type", valid_id, value=None)
        self.assertFalse(result, "Should fail for type action with None value")

    def test_05_ghost_element(self):
        print("\n--- Test: Ghost Element (NoSuchElementException) ---")
        # 1. We need a real page loaded for find_element to actually run (and fail)
        self.browser.navigate("https://example.com")
        
        # 2. Force max_id high so the logical check passes
        self.browser.max_id = 100000
        
        # 3. Try to click an ID that logic says is "valid" (int < max), 
        # but reality says doesn't exist.
        ghost_id = "99999" 
        
        result = self.browser.execute_action("click", ghost_id)
        self.assertFalse(result, "Should catch NoSuchElementException")

if __name__ == "__main__":
    unittest.main()