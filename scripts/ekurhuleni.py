from datetime import datetime
import os
import re
import requests
from playwright.async_api import Playwright, async_playwright, expect
from dotenv import load_dotenv
from apintegrations.email import send_latest_bill_to_email
from config.secrets import get_secret
from pathlib import Path
load_dotenv()

username = get_secret("EKU_USER")
password = get_secret("EKU_PASS")
link = "https://siyakhokha.ekurhuleni.gov.za/"
if not username or not password:
    raise SystemExit("EKU_USER and EKU_PASS must be set")
current_date = datetime.now().strftime("%Y-%m-%d")

async def run(playwright: Playwright) -> None:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(accept_downloads=True)
    page = await context.new_page()
    await page.goto(link)
    await page.get_by_role("link", name="Log In").click()
    await page.locator("#UserName").click()
    await page.locator("#UserName").click()
    await page.locator("#UserName").fill(username)
    await page.get_by_label("Password").click()
    await page.get_by_label("Password").fill(password)
    await page.get_by_role("button", name="Log in").click()
    await page.get_by_role("link", name="Municipal Services").click()
    await page.get_by_role("link", name="View/ Pay Municipal Bills").first.click()
    
    year_month = datetime.now().strftime("%Y-%m")
    
    async with page.expect_popup() as popup_info:
        await page.get_by_role("row").filter(has_text=year_month).first.get_by_role("link").first.click()
    
    doc_page = await popup_info.value
    await doc_page.wait_for_load_state("domcontentloaded")
    doc_url = doc_page.url
    print(f"Document URL captured: {doc_url}")
    await doc_page.close()
    
    print("Downloading file...")
    response = requests.get(doc_url)
    response.raise_for_status()
    
    temp_dir = Path.cwd() / "temp"
    temp_dir.mkdir(exist_ok=True)
    
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

            print("Begin send file via email...")
            isSuccessful = await send_latest_bill_to_email(save_path)
            if isSuccessful:
                print("File sent successfully via email.")
            else:
                print("Failed to send the file via email.")

            # TODO - Think about backing up file to Google drive folder
        
    except Exception as e:
        print("Failed to download the file:", e)
        raise e
    finally:
        try:
            await doc_page.close()
            # delete temp file
            os.remove(save_path)
            print("Temp file deleted")
            await context.close()
            await browser.close()
        except Exception:
            pass
        
