import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from scripts.ekurhuleni import run
from postgres_connector import log_to_db, bill_already_retrieved
from apintegrations.email import send_final_attempt_failure_email
from scripts.constants import Process_Names
import time

async def main():
    run_id = int(os.getenv("GITHUB_RUN_ID", time.time()))
    process_name = Process_Names.Automation_Apps_Ekurhuleni.value
    year_month = datetime.now().strftime("%Y-%m")
    final_attempt = os.getenv("FINAL_ATTEMPT") == "true"

    # Checked on every run, not only the 25th: a manual dispatch after a successful month
    # would otherwise re-email the statement and then die on the Drive duplicate check.
    if bill_already_retrieved(process_name):
        log_to_db(run_id, process_name, True, f"Skipped: bill for {year_month} already retrieved this month.")
        return

    try:
        async with async_playwright() as playwright:
            downloaded = await run(playwright)

        if downloaded:
            log_to_db(run_id, process_name, True, "Successfully completed.")
        elif final_attempt:
            log_to_db(run_id, process_name, False, f"Bill for {year_month} still not published on final attempt.")
            await send_final_attempt_failure_email(year_month)
            raise SystemExit(1)
        else:
            log_to_db(run_id, process_name, False, f"Bill for {year_month} not yet published; will retry on the 25th.")

    except Exception as e:
        log_to_db(run_id, process_name, False, f"Failed with error: {e}")
        raise # re-raise the exception after logging

if __name__ == "__main__":
    asyncio.run(main())
