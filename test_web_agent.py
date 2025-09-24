from web_agent import WebAgent
from agent_logic import get_next_action

agent = WebAgent()

goals = ["Find the rating of the first Mystery book", "Find the last book on the first page. The page is scrollable."]
goal_count = 0

for goal in goals:

    agent.go_to_url("https://books.toscrape.com", "div.page_inner")

    step_count = 0
    while True:
        screenshot_path = f"data/task{goal_count}/step{step_count}.png"
        agent.take_screenshot(screenshot_path)
        snapshot = agent.get_page_snapshot()

        action_info = get_next_action(screenshot_path, goal, snapshot)

        finished = agent.act(action_info, "div.page_inner")

        step_count+=1

        if finished:
            break
    
    goal_count+=1

agent.quit()
