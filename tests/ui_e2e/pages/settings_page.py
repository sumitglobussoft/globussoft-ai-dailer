from playwright.sync_api import expect
from tests.ui_e2e.pages.base_page import BasePage


class SettingsPage(BasePage):
    def go_to_settings(self):
        self.switch_tab("Settings")

    def add_product(self, product_name):
        self.page.locator("button:has-text('+ Add Product')").click()
        self.page.fill('input[placeholder*="Product name"]', product_name)
        self.page.locator("button:has-text('Add')").first.click()

    def get_product(self, product_name):
        return self.page.locator(f"div:has-text('{product_name}')")

    def delete_product(self, product_name):
        self.page.once("dialog", lambda dialog: dialog.accept())
        product = self.get_product(product_name)
        product.locator("button:has-text('Remove')").first.click()

    def add_pronunciation_rule(self, word, phonetic):
        self.page.fill('input[placeholder="e.g. Adsgpt"]', word)
        self.page.fill('input[placeholder="e.g. Ads G P T"]', phonetic)
        self.page.locator("button:has-text('+ Add Rule')").click()

    def delete_pronunciation_rule(self, word):
        row = self.page.locator(f"tr:has-text('{word}')")
        row.locator("button:has-text('Remove')").click()
