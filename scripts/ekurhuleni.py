from datetime import datetime
import os
import re
import requests
from playwright.async_api import Playwright, async_playwright, expect
from dotenv import load_dotenv
from apintegrations.whatsapp import send_latest_bill_via_whatsapp
load_dotenv()

USERNAME = os.getenv("EKU_USER")
PASSWORD = os.getenv("EKU_PASS")
if not USERNAME or not PASSWORD:
    raise SystemExit("EKU_USER and EKU_PASS must be set")
current_date = datetime.now().strftime("%Y-%m-%d")

async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()
    await page.goto("https://siyakhokha.ekurhuleni.gov.za/")
    await page.get_by_role("link", name="Log In").click()
    await page.locator("#UserName").click()
    await page.locator("#UserName").click()
    await page.locator("#UserName").fill(USERNAME)
    await page.get_by_label("Password").click()
    await page.get_by_label("Password").fill(PASSWORD)
    await page.get_by_role("button", name="Log in").click()
    await page.get_by_role("link", name="Municipal Services").click()
    await page.get_by_role("link", name="View/ Pay Municipal Bills").first.click()
    
    year_month = datetime.now().strftime("%Y-%m")
    
    async with page.expect_popup() as popup_info:
        await page.get_by_role("row").filter(has_text=year_month).first.get_by_role("link").first.click()
    
    doc_page = await popup_info.value
    await doc_page.wait_for_load_state()
    doc_url = doc_page.url
    print(f"Document URL captured: {doc_url}")
    await doc_page.close()
    
    print("Downloading file...")
    response = requests.get(doc_url)
    response.raise_for_status()
    
    temp_dir = r"C:\Temp\EkurhuleniStatements"
    
    try:
        resp = await context.request.get(doc_url, timeout=60 * 1000)
        ct = resp.headers.get("content-type", "")
        # If direct PDF, save it
        if "application/pdf" in ct.lower():
            data = await resp.body()
            filename = f"EkurhuleniStatement-{year_month}.pdf"
            save_path = os.path.join(temp_dir, filename)
            with open(save_path, "wb") as fh:
                fh.write(data)
            print("Saved PDF from direct request to:", save_path)

            print("Begin send file via Whatsapp")
            isSuccessful = await send_latest_bill_via_whatsapp(save_path)

            # Why not try save the file to Google Drive here?
        
    except Exception as e:
        print("Failed to download the file:", e)
        raise e
    finally:
        try:
            doc_page.close()
            # delete temp file
            os.remove(save_path)
            print("Temp file deleted")
        except Exception:
            pass
        
    context.close()
    browser.close()
