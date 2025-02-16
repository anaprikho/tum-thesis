import json
import os
from dotenv import load_dotenv

from config import SELECTORS, MAX_RETRIES

# Login
def login(page):
    """
    Accept cookies and log in a user using credentials from environment variables (EMAIL, PASSWORD).
    """
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
    page.fill(SELECTORS["login_email"], EMAIL)
    page.fill(SELECTORS["login_password"], PASSWORD)

    # Ensure the login button is visible and enabled, then click it
    page.wait_for_selector((SELECTORS["login_button"]), timeout=5000)
    page.click(SELECTORS["login_button"])  
    page.wait_for_timeout(2000)  # Wait for login to complete

    print("Login successful.")

# Pagination
def pagination(page, next_button_selector):
    """
    Check and clikc the 'Next page' or 'Show more posts' button if it exists. 
    Retries if the button is missing (for both 'Next Page' and 'Show more posts').
    Reloads the page before each retry. 
    Stops if 'Show more posts' doesn't load new content (problem with HealthUnlocked).
    Return True if pagination occurred, False otherwise.
    """
    next_button = page.locator(next_button_selector)
    is_show_more_btn = "show_more" in next_button_selector  #SELECTORS["show_more_posts_button"]
    retries = 0  # track number of attempts

    while retries < MAX_RETRIES:
        try:
            # Check if new content is actually loaded after clicking on 'Show more posts'
            if is_show_more_btn:
                post_items_before = page.locator(SELECTORS["post_items"]).count()
            else:
                post_items_before = None
            
            # Reload page before retrying
            if retries > 0:
                print(f"Retrying pagination ({retries}/{MAX_RETRIES})... Reloading page.")
                page.reload()
                page.wait_for_timeout(2000)

            # Ensure btn exists and is visible
            if next_button.count() > 0 and next_button.is_visible():
                print("Pagination: Clicking 'Next' or 'Show more posts' button...")
                next_button.click()  # load new content
                page.wait_for_timeout(2000)

                if is_show_more_btn:
                    post_items_after = page.locator(SELECTORS["post_items"]).count()
                    if post_items_before == post_items_after:  # problem with HU
                        print(f"No new posts loaded after clicking 'Show more posts'. Stopping pagination.")
                        return False
            
                return True
            else:  # btn is missing
                print(f"'{next_button_selector}' button not found. Retrying... ({retries + 1}/{MAX_RETRIES})")
                retries += 1

        except Exception as e:  # unexpected error occurs
            print(f"Error during pagination attempt {retries + 1}: {str(e)}")
            retries += 1
    
    print("No more pages (or posts) to navigate.")
    return False  # if all retries failed


    # if next_button.count() > 0 and next_button.is_visible():
    #     print("Pagination: Clicking 'Next' or 'Show more posts' button...")
    #     page.wait_for_selector(next_button_selector, timeout=3000)  # Wait for button to appear
    #     next_button.wait_for(state="visible", timeout=3000)
    #     next_button.click()
    #     page.wait_for_timeout(2000) # Wait for the next page or more post items to load
    #     return True
    # else:
    #     print("No more pages (or posts) to navigate.")
    #     return False

# Read from JSON
def read_json(file_path):
    """
    Read data from a JSON file.
    """
    with open(file_path, mode="r", encoding="utf-8") as file:
        return json.load(file)
    print(f"Reading JSON file: {file_path}")

# Save to JSON
def write_to_json(file_path, data):
    """
    Write data to a JSON file.
    """
    with open(file_path, mode="w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    print(f"Saved to JSON file: {file_path}")