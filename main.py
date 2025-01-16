import os
import time
import csv
import re
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

### Options for pausing while scraping:
# page.wait_for_selector(".some-element", timeout=3000)
# page.wait_for_timeout(2000)
# time.sleep(2)
GLOBAL_KEYWORDS = ["depression", "anxiety"]  # define keywords for global search on HU to collect usernames
POST_LIMIT=70  # Optional: limit number of posts when collecting usernames by a keyword
USER_PROFILE_LIMIT = 3  # Optinal: limit number of user's profile to collect info from

# Define file names
USERNAMES_KEYWORD_OUTPUT_CSV = "usernames_keyword_data.csv"  # file with usernames by a keyword; cols "username", "keyword", "post_count"
USERNAMES_KEYWORD_INPUT_CSV = "usernames_keyword_data.csv"  # file containing usernames for which to scrape user profiles
PROFILES_DATA_OUTPUT_CSV = "profiles_data.csv"  # file with user'profile info; cols "username", "tags", "demographics", "bio", "commmunities"
UNIQUE_COMMUNITIES_CSV = "unique_communities.csv"  # file containg set of communities; cols "community_name", "community_url"
USERNAMES_COMMUNITY_OUTPUT_CSV = "usernames_comm_data"  # file with usernames by a community; cols "community_name", "community_url", "username"

# Perform global search by a keyword and gather usernames
def get_usernames_by_keyword(page, keywords, output_csv, post_limit=None):
    """
    Perform global search on HealthUnlocked for aech keyword from the list, collect usernames from posts, 
    and save the results into a CSV file. The limit of posts to search through is set to 'None' by default.
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
            # Find all post elements which are the serach results
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
def get_user_profile(page, input_csv, output_csv, unique_communities_csv):
    """
    For each username in 'input_csv' file, navigate to the user's profile and gather their personal data 
    (tags, demographics, bio, communities). Also maintains a global set of all communities doscovered. 
    Create 2 CSV files containing user data and ther set of communities.
    """
    # Global set of unique communities across *all* users
    all_communities = set()
    
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
    tab_locators = {  
        "posts": "a[href$='/posts']",  # 'Posts' tab
        "replies": "a[href$='/replies']"  # 'Replies' tab
    }

    # Helper function: collect communities from a given tab ("Posts" or "Replies")
    def collect_communities_from_tab(tab_name):
        """
        Navigate to according tab (e.g. "Posts" or "Replies"). 
        Extract community names and href from user's posts/replies.
        Return a set of (community_name, community_url).
        """
        tab_locator = tab_locators[tab_name]
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
    for username in usernames[:USER_PROFILE_LIMIT]:
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

            # Collect community names and href from tabs 'Posts'and 'Replies' (where a user has showed any activity)
            communities = set()
            for tab in ["posts", "replies"]:
                tab_communities = collect_communities_from_tab(tab)
                communities.update(tab_communities)  # merge sets
            
            # Update the global community set
            all_communities.update(communities)

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

    # Store data from user's profiles
    save_to_csv(output_csv, profiles_data, ["username", "tags", "demographics", "bio", "communities"])
    
    # Store a list of unique community names and their urls
    # Convert set of tuples to list of dict
    communities_list = []
    for (name, url) in sorted(all_communities):
        communities_list.append({"community_name": name, "community_url": url})
    save_to_csv(unique_communities_csv, communities_list, ["community_name", "community_url"])
    print(f"Write {len(all_communities)} unique communities to {unique_communities_csv}.")

# Collect usernames from a community page
def get_usernames_by_community(page, input_csv, output_csv, post_limit=None):
    """
    For each community in the unique community list, navigate to the respective community page, 
    go to 'Most Contributors' tab and collect the usernames. Also, save the number of memebers ans posts of the community.
    The output CSV file has cols: "community_name", "community_url", "members_count", "posts_count", "username".
    """
    # Read the unique community list
    communities_name_url = []
    with open(input_csv, mode="r", encoding="utf-8") as file:  # stored as ("Anxiety and Depression Support", /anxiety-depression-support)
        reader = csv.DictReader(file)
        for row in reader:
            communities_name_url.append({  # convert to list of dict
                "community_name": row["community_name"],  #  "Anxiety and Depression Support"
                "community_url": row["community_url"]     #  "/anxiety-depression-support"
            })

    usernames_comm_data = []
    # Iterate over each community
    for community in communities_name_url:
        comm_name = community["community_name"]
        comm_url = community["community_url"]
        print(f"Collecting usernames from {comm_name} at {comm_url}...")    

        # Navigate to a communitiy's page ('Members' tab)
        comm_url_full = f"https://healthunlocked.com{comm_url}/members"
        page.goto(comm_url_full)
        page.wait_for_timeout(2000)
        page.click("text=Most contributions")

        # Get the metadata of a community: "Anxiety and Depression Support94,251 members•88,014 posts"
        metadata = page.locator("div[data-sentry-component='Details']").text_content().strip()

        # Regex to extract the numbers of members and posts separately
        # \d{1,3}: matches 1–3 digits
        # (?:,\d{3})*: matches groups of ,### (e.g., ,251) for thousands separators
        match = re.search(r"(\d{1,3}(?:,\d{3})*) members•(\d{1,3}(?:,\d{3})*) posts", metadata) 
        if match:
            members_count = match.group(1)  # members number
            posts_count = match.group(2) 
        print(f"Members: {members_count}, Posts: {posts_count}")

        # Click 'Most contributions' button
        # page.click("text=Most contributions")
        # page.wait_for_selector(".community-member-card__username", timeout=10000)
        page.wait_for_timeout(2000)

        # Collect usernames
        usernames = []
        while True:
            # Locate username links on the current page
            post_elements = page.locator(".community-member-card__username").all()
            
            for element in post_elements:
                username = element.inner_text()  # extract username
                if username and username not in usernames:
                    usernames.append(username)

                    # Check if limit on distinct usernames is reached
                    if post_limit and len(usernames) >= post_limit:
                        break  # for-loop

            # Check if limit on distinct usernames is reached
            if post_limit and len(usernames) >= post_limit:
                break  # while-loop

            # Pagination
            next_button_selector = "text=Next page"
            if not pagination(page, next_button_selector): # as returns False
                break

        for username in usernames:
            usernames_comm_data.append({
                "username": username,
                "community_name": comm_name,
                "community_url": comm_url,
                "members_count": members_count,
                "posts_count": posts_count
            })

    save_to_csv(output_csv, usernames_comm_data, ["community_name", "community_url", "members_count", "posts_count", "username"])

# Helper: Login
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
    page.fill("#email", EMAIL)
    page.fill("#password", PASSWORD)

    # Ensure the login button is visible and enabled, then click it
    page.wait_for_selector("button[data-testid='log-in-button']", timeout=5000)  
    page.click("button[data-testid='log-in-button']")  
    page.wait_for_timeout(2000)  # Wait for login to complete

    print("Login successful.")

# Helper: Pagination
def pagination(page, next_button_selector):
    """
    Check and clikc the 'Next page' button if it exists. 
    Return True if pagination occurred, False otherwise.
    """
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

# Helper: Save to CSV
def save_to_csv(filename, data, headers):
    """
    Writes data (a list of dictionaries) to a file using the given columns.
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        print(f"Saved to file {filename}")

# Main
with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)  # True - for headless mode
    page = browser.new_page()

    try:
        login(page)
        ### 1) General Patterns

        ## --- Collect Usernames from Posts using a Keyword
        # get_usernames_by_keyword(page, GLOBAL_KEYWORDS, USERNAMES_KEYWORD_OUTPUT_CSV, POST_LIMIT)

        ## --- Collect User Profiles and Create Unique Community List
        # get_user_profile(page, USERNAMES_KEYWORD_INPUT_CSV, PROFILES_DATA_OUTPUT_CSV, UNIQUE_COMMUNITIES_CSV)

        ### 2) Community-specific Patterns

        ## --- Collect Usernames from Communities of the Unique Community List
        get_usernames_by_community(page, UNIQUE_COMMUNITIES_CSV, USERNAMES_COMMUNITY_OUTPUT_CSV, post_limit=10)



    finally:
        browser.close()

