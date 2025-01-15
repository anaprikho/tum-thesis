import os
import time
import csv
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

### Option for pausing while scraping:
# page.wait_for_selector(".some-element", timeout=3000)
# page.wait_for_timeout(2000)
# time.sleep(2)

def get_usernames_by_keyword(page, keyword, post_limit=None):
    # Global search on HU using a keyword
    page.goto("https://healthunlocked.com/")
    page.fill("input[placeholder='Search HealthUnlocked']", keyword)
    page.keyboard.press("Enter")
    time.sleep(2)
    print(f"-------- Keyword: {keyword} --------")

    # Track post count per user: {"user1": 3, "user2": 5, "user3": 1}
    user_post_count= {}

    while True:
        post_elements = page.locator("a[data-sentry-element='Link'][href^='/user/']").all()

        for post in post_elements:
            username = post.text_content().strip()
            if username:
                if username in user_post_count:
                    user_post_count[username] += 1
                else:
                    user_post_count[username] = 1
            
            # Stop collection if the limit is reached (on current page)
            if post_limit and len(user_post_count) >= post_limit:
                break
            
        # Stop collection if the limit is reached (entire page processing)
        if post_limit and len(user_post_count) >= post_limit:
            print(f"Reached limit of {post_limit} usernames -> stop pagination.")
            break

        # Pagination
        next_button = page.locator("text=Next page")
        if next_button.count() > 0 and next_button.is_visible():
            print("Pagination: Moving to the next page...")
            page.wait_for_selector("text=Next page", timeout=2000)
            next_button.click()
            # page.wait_for_timeout(2000)
            # try:
            #     current_url = page.url
            #     next_button.click(timeout=10000)
            #     page.wait_for_load_state("domcontentloaded")
            #     # Verify page change
            #     if page.url == current_url:
            #         print("Next page did not load. Exiting pagination.")
            #         break
            # except TimeoutError:
            #     print("Pagination failed. Exiting pagination loop.")
            #     break
        else:
            print("No more pages to navigate.")
            break
    
    # Convert dictionary to a list of dictionaries
    usernames_data = [{"username": user, "keyword": keyword, "post_count": count} 
        for user, count in user_post_count.items()]
    return usernames_data

# Helper: Login
def login(page):
    # Load environment variables
    load_dotenv()
    EMAIL = os.getenv("EMAIL")
    PASSWORD = os.getenv("PASSWORD")

    # Open the login page
    page.goto("https://healthunlocked.com/login")
    page.wait_for_timeout(3000)  # = 1 sec

    # Accept cookies
    page.click("#ccc-notify-accept")
    page.wait_for_timeout(2000)

    # Enter login credentials
    page.fill("#email", EMAIL)
    page.fill("#password", PASSWORD)

    # Ensure the login button is visible and enabled, then click it
    page.wait_for_selector("button[data-testid='log-in-button']", timeout=5000)  
    page.click("button[data-testid='log-in-button']")  
    page.wait_for_timeout(2000)  # Wait for login to complete

    print("Login successful.")

# Helper: Save
def save_to_csv(filename, data, headers):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        print(f"Saved to file {filename}")

# Main
with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)  # True - for headless mode
    page = browser.new_page()

    try:
        login(page)

        ### Part 1: General Patterns

        # Step 1: Collect Usernames from Posts using a Keyword
        keywords = ["depression", "anxiety"]
        usernames_data = []
        for keyword in keywords:
            usernames_data.extend(get_usernames_by_keyword(page, keyword, post_limit=70))
        save_to_csv("usernames_data.csv", usernames_data, ["username", "keyword", "post_count"])

        # Step 2: Collect User Profiles
        # Step 3: Create Unique Community List

    finally:
        browser.close()

