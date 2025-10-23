from datetime import datetime
import os
import re
import requests
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv("EKU_USER")
PASSWORD = os.getenv("EKU_PASS")
if not USERNAME or not PASSWORD:
    raise SystemExit("EKU_USER and EKU_PASS must be set")
current_date = datetime.now().strftime("%Y-%m-%d")

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()
    page.goto("https://siyakhokha.ekurhuleni.gov.za/")
    page.get_by_role("link", name="Log In").click()
    page.locator("#UserName").click()
    page.locator("#UserName").click()
    page.locator("#UserName").fill("<redacted>")
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("<redacted>")
    page.get_by_role("button", name="Log in").click()
    page.get_by_role("link", name="Municipal Services").click()
    page.get_by_role("link", name="View/ Pay Municipal Bills").first.click()
    
    year_month = datetime.now().strftime("%Y-%m")
    
    with page.expect_popup() as popup_info:
        page.get_by_role("row").filter(has_text=year_month).first.get_by_role("link").first.click()
    
    doc_page = popup_info.value
    doc_page.wait_for_load_state()
    doc_url = doc_page.url
    print(f"Document URL captured: {doc_url}")
    doc_page.close()
    
    print("Downloading file...")
    response = requests.get(doc_url)
    response.raise_for_status()
    
    temp_dir = r"C:\Temp"
    
    try:
        resp = context.request.get(doc_url, timeout=60 * 1000)
        ct = resp.headers.get("content-type", "")
        # If direct PDF, save it
        if "application/pdf" in ct.lower():
            data = resp.body()
            filename = f"EkurhuleniStatement-{year_month}.pdf"
            save_path = os.path.join(temp_dir, filename)
            with open(save_path, "wb") as fh:
                fh.write(data)
            print("Saved PDF from direct request to:", save_path)
    except Exception as e:
        print("Failed to download the file:", e)
        raise e
    finally:
        try:
            doc_page.close()
        except Exception:
            pass
        
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)