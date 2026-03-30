import os
import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("E2E_BASE_URL", "https://test.callified.ai")
TEST_SESSION_ID = int(time.time())
TEST_USER_EMAIL = os.getenv("E2E_USER_EMAIL", f"e2esession_{TEST_SESSION_ID}@globussoft.com")
TEST_USER_PW = os.getenv("E2E_USER_PASSWORD", "AutoTest!2026")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def auth_context(browser, base_url):
    """
    Creates a new browser context, signs up a fresh user, and returns the
    authenticated context.
    """
    context = browser.new_context(base_url=base_url, viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.goto("/")

    # Wait for React app to render
    page.wait_for_selector('input[type="email"]', timeout=15000)

    if page.is_visible('input[type="email"]'):
        # Click Sign Up tab and register
        page.locator(".tab-btn:has-text('Sign Up')").click()
        page.fill('input[placeholder="e.g. Globussoft"]', "Automated Testing Org")
        page.fill('input[placeholder="e.g. Sumit Kumar"]', "Automated Tester")
        page.fill('input[type="email"]', TEST_USER_EMAIL)
        page.fill('input[type="password"]', TEST_USER_PW)
        page.locator("button.btn-primary:has-text('Create Account')").click()
        # Wait for dashboard to load (logout button means we're in)
        page.wait_for_selector("button:has-text('Logout')", timeout=15000)

    yield context
    context.close()


@pytest.fixture
def auth_page(auth_context):
    """
    Yields a page object that is already authenticated.
    """
    page = auth_context.new_page()
    yield page
    page.close()
