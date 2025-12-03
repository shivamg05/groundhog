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

    def test_navigation_and_stamping(self):
        """
        Verifies that we can navigate to a page and that our 
        JS script successfully stamps 'data-m2w-id' on elements.
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

if __name__ == "__main__":
    unittest.main()