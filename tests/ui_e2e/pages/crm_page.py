from playwright.sync_api import expect
from tests.ui_e2e.pages.base_page import BasePage


class CrmPage(BasePage):
    def navigate_to_tab(self):
        self.switch_tab("CRM")

    def click_add_lead(self):
        self.page.locator("button:has-text('+ Add Lead')").click()
        # Wait for the modal to appear
        self.page.wait_for_selector(".modal-overlay", timeout=5000)

    def fill_and_submit_lead(self, first_name, last_name, phone):
        self.page.fill('input[placeholder="e.g. John"]', first_name)
        self.page.fill('input[placeholder="e.g. Doe"]', last_name)
        self.page.fill('input[placeholder="+917406317771"]', phone)
        self.page.locator("button.btn-primary:has-text('Save Lead')").click()

    def get_lead_row(self, phone):
        return self.page.locator(f"tr:has-text('{phone}')")

    def edit_lead(self, phone, new_last_name):
        row = self.get_lead_row(phone)
        row.locator("button:has-text('Edit')").click()
        # Wait for Edit Lead modal
        self.page.wait_for_selector("h2:has-text('Edit Lead')", timeout=5000)
        # Edit modal inputs use name attributes, not placeholders
        last_name_input = self.page.locator(".modal-overlay input[name='last_name']")
        last_name_input.fill(new_last_name)
        self.page.locator("button.btn-primary:has-text('Update Lead')").click()

    def delete_lead(self, phone):
        row = self.get_lead_row(phone)
        self.page.once("dialog", lambda dialog: dialog.accept())
        row.locator("button:has-text('\U0001f5d1\ufe0f')").click()

    def search_lead(self, query):
        self.page.fill('input[placeholder*="Search Leads"]', query)
