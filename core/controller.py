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

    def run_task_generator(self, goal, start_url, max_steps=15):
        """
        loop for UIs (Gradio).
        Yields a dictionary at every step: 
        {
            "screenshot": PIL_Image, 
            "log": "text string", 
            "done": bool
        }
        """
        print(f"\n🚀 [Agent] Starting Task: {goal}")
        self.browser.navigate(start_url)
        
        logs = [f"🚀 Goal: {goal}", f"🌐 URL: {start_url}"]
        
        for step in range(1, max_steps + 1):
            step_header = f"\n--- Step {step}/{max_steps} ---"
            print(step_header)
            logs.append(step_header)
            
            # 1. Capture
            screenshot, raw_html = self.browser.capture_state()
            
            # 2. Process
            processed_img = self.processor.process_image(screenshot)
            distilled_dom = self.processor.distill_dom(raw_html)
            prompt = self.processor.format_prompt(goal, distilled_dom)
            
            # DEBUG LOG: Show user how many elements the model actually sees
            element_count = distilled_dom.count('\n') + 1
            dom_msg = f"👁️ Processed DOM: {element_count} visible elements."
            print(dom_msg)
            logs.append(dom_msg)

            # YIELD HERE: Show the user the screen BEFORE inference starts (so they don't wait)
            yield {"screenshot": processed_img, "log": "\n".join(logs), "done": False}

            # 3. Inference
            print("[Agent] Thinking...")
            logs.append("🧠 Thinking...")
            yield {"screenshot": processed_img, "log": "\n".join(logs), "done": False}
            
            raw_pred = self.model.predict(processed_img, prompt)
            
            # 4. Parse
            action_dict = self._extract_json(raw_pred)
            
            # Log the raw prediction so you can see if the model is outputting garbage
            print(f"[Agent] Raw Output: {raw_pred}")
            
            if not action_dict:
                err = f"⚠️ Invalid JSON output. Retrying...\nRaw: {raw_pred}"
                print(err)
                logs.append(err)
                continue

            # 5. Execution Logic
            if action_dict.get("is_finished", False):
                msg = f"✅ Task Complete. Result: {action_dict.get('value', '')}"
                print(msg)
                logs.append(msg)
                yield {"screenshot": processed_img, "log": "\n".join(logs), "done": True}
                return

            element_id = str(action_dict.get("element_id", "0"))
            # cleanup weird strings
            if element_id.lower() in ["none", "null", "nan", "undefined"]: element_id = "0"
            
            action_type = action_dict.get("action", "").lower()
            value = action_dict.get("value", "")

            # Log the parsed action
            action_msg = f"🤖 Action: {action_type} on ID {element_id} ({value})"
            logs.append(action_msg)
            yield {"screenshot": processed_img, "log": "\n".join(logs), "done": False}

            # 6. Validation & Execution
            valid_ids = self._get_valid_ids_from_dom(distilled_dom)

            # Case: Not in DOM (Hallucination)
            if element_id != "0" and action_type != "scroll" and element_id not in valid_ids:
                warn = f"⚠️ Hallucination: ID {element_id} not visible. Retrying..."
                print(warn)
                logs.append(warn)
                continue 

            # Case: Scroll
            if element_id == "0" or action_type == "scroll":
                logs.append("📜 Scrolling down...")
                self.browser.scroll("down")
                time.sleep(2)
                continue

            # Case: Execute
            success = self.browser.execute_action(action_type, element_id, value)
            if not success:
                logs.append("⚠️ Browser action failed.")
            
            time.sleep(2)

        fail_msg = "❌ Max steps reached."
        print(fail_msg)
        logs.append(fail_msg)
        yield {"screenshot": processed_img, "log": "\n".join(logs), "done": True}