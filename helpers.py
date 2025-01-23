import json
import os
from dotenv import load_dotenv

from config import SELECTORS

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
    Check and clikc the 'Next page' button if it exists. 
    Return True if pagination occurred, False otherwise.
    """
    next_button = page.locator(next_button_selector)

    if next_button.count() > 0 and next_button.is_visible():
        print("Pagination: Moving to the next page...")
        page.wait_for_selector(next_button_selector, timeout=3000)  # Wait for button to appear
        next_button.click()
        page.wait_for_timeout(2000) # Wait for the next page to load
        return True
    else:
        print("No more pages to navigate.")
        return False

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