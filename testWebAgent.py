from webAgent import WebAgent
from agent_logic import get_next_action

# agent = WebAgent()
# agent.go_to_url("https://books.toscrape.com", "div.page_inner")
# agent.take_screenshot("data/task1/step1_homepage.png")
# agent.click_element(".product_pod h3 a", "div.page_inner")
# agent.take_screenshot("data/task1/step2_book_detail.png")
# agent.quit()

agent = WebAgent()
agent.go_to_url("https://books.toscrape.com", "div.page_inner")

screenshot_path = "data/task1/step1.png"
agent.take_screenshot(screenshot_path)
snapshot = agent.get_page_snapshot()

goal = "Find the rating of the first Mystery book"
action_info = get_next_action(screenshot_path, goal, snapshot)
print(action_info)


agent.click_element("a:contains('Mystery')", "div.page_inner")
agent.take_screenshot("data/task1/step2.png")
snapshot2 = agent.get_page_snapshot()
action_info = get_next_action("data/task1/step2.png", goal, snapshot2)
print(action_info)

agent.quit()