import time
from playwright.sync_api import expect


def test_ops_tab_loads(auth_page, base_url):
    """Test that the Ops & Tasks tab loads and shows the main heading."""
    auth_page.goto(f"{base_url}?_cb={int(time.time())}")
    time.sleep(2)

    auth_page.locator('button:has-text("Ops & Tasks")').first.click()
    auth_page.wait_for_load_state("networkidle")
    time.sleep(1)

    expect(
        auth_page.get_by_text("Internal Cross-Department Tasks")
    ).to_be_visible(timeout=8000)


def test_ops_metrics_visible(auth_page, base_url):
    """Test that Ops metric cards are visible."""
    auth_page.goto(f"{base_url}?_cb={int(time.time())}")
    time.sleep(2)

    auth_page.locator('button:has-text("Ops & Tasks")').first.click()
    auth_page.wait_for_load_state("networkidle")
    time.sleep(1)

    expect(
        auth_page.get_by_text("Closed Deals")
    ).to_be_visible(timeout=8000)
    expect(
        auth_page.get_by_text("Verified Punches")
    ).to_be_visible(timeout=8000)
    expect(
        auth_page.get_by_text("Pending Tasks")
    ).to_be_visible(timeout=8000)
