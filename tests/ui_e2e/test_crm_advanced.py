import random
import time
from playwright.sync_api import expect
from tests.ui_e2e.pages.crm_page import CrmPage


def _create_test_lead(crm, auth_page):
    """Helper: create a lead and return its phone number."""
    test_phone = f"+91{random.randint(1000000000, 9999999999)}"
    crm.click_add_lead()
    crm.fill_and_submit_lead("E2E", "ModalTest", test_phone)
    expect(crm.get_lead_row(test_phone)).to_be_visible(timeout=10000)
    return test_phone


def test_transcript_modal_opens(auth_page, base_url):
    """Test that clicking Transcript button on a lead opens the TranscriptModal."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = _create_test_lead(crm, auth_page)
    time.sleep(1)

    # Click the Transcript button on the lead row
    row = crm.get_lead_row(test_phone)
    row.locator("button:has-text('Transcript')").click()
    time.sleep(1)

    # Verify TranscriptModal opens with the expected heading
    expect(
        auth_page.get_by_text("Call Transcripts")
    ).to_be_visible(timeout=8000)

    # Verify empty state for a fresh lead
    expect(
        auth_page.get_by_text("No call transcripts yet")
    ).to_be_visible(timeout=8000)

    # Clean up: close the modal and delete the lead
    auth_page.keyboard.press("Escape")
    time.sleep(1)
    crm.delete_lead(test_phone)


def test_document_vault_opens(auth_page, base_url):
    """Test that clicking Docs button on a lead opens the Document Vault modal."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = _create_test_lead(crm, auth_page)
    time.sleep(1)

    # Click the Docs button on the lead row
    row = crm.get_lead_row(test_phone)
    row.locator("button:has-text('Docs')").click()
    time.sleep(1)

    # Verify Document Vault modal opens
    expect(
        auth_page.get_by_text("Document Vault")
    ).to_be_visible(timeout=8000)

    # Clean up: close the modal and delete the lead
    auth_page.keyboard.press("Escape")
    time.sleep(1)
    crm.delete_lead(test_phone)


def test_note_modal(auth_page, base_url):
    """Test that clicking Note button on a lead shows the note input area."""
    crm = CrmPage(auth_page, base_url)
    crm.navigate_with_cache_bust()
    time.sleep(2)

    test_phone = _create_test_lead(crm, auth_page)
    time.sleep(1)

    # Click the Note button on the lead row
    row = crm.get_lead_row(test_phone)
    row.locator("button:has-text('Note')").click()
    time.sleep(1)

    # Verify a textarea or input for notes appears
    note_input = auth_page.locator("textarea").first
    alt_input = auth_page.locator("input[placeholder*='note' i]").first
    # At least one note input element should be visible
    expect(note_input.or_(alt_input)).to_be_visible(timeout=8000)

    # Clean up: close anything open and delete the lead
    auth_page.keyboard.press("Escape")
    time.sleep(1)
    crm.delete_lead(test_phone)
