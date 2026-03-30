from playwright.sync_api import expect
from tests.ui_e2e.pages.base_page import BasePage


class AuthPage(BasePage):
    def login(self, email, password):
        self.page.goto(self.base_url)
        # Click Login tab if not already active
        self.page.locator(".tab-btn:has-text('Login')").click()
        self.page.fill('input[type="email"]', email)
        self.page.fill('input[type="password"]', password)
        self.page.locator("button.btn-primary:has-text('Login')").click()

    def check_login_success(self):
        # After login, the top header with logout button should appear
        expect(self.page.locator("button:has-text('Logout')")).to_be_visible(timeout=10000)

    def signup(self, org_name, full_name, email, password):
        self.page.goto(self.base_url)
        # Click Sign Up tab
        self.page.locator(".tab-btn:has-text('Sign Up')").click()
        self.page.fill('input[placeholder="e.g. Globussoft"]', org_name)
        self.page.fill('input[placeholder="e.g. Sumit Kumar"]', full_name)
        self.page.fill('input[type="email"]', email)
        self.page.fill('input[type="password"]', password)
        self.page.locator("button.btn-primary:has-text('Create Account')").click()

    def logout(self):
        self.page.locator("button:has-text('Logout')").click()
        expect(self.page.locator('input[type="email"]')).to_be_visible(timeout=5000)
