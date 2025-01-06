from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import time

load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def collect_usernames(page):
    usernames = []
    while len(usernames) < 50:
        # Collect usernames on the current page
        time.sleep(1) # Actually, playwright automatically waits for elements (built-in waits)
        username_elements = page.locator(".community-member-card__username").all()
        
        for element in username_elements:
            username = element.inner_text()
            if username and username not in usernames:
                usernames.append(username)
                if len(usernames) >= 50:
                    break
        
        # Pagination
        next_button = page.locator("text=Next page")
        if next_button.count() > 0:
            next_button.click()
        else:
            print("No more pages to navigate.")
            break

    return usernames

# Main script
with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # True - for headless mode
    page = browser.new_page()

    try:
        # Open the login page
        page.goto("https://healthunlocked.com/login")
        page.wait_for_timeout(1000)  # = 1 sec

        # Accept cookies button
        page.click("#ccc-notify-accept")

        # Enter login credentials
        page.fill("#email", EMAIL)
        page.fill("#password", PASSWORD)
        page.click("button[data-testid='log-in-button']")
        page.wait_for_timeout(2000)  # Wait for login to complete

        # Navigate to the members page
        page.goto("https://healthunlocked.com/anxiety-depression-support/members")
        page.wait_for_timeout(1000)  # Wait for the page to load

        # Click 'Most contributions' button
        page.click("text=Most contributions")
        page.wait_for_timeout(2000)

        # Collect usernames
        usernames = collect_usernames(page)

        # Print the collected usernames
        print("Collected Usernames:")
        for username in usernames:
            print(username)
        print("Number of elements found:", len(usernames))

    finally:
        browser.close()