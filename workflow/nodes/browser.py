# Node: open the page and read its real elements, so the AI doesn't have to guess

from playwright.sync_api import sync_playwright

from workflow.state import TestState


def read_page(state: TestState):
    print(f"Opening {state['app_url']} to read the real page elements")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(state["app_url"])
        snapshot = f"Page title: {page.title()}\n" + page.locator("body").aria_snapshot()
        browser.close()
    return {"page_snapshot": snapshot}
