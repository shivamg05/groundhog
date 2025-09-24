from webAgent import WebAgent

agent = WebAgent()
agent.go_to_url("https://books.toscrape.com")
agent.take_screenshot("data/task1/step1_homepage.png")
agent.click_element(".product_pod h3 a")
agent.take_screenshot("data/task1/step2_book_detail.png")
agent.quit()