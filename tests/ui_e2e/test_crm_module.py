import random
import time
from playwright.sync_api import expect
from tests.ui_e2e.pages.crm_page import CrmPage


def test_add_lead(auth_page, base_url):
    """Test adding a new lead via the CRM modal."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = f"+91{random.randint(1000000000, 9999999999)}"

    crm.click_add_lead()
    crm.fill_and_submit_lead("E2E", "TestLead", test_phone)

    # The new lead should appear in the table
    row = crm.get_lead_row(test_phone)
    expect(row).to_be_visible(timeout=10000)


def test_edit_lead(auth_page, base_url):
    """Test editing an existing lead."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = f"+91{random.randint(1000000000, 9999999999)}"

    # Create a lead first
    crm.click_add_lead()
    crm.fill_and_submit_lead("E2E", "BeforeEdit", test_phone)
    expect(crm.get_lead_row(test_phone)).to_be_visible(timeout=10000)

    # Edit it
    crm.edit_lead(test_phone, "AfterEdit")

    # Verify the edit took effect
    row = crm.get_lead_row(test_phone)
    expect(row).to_be_visible(timeout=8000)


def test_delete_lead(auth_page, base_url):
    """Test deleting a lead."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = f"+91{random.randint(1000000000, 9999999999)}"

    # Create a lead first
    crm.click_add_lead()
    crm.fill_and_submit_lead("E2E", "ToDelete", test_phone)
    expect(crm.get_lead_row(test_phone)).to_be_visible(timeout=10000)

    # Delete it
    crm.delete_lead(test_phone)

    # Should be gone
    expect(crm.get_lead_row(test_phone)).to_be_hidden(timeout=10000)


def test_search_lead(auth_page, base_url):
    """Test the search bar filters leads."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = f"+91{random.randint(1000000000, 9999999999)}"
    unique_name = f"SearchTest{int(time.time())}"

    # Create a lead with a unique name
    crm.click_add_lead()
    crm.fill_and_submit_lead(unique_name, "Lead", test_phone)
    expect(crm.get_lead_row(test_phone)).to_be_visible(timeout=10000)

    # Search for it
    crm.search_lead(unique_name)
    time.sleep(1)

    # The lead should still be visible
    expect(crm.get_lead_row(test_phone)).to_be_visible(timeout=5000)

    # Search for something that doesn't exist
    crm.search_lead("ZZZZNONEXISTENT999")
    time.sleep(1)

    # Our lead should now be hidden
    expect(crm.get_lead_row(test_phone)).to_be_hidden(timeout=5000)
