import unittest
import sys
import os
from PIL import Image

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.processor import Processor

class TestProcessor(unittest.TestCase):
    
    def setUp(self):
        self.processor = Processor()

    def test_image_resizing_and_cropping(self):
        """
        Verifies that images are resized to width 1024 and capped at height 1280.
        """
        print("\n--- Testing Image Processing ---")
        
        # Case 1: Huge Image (Needs Resize AND Crop)
        # 2560px wide -> scales down to 1024 (factor 0.4)
        # 5000px high -> scales down to 2000. 
        # 2000 > 1280, so it should be cropped to 1280.
        huge_img = Image.new('RGB', (2560, 5000), color='red')
        processed_huge = self.processor.process_image(huge_img)
        
        print(f"Huge Input (2560x5000) -> Output: {processed_huge.size}")
        self.assertEqual(processed_huge.size, (1024, 1280), "Should resize width to 1024 and crop height to 1280")

        # Case 2: Wide Short Image (Needs Resize, NO Crop)
        # 2048px wide -> scales down to 1024 (factor 0.5)
        # 1000px high -> scales down to 500.
        # 500 < 1280, so no crop needed.
        wide_img = Image.new('RGB', (2048, 1000), color='blue')
        processed_wide = self.processor.process_image(wide_img)
        
        print(f"Wide Input (2048x1000) -> Output: {processed_wide.size}")
        self.assertEqual(processed_wide.size, (1024, 500), "Should resize width to 1024 and maintain aspect ratio")

    def test_format_prompt_structure(self):
        """
        Verifies that the prompt string is constructed correctly.
        """
        print("\n--- Testing Prompt Formatting ---")
        
        dummy_goal = "Book a flight to Mars"
        dummy_dom = "[1] <button> Launch </button>\n[2] <input> Destination"
        
        prompt = self.processor.format_prompt(dummy_goal, dummy_dom)
        
        # Check that key components are present
        self.assertIn(f"TASK: {dummy_goal}", prompt)
        self.assertIn("ELEMENTS:\n" + dummy_dom, prompt)
        self.assertIn("Generate a JSON with keys:", prompt)
        
        print("Prompt successfully formatted.")

if __name__ == "__main__":
    unittest.main()