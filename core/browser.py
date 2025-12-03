import os
import time
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

class Browser:
    def __init__(self, headless=False, script_path=None):
        """
        Initializes the Chrome driver and loads the stamping script
        """
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        
        # Standard options to avoid detection/errors
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 10)

        # Load the JS stamper script
        # Default assumption: scripts/stamp_page.js is relative to the project root
        if script_path is None:
            # Resolves to: groundhog_agent/core/../../scripts/stamp_page.js
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "..", "..", "scripts", "stamp_page.js")
        
        if os.path.exists(script_path):
            with open(script_path, "r") as f:
                self.stamper_js = f.read()
        else:
            raise FileNotFoundError(f"Could not find stamp_page.js at {script_path}")

    def navigate(self, url):
        """Goes to a URL and waits for the body to be present."""
        print(f"[Browser] Navigating to {url}...")
        self.driver.get(url)
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)  # Small buffer for dynamic content to settle
        except TimeoutException:
            print("[Browser] Warning: Timeout waiting for page load, proceeding anyway.")

    def capture_state(self):
        """
        1. Injects the JS to stamp IDs (data-m2w-id) and visibility (data-m2w-visible).
        2. Captures the full HTML snapshot.
        3. Captures the screenshot as a PIL Image.
        
        Returns:
            screenshot (PIL.Image): The raw screenshot.
            html (str): The raw HTML string with injected IDs.
        """
        # 1. Inject IDs
        # We execute the script we loaded. It returns the max ID used (useful for debugging)
        max_id = self.driver.execute_script(self.stamper_js)
        print(f"[Browser] Stamped page. Max ID: {max_id}")

        # 2. Get HTML
        # We need the outerHTML of the document element to get the attributes we just added
        raw_html = self.driver.execute_script("return document.documentElement.outerHTML;")

        # 3. Get Screenshot
        # We get it as PNG bytes and convert to PIL Image in memory
        png_data = self.driver.get_screenshot_as_png()
        screenshot = Image.open(io.BytesIO(png_data)).convert("RGB")

        return screenshot, raw_html

    def execute_action(self, action, element_id, value=None):
        """
        Executes an action on a specific element identified by the VLM.
        
        Args:
            action (str): 'click', 'type', 'select'
            element_id (str): The ID assigned by stamp_page.js (e.g., '15')
            value (str): Text to type or option to select.
        """
        if element_id == "0" or element_id is None:
            print(f"[Browser] Action '{action}' on ID 0 (Target Not Found). Logic should be handled by Controller.")
            return False

        try:
            # Find the element using the stamped attribute
            selector = f"[data-m2w-id='{element_id}']"
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            # Scroll into view to ensure interactability
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)

            print(f"[Browser] Executing {action} on Element {element_id} ({element.tag_name})")

            if action == "click":
                element.click()
            
            elif action == "type":
                element.clear()
                element.send_keys(value)
                element.send_keys(Keys.ENTER) # Often helpful to hit enter after typing
            
            elif action == "select":
                # Check if it's a standard <select> tag
                if element.tag_name.lower() == "select":
                    select = Select(element)
                    # Try selecting by text, then value, then index logic could be added
                    try:
                        select.select_by_visible_text(value)
                    except:
                        # Fallback: try selecting by value attribute
                        select.select_by_value(value)
                else:
                    # Non-standard dropdowns (divs/buttons) usually just need a click
                    # The VLM usually predicts a sequence: Click Dropdown -> Click Option.
                    # If it predicted "select" on a div, just clicking might work.
                    element.click()

            time.sleep(1) # Wait for page reaction
            return True

        except NoSuchElementException:
            print(f"[Browser] ❌ Element with data-m2w-id='{element_id}' not found in current DOM.")
            return False
        except ElementNotInteractableException:
            print(f"[Browser] ❌ Element {element_id} found but not interactable.")
            return False
        except Exception as e:
            print(f"[Browser] ❌ Action failed: {e}")
            return False

    def scroll(self, direction="down", amount=None):
        """
        Scrolls the page. 
        Used when the VLM cannot find the target (ID=0) or predicts a scroll action.
        """
        if amount is None:
            # Default to roughly one viewport height
            amount = "window.innerHeight * 0.8"
        else:
            amount = str(amount)

        if direction == "down":
            script = f"window.scrollBy(0, {amount});"
        elif direction == "up":
            script = f"window.scrollBy(0, -{amount});"
        elif direction == "top":
            script = "window.scrollTo(0, 0);"
        elif direction == "bottom":
            script = "window.scrollTo(0, document.body.scrollHeight);"
        
        self.driver.execute_script(script)
        print(f"[Browser] Scrolled {direction}")
        time.sleep(0.5)

    def quit(self):
        self.driver.quit()