import asyncio
import os
from playwright.async_api import async_playwright
from scripts.ekurhuleni import run
from postgres_connector import log_to_db
from scripts.constants import Process_Names
import time

async def main():
    run_id = int(os.getenv("GITHUB_RUN_ID", time.time()))
    process_name = Process_Names.Automation_Apps_Ekurhuleni.value
    try:
        async with async_playwright() as playwright:
            await run(playwright)
        log_to_db(run_id, process_name, True, "Successfully completed.")
        
    except Exception as e:
        log_to_db(run_id, process_name, False, f"Failed with error: {e}")
        raise # re-raise the exception after logging

if __name__ == "__main__":
    asyncio.run(main())
