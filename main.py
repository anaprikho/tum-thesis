import os
import time
import csv
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

### Options for pausing while scraping:
# page.wait_for_selector(".some-element", timeout=3000)
# page.wait_for_timeout(2000)
# time.sleep(2)

# Perform global search by a keyword and gather usernames
def get_usernames_by_keyword(page, keywords, output_csv, post_limit=None):
    """
    Perform global search by a list of keywords, collect usernames from posts, 
    and save the results into a CSV file. The limit of posts is set to None by default.
    """
    usernames_data = []

    for keyword in keywords:
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
            next_button_selector = "text=Next page"
            if not pagination(page, next_button_selector): # as returns False
                break
        
         # Append collected data for this keyword
        for username, count in user_post_count.items():
            usernames_data.append({"username": username, "keyword": keyword, "post_count": count})
    
    # Save all collected usernames to CSV file
    save_to_csv(output_csv, usernames_data, ["username", "keyword", "post_count"])

# Collect user's profile information
def get_user_profile(page, input_csv, output_csv):
    """
    Navigates to each user's profile (based on the usernames provided in the input CSV file) and gathers their data.
    Returns a CSV file containing user data.
    """
    # Read usernames from input file
    with open(input_csv, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        usernames = [row["username"] for row in reader]

    # Define locator of data elements
    tags_locator = "ul.sc-4bc2cf0e-0.emzbAL li a"
    demographics_locators = {
        "age": "div[data-testid='profile__about_age']",
        "gender": "div[data-testid='profile__about_gender']",
        "country": "div[data-testid='profile__about_country']",
        "ethnicity": "div[data-testid='profile__about_ethnicity']",
    }
    bio_locator = "div[data-sentry-component='ProfileBio']"
    tabs_locators = {  
        "posts": "a[href$='/posts']",  # 'Posts' tab
        "replies": "a[href$='/replies']"
    }

    # Helper function: collect communities from a given tab ("Posts" or "Replies")
    def collect_communities_from_tab(tab_name):
        """
        Navigate to according tab (e.g. "Posts" or "Replies"). 
        Extract community names and href from user's posts/replies.
        Return a set of (community_name, community_url).
        """
        tab_locator = tabs_locators[tab_name]
        tab_communities = set()
        page.click(tab_locator)
        page.wait_for_timeout(2000)

        # Get all post items
        post_items = page.locator("div[data-sentry-element='PostItem']")
        # Loop over each post item, find the community link
        for i in range(post_items.count()):
            post_item = post_items.nth(i)  # only look inside the current post item, not the entire page
            # Within this PostItem, find the "MetaTextWrapper" containing community name and href
            meta_wrapper = post_item.locator("div[data-sentry-element='MetaTextWrapper']")
            
            # Get the SECOND <a> tag in MetaTextWrapper, as the FIRST is the userlink
            all_links = meta_wrapper.locator("a[href^='/']")
            if all_links.count() >= 2:
                community_link = all_links.nth(1)  # the 2nd link
                community_name = community_link.text_content().strip()
                community_url = community_link.get_attribute("href")
                communities.add((community_name, community_url))
            else:
                # There's no second link
                print("No second link found; skipping this post...")

        return tab_communities

    # Navigate to user profile page by constructing URL
    profiles_data = []
    for username in usernames[:3]:
        print(f"Processing profile for username: {username}")

        # Navigate to the user's profile page
        profile_url = f"https://healthunlocked.com/user/{username}"
        page.goto(profile_url)
        page.wait_for_timeout(2000)

        # Collect tags, demographic info, bio details, communities
        try:
            # Collect tags
            tags = []
            tag_elements = page.locator(tags_locator)
            if tag_elements.count() >0:
                for tag in tag_elements.all():
                    tag_text = tag.text_content().strip()
                    if tag_text:
                        tags.append(tag_text)
            else:
                tags = ["N/A"]  # if no tags
            print(f"username: {username} has tags {tags}")

            # Collect demographics (age, gender, country, ethnicity)
            demographics = {}
            for key, locator in demographics_locators.items():
                # Check if a fiels exists and extract its content
                if page.locator(locator).count() > 0:
                    demographics[key] = page.locator(locator).text_content().strip()
                else:
                    demographics[key] = "N/A"  # if field is missing
            print(f"username: {username} has demographics: {demographics}")

            # Collect bio
            if page.locator(bio_locator).count() > 0: # Check if bio section exists
                bio = page.locator(bio_locator).text_content().strip()
            else:
                bio = "N/A" # if no bio
            print(f"username: {username} has bio: {bio}")

            # Collect communities a user has been active in (posted and replied)
            communities = set()
            # Collect community names and href from tabs 'Posts'and 'Replies'
            for tab in ["posts", "replies"]:
                tab_communities = collect_communities_from_tab(tab)
                communities.update(tab_communities)  # merge sets

            # Store collected info
            profiles_data.append({
                "username": username,
                "tags": tags,
                "demographics": demographics,
                "bio": bio,
                "communities": list(communities)
            })
        except Exception as e:
            print(f"Error collecting user's profile data for {username}: {e}")
            continue

    # store data
    print(f"profile data: {profiles_data}")
    save_to_csv(output_csv, profiles_data, ["username", "tags", "demographics", "bio", "communities", "community_urls"])

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

# Helper: Pagination
def pagination(page, next_button_selector):
    next_button = page.locator(next_button_selector)

    if next_button.count() > 0 and next_button.is_visible():
        print("Pagination: Moving to the next page...")
        page.wait_for_selector(next_button_selector, timeout=2000)  # Wait for button to appear
        next_button.click()
        page.wait_for_timeout(2000) # Wait for the next page to load
        return True
    else:
        print("No more pages to navigate.")
        return False
    
    # Pagination
        # next_button = page.locator("text=Next page")
        # if next_button.count() > 0 and next_button.is_visible():
        #     print("Pagination: Moving to the next page...")
        #     page.wait_for_selector("text=Next page", timeout=2000)
        #     next_button.click()
        #     # page.wait_for_timeout(2000)
        #     # try:
        #     #     current_url = page.url
        #     #     next_button.click(timeout=10000)
        #     #     page.wait_for_load_state("domcontentloaded")
        #     #     # Verify page change
        #     #     if page.url == current_url:
        #     #         print("Next page did not load. Exiting pagination.")
        #     #         break
        #     # except TimeoutError:
        #     #     print("Pagination failed. Exiting pagination loop.")
        #     #     break
        # else:
        #     print("No more pages to navigate.")
        #     break

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

        ## Step 1: Collect Usernames from Posts using a Keyword
        keywords = ["depression", "anxiety"]
        usernames_csv = "usernames_data.csv"
        # Define a post limit to search through (default=None)
        get_usernames_by_keyword(page, keywords, usernames_csv, post_limit=70)

        ## Step 2: Collect User Profiles
        # Define the input and output CSV files
        input_csv = "usernames_data.csv" 
        output_csv = "user_profiles.csv"
        # Collect user profiles
        get_user_profile(page, input_csv, output_csv)

        ## Step 3: Create Unique Community List
        # unique_communities = []

    finally:
        browser.close()

