from web_agent import WebAgent
from agent_logic import get_next_action

# agent = WebAgent()
# agent.go_to_url("https://books.toscrape.com", "div.page_inner")
# agent.take_screenshot("data/task1/step1_homepage.png")
# agent.click_element(".product_pod h3 a", "div.page_inner")
# agent.take_screenshot("data/task1/step2_book_detail.png")
# agent.quit()

agent = WebAgent()
agent.go_to_url("https://books.toscrape.com", "div.page_inner")

goal = "Find the rating of the first Mystery book"
count = 0

while True:
    screenshot_path = f"data/task1/step{count}.png"
    agent.take_screenshot(screenshot_path)
    snapshot = agent.get_page_snapshot()

    action_info = get_next_action(screenshot_path, goal, snapshot)

    finished = agent.act(action_info, "div.page_inner")

    count+=1

    if finished:
        agent.quit()
        break