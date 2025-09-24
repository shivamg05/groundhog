from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

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
