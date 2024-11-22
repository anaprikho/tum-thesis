from selenium import webdriver
from selenium.webdriver.common.by import By
from dotenv import load_dotenv
import os
import time

# Initialize the Firefox WebDriver
driver = webdriver.Firefox()

try:
    # Step 1: Open the login page
    driver.get("https://healthunlocked.com/login")
    time.sleep(1)  # Wait for the page to load

    # Click btn to accept cookies
    cookies_button = driver.find_element(By.ID, "ccc-notify-accept")
    cookies_button.click()

    # Step 2: Enter login credentials
    load_dotenv()
    email_input = driver.find_element(By.ID, "email")
    password_input = driver.find_element(By.ID, "password")
    email_input.send_keys(os.getenv("EMAIL"))
    password_input.send_keys(os.getenv("PASSWORD"))

    # Click the login button
    login_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='log-in-button']")  # type='submit'
    login_button.click()

    time.sleep(2)  # Wait for login to complete

    # Step 3: Navigate to the members page
    driver.get("https://healthunlocked.com/anxiety-depression-support/members")
    time.sleep(1)  # Wait for the page to load

    # Click the 'Most contributors'
    most_contributors_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Most contributions')]")
    most_contributors_button.click()

    # Step 4: Collect usernames with pagination
    usernames = []
    while len(usernames) < 50:  # Stop when we have 50 usernames

        # Collect usernames on the current page
        time.sleep(2)
        username_elements = driver.find_elements(By.CLASS_NAME, "community-member-card__username")
        for element in username_elements:
            if element.text and element.text not in usernames:  # Avoid duplicates
                usernames.append(element.text)
                if len(usernames) >= 50:
                    break  # Exit inner loop if we hit 50

        # Go to the next page
        try:
            next_page_link = driver.find_element(By.LINK_TEXT, "Next page")
            next_page_link.click()  # Click the "Next page" link
        except Exception:
            print("No more pages to navigate.")
            break  # Exit if the "Next page" link is not found

    # Print the collected usernames
    print("Collected Usernames:")
    for username in usernames:
        print(username)
    print("Number of elements found:", len(usernames))

    time.sleep(1)

finally:
    # Close the browser
    driver.quit()