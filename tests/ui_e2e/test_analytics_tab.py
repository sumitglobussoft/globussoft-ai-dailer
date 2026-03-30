import time
from playwright.sync_api import expect


def test_analytics_tab_loads(auth_page, base_url):
    """Test that the Analytics tab loads and shows the main heading."""
    auth_page.goto(f"{base_url}?_cb={int(time.time())}")
    time.sleep(2)

    auth_page.locator('button:has-text("Analytics")').first.click()
    auth_page.wait_for_load_state("networkidle")
    time.sleep(1)

    expect(
        auth_page.get_by_text("Executive Data Analytics")
    ).to_be_visible(timeout=8000)


def test_analytics_chart_visible(auth_page, base_url):
    """Test that the bar chart area with Call Volume vs. Deals Closed is visible."""
    auth_page.goto(f"{base_url}?_cb={int(time.time())}")
    time.sleep(2)

    auth_page.locator('button:has-text("Analytics")').first.click()
    auth_page.wait_for_load_state("networkidle")
    time.sleep(1)

    expect(
        auth_page.get_by_text("Call Volume vs. Deals Closed")
    ).to_be_visible(timeout=8000)
