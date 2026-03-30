import time
from playwright.sync_api import expect


def test_integrations_tab_loads(auth_page, base_url):
    """Test that the Integrations tab loads and shows the main heading."""
    auth_page.goto(f"{base_url}?_cb={int(time.time())}")
    time.sleep(2)

    auth_page.locator('button:has-text("Integrations")').first.click()
    auth_page.wait_for_load_state("networkidle")
    time.sleep(1)

    expect(
        auth_page.get_by_text("CRM Integrations")
    ).to_be_visible(timeout=8000)


def test_integrations_form_visible(auth_page, base_url):
    """Test that the Add New Connection form and Provider dropdown are visible."""
    auth_page.goto(f"{base_url}?_cb={int(time.time())}")
    time.sleep(2)

    auth_page.locator('button:has-text("Integrations")').first.click()
    auth_page.wait_for_load_state("networkidle")
    time.sleep(1)

    expect(
        auth_page.get_by_text("Add New Connection")
    ).to_be_visible(timeout=8000)

    # Verify the Provider dropdown (select element) is present
    provider_select = auth_page.locator("select").first
    expect(provider_select).to_be_visible(timeout=8000)
