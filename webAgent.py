from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import sys

class WebAgent:
    def __init__(self, headless=False):
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    def go_to_url(self, url, wait_for="body"):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
        )   

    def take_screenshot(self, path="screenshot.png"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        success = self.driver.save_screenshot(path)
        if success:
            print(f"[Screenshot saved to: {path}]")
        else:
            print(f"[❌ Failed to save screenshot to: {path}]")
    
    def click_element(self, css_selector, wait_for="body"):
        try:
            # Handle :contains("text")
            if ":contains(" in css_selector:
                tag, text = css_selector.split(":contains(")
                text = text.strip(")").strip("'\"")
                elements = self.driver.find_elements(By.CSS_SELECTOR, tag or "*")
                for el in elements:
                    if text in el.text:
                        el.click()
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                        )
                        return
                raise Exception(f"No element with text '{text}' found for selector '{css_selector}'.")

            # Handle :eq(n)
            elif ":eq(" in css_selector:
                tag, index = css_selector.split(":eq(")
                index = int(index.strip(")"))
                elements = self.driver.find_elements(By.CSS_SELECTOR, tag or "*")
                elements[index].click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )
                return

            # Handle :first
            elif css_selector.endswith(":first"):
                tag = css_selector.replace(":first", "")
                elements = self.driver.find_elements(By.CSS_SELECTOR, tag or "*")
                elements[0].click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )
                return

            # Handle :last
            elif css_selector.endswith(":last"):
                tag = css_selector.replace(":last", "")
                elements = self.driver.find_elements(By.CSS_SELECTOR, tag or "*")
                elements[-1].click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )
                return

            # Regular CSS selector
            else:
                element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
                element.click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )

        except Exception as e:
            print(f"[Click Failed] {e}")
    
    def type_into_element(self, css_selector, text, wait_for="body"):
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, css_selector)
            element.clear()
            element.send_keys(text)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
            )
        except Exception as e:
            print(f"[Typing Failed] {e}")

    def quit(self):
        self.driver.quit()

    def get_page_snapshot(self, include_hidden=False, max_elements=150):
        tags = ["a", "button", "input", "textarea", "select", "div", "span", "p", "h1", "h2", "h3", "li", "strong", "em"]
        snapshot = []

        for tag in tags:
            elements = self.driver.find_elements(By.TAG_NAME, tag)
            for el in elements:
                try:
                    if not include_hidden and not el.is_displayed():
                        continue

                    text = el.text.strip()
                    if not text and tag not in ["input", "textarea", "select", "button"]:
                        continue

                    selector = self._build_selector(el)
                    snapshot.append({
                        "tag": tag,
                        "text": text,
                        "selector": selector
                    })

                    if len(snapshot) >= max_elements:
                        print(snapshot)
                        return snapshot
                except Exception:
                    continue
    
        print(snapshot)
        sys.stdout.flush()

        return snapshot

    def _build_selector(self, element: WebElement) -> str:
        tag = element.tag_name
        el_id = element.get_attribute("id")
        el_class = element.get_attribute("class")

        if el_id:
            return f"{tag}#{el_id}"
        elif el_class:
            classes = ".".join(el_class.strip().split())
            return f"{tag}.{classes}"
        else:
            return tag
