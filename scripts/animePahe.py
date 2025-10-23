import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://siyakhokha.ekurhuleni.gov.za/?AspxAutoDetectCookieSupport=1")
    page.get_by_role("link", name="Log In").click()
    page.locator("#UserName").click()
    page.locator("#UserName").fill("<redacted>")
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("<redacted>")
    page.get_by_role("button", name="Log in").click()
    page.get_by_role("link", name="Municipal Services").click()
    page.get_by_role("link", name="View/ Pay Municipal Bills", exact=True).click()
    with page.expect_popup() as page1_info:
        page.get_by_role("row", name="2025-10-15 R3000.00").get_by_role("link").first.click()
    page1 = page1_info.value
    page.get_by_role("row", name="2025-10-15 R3000.00").locator("div").first.click()
    page.get_by_role("cell", name="-10-15").click()
    page.get_by_role("row", name="2025-07-18 R2386.00").locator("div").first.click()
    page1.close()
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
