import time
from playwright.sync_api import expect
from tests.ui_e2e.pages.base_page import BasePage


class AuthPage(BasePage):
    def _navigate_with_cache_bust(self):
        self.page.goto(f"{self.base_url}?_cb={int(time.time())}")

    def login(self, email, password):
        self._navigate_with_cache_bust()
        self.page.wait_for_selector('input[type="email"]', timeout=15000)
        self.page.locator("button:has-text('Login')").first.click()
        self.page.fill('input[type="email"]', email)
        self.page.fill('input[type="password"]', password)
        self.page.locator("button.btn-primary").click()

    def check_login_success(self):
        expect(self.page.locator("button:has-text('Logout')")).to_be_visible(timeout=15000)

    def signup(self, org_name, full_name, email, password):
        self._navigate_with_cache_bust()
        self.page.wait_for_selector('input[type="email"]', timeout=15000)
        self.page.locator("button:has-text('Sign Up')").first.click()
        self.page.wait_for_selector('input[placeholder="e.g. Globussoft"]', timeout=5000)
        self.page.fill('input[placeholder="e.g. Globussoft"]', org_name)
        self.page.fill('input[placeholder="e.g. Sumit Kumar"]', full_name)
        self.page.fill('input[type="email"]', email)
        self.page.fill('input[type="password"]', password)
        self.page.locator("button.btn-primary").click()

    def logout(self):
        self.page.locator("button:has-text('Logout')").click()
        expect(self.page.locator('input[type="email"]')).to_be_visible(timeout=5000)
