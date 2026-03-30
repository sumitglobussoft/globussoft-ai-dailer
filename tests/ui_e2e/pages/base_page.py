from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url

    def navigate(self, path: str = "/"):
        self.page.goto(f"{self.base_url}{path}")

    def get_by_testid(self, testid: str):
        return self.page.get_by_test_id(testid)

    def switch_tab(self, tab_text: str):
        self.page.locator(f'.tab-btn:has-text("{tab_text}")').click()
        self.page.wait_for_load_state("networkidle")
