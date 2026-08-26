from datetime import datetime
import os
import re
import requests
from playwright.async_api import Playwright, async_playwright, expect
from dotenv import load_dotenv
from apintegrations.email import send_latest_bill_to_email
from apintegrations.gdrive import upload_to_drive
from config.secrets import get_secret
from pathlib import Path
load_dotenv()

username = get_secret("EKU_USER")
password = get_secret("EKU_PASS")
link = "https://siyakhokha.ekurhuleni.gov.za/"
if not username or not password:
    raise SystemExit("EKU_USER and EKU_PASS must be set")
current_date = datetime.now().strftime("%Y-%m-%d")

async def run(playwright: Playwright) -> bool:
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

    temp_dir = Path.cwd() / "temp"
    temp_dir.mkdir(exist_ok=True)
    save_path = None
    
    try:
        await page.get_by_role("row").nth(1).wait_for()

        current_month_bill = page.get_by_role("row").filter(has_text=year_month)
        if await current_month_bill.count() == 0:
            print(f"Bill for {year_month} has not been published yet.")
            return False

        async with page.expect_download() as download_info:
            await current_month_bill.first.get_by_role("link").first.click()
        download = await download_info.value

        filename = f"EkurhuleniStatement-{year_month}.pdf"
        save_path = temp_dir / filename
        await download.save_as(save_path)
        print(f"Saved PDF to: {save_path}")

        print("Begin send file via email...")
        isSuccessful = await send_latest_bill_to_email(str(save_path))
        if not isSuccessful:
            raise RuntimeError("Failed to send the statement via email.")
        print("File sent successfully via email.")

        upload_to_drive(save_path)

        return True

    except Exception as e:
        print("Failed to download the file:", e)
        raise e
    finally:
        try:
            if save_path and save_path.exists():
                save_path.unlink()
                print("Temp file deleted")
        except Exception as e:
            print(f"Error during cleanup of temp file: {e}")
        
        await context.close()
        await browser.close()
        
        
