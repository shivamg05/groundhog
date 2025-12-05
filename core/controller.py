import time
import json
import re
import os
from core.browser import Browser
from core.processor import Processor
from core.model import ModelEngine

class AgentController:
    def __init__(self, browser: Browser, processor: Processor, model: ModelEngine):
        """
        Args:
            browser: Instance of core.browser.Browser
            processor: Instance of core.processor.Processor
            model: Instance of core.model.ModelEngine
        """
        self.browser = browser
        self.processor = processor
        self.model = model

    def _extract_json(self, text):
        """
        Robustly extracts JSON from model output.
        Handles markdown code blocks (```json ... ```) or plain text.
        """
        try:
            # try to find JSON inside code blocks first
            code_block_pattern = r"```json\s*(\{.*?\})\s*```"
            match = re.search(code_block_pattern, text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            # try to find the first curly brace block
            brace_pattern = r"(\{.*\})"
            match = re.search(brace_pattern, text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            
            # fallback: try parsing the raw text
            return json.loads(text)
            
        except json.JSONDecodeError:
            print(f"[Controller] ❌ Failed to parse JSON: {text}")
            return None

    def _get_valid_ids_from_dom(self, distilled_dom):
        """
        Extracts all IDs present in the distilled DOM string.
        Format is: [123] <tag> ...
        """
        # Finds all numbers inside brackets at the start of a line
        ids = re.findall(r"\[(\d+)\]", distilled_dom)
        return set(ids)

    def run_task(self, goal, start_url, max_steps=15):
        """
        Main Agent Loop
        """
        print(f"\n🚀 [Agent] Starting Task: {goal}")
        print(f"   [Agent] URL: {start_url}")
        
        debug_dir = os.path.join("debug_traces", f"task_{int(time.time())}")
        os.makedirs(debug_dir, exist_ok=True)
        print(f"   [Debug] Saving traces to: {debug_dir}")

        self.browser.navigate(start_url)
        
        for step in range(1, max_steps + 1):
            print(f"\n--- Step {step}/{max_steps} ---")
            
            screenshot, raw_html = self.browser.capture_state()
            
            processed_img = self.processor.process_image(screenshot)

            processed_img.save(os.path.join(debug_dir, f"step_{step}_view.png"))

            distilled_dom = self.processor.distill_dom(raw_html)

            with open(os.path.join(debug_dir, f"step_{step}_dom.txt"), "w", encoding="utf-8") as f:
                f.write(distilled_dom)

            prompt = self.processor.format_prompt(goal, distilled_dom)

            valid_ids = self._get_valid_ids_from_dom(distilled_dom)

            # inference
            print("[Agent] Thinking...")
            raw_pred = self.model.predict(processed_img, prompt)
            # print(f"[Debug] Raw Model Output: {raw_pred}")

            with open(os.path.join(debug_dir, f"step_{step}_output.txt"), "w", encoding="utf-8") as f:
                f.write(raw_pred)

            action_dict = self._extract_json(raw_pred)
            
            if not action_dict:
                print("[Agent] ⚠️ Model output invalid. Retrying step...")
                continue

            print(f"[Agent] Prediction: {action_dict}")

            # 5. Logic & Execution
            if action_dict.get("is_finished", False):
                print(f"✅ [Agent] Task Marked Complete by Model.")
                return True

            element_id = str(action_dict.get("element_id", "0"))
            if element_id.lower() in ["none", "null", "nan", "undefined"]:
                element_id = "0"

            action_type = action_dict.get("action", "").lower()
            value = action_dict.get("value", "")

            # --- HANDLE ID 0 (Target Not Visible) ---
            if element_id == "0" or action_type == "scroll":
                print("[Agent] Target element not in current view (ID 0). Scrolling down...")
                self.browser.scroll("down")
                time.sleep(2)
                continue
            
            elif element_id in valid_ids:
                success = self.browser.execute_action(action_type, element_id, value)
                if not success:
                    print("[Agent] ⚠️ Action failed on valid ID")
                time.sleep(2)
                continue
            # CASE C: Hallucination (ID is not 0, not scroll, and NOT in DOM)
            else:
                print(f"[Agent] ⚠️ Hallucination detected: ID {element_id} was not in the processed DOM. Retrying step...")
                # We simply 'continue' here. 
                # Since we didn't scroll or act, the browser state remains identical.
                # The next loop iteration will take the same screenshot and prompt the model again.
                continue

        print("❌ [Agent] Max steps reached. Task incomplete.")
        return False