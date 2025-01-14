import os
import time
import csv
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# page.wait_for_selector(".some-element", timeout=3000)

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_usernames_by_keyword(page, keyword, post_limit=None):
    # Global search on HU using a keyword
    page.goto("https://healthunlocked.com/")
    page.fill("input[placeholder='Search HealthUnlocked']", keyword)
    page.keyboard.press("Enter")
    time.sleep(2)

    # Track post count per user
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
            
            if post_limit and len(user_post_count) >= post_limit:
                break
            
        # Break the outer loop if the limit is reached
        if post_limit and len(user_post_count) >= post_limit:
            break

        # Pagination
        next_button = page.locator("a[aria-label='Next page']")
        # print(next_button.all_inner_texts())
        # print(next_button.count())
        if next_button.count() > 0:
            next_button.click()
            time.sleep(2)
        else:
            break
    
    # Convert dictionary to a list of dictionaries
    usernames_data = [{"username": user, "keyword": keyword, "post_count": count} 
                  for user, count in user_post_count.items()]
    return usernames_data

#helper
def save_to_csv(filename, data, headers):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

# Main
with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # True - for headless mode
    page = browser.new_page()

    try:
        #-------------------Login-------------------
        # Open the login page
        page.goto("https://healthunlocked.com/login")
        page.wait_for_timeout(3000)  # = 1 sec

        # Accept cookies
        page.click("#ccc-notify-accept")

        # Enter login credentials
        page.fill("#email", EMAIL)
        page.fill("#password", PASSWORD)
        page.click("button[data-testid='log-in-button']")
        page.wait_for_timeout(2000)  # Wait for login to complete

        # Part 1: General Patterns

        #-------------------Collect Usernames from Posts using a Keyword-------------------
        # Search for keywords and collect usernames
        keywords = ["depression", "anxiety"]
        usernames_data = []
        for keyword in keywords:
            usernames_data.extend(get_usernames_by_keyword(page, keyword, post_limit=100))
        save_to_csv("usernames_data.csv", usernames_data, ["username", "keyword", "post_count"])
    

        #-------------------Collect User Profiles-------------------
        #-------------------Create Unique Community List-------------------

    finally:
        browser.close()

