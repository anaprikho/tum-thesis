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
POST_LIMIT_KEYWORD = 70  # Optional: limit number of posts when collecting usernames by a keyword
USER_PROFILE_LIMIT = 6  # Optinal: limit number of user's profile to collect info from
POST_LIMIT_USER = 100  # number of posts to go through to collect communities' names and links when on user profile
POST_LIMIT_MEMBERS = 10  # Optional: number of most active users of a community to collect ('Members'->'Most contribution')

### Define file names
DATA_OUTPUT_DIR = "data_output"  # directory for data output
os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)  # ensure the data output directory exists

# General patterns of co-occurrence:
USERNAMES_BY_KEYWORD =  os.path.join(DATA_OUTPUT_DIR, "usernames_keyword_data.csv")  # file with usernames by a keyword; cols "username", "keyword", "post_count"
PROFILES_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_data.csv")  # file with user'profile info; cols "username", "tags", "demographics", "bio", "commmunities"
UNIQUE_COMM_LIST =  os.path.join(DATA_OUTPUT_DIR, "unique_communities.csv")  # file containg set of communities; cols "community_name", "community_url"

# Community-specific patterns of co-occurrence:
USERNAMES_BY_COMM =  os.path.join(DATA_OUTPUT_DIR, "usernames_comm_data.csv")  # file with usernames by a community; cols "community_name", "community_url", "username"
PROFILES_BY_COMM_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_by_comm_data.csv")  # file with profile info of communities' members; ; cols "username", "tags", "demographics", "bio", "commmunity"
COMM_LIST_METADATA = os.path.join(DATA_OUTPUT_DIR, "comm_metadata.csv")  # unique community list extended by metadata

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
def get_user_profile_and_comm(page, input_csv, output_csv, unique_communities_csv, post_limit):
    """
    For each username in 'input_csv' file, navigate to the user's profile and gather their personal data 
    (tags, demographics, bio, communities). Also maintains a global set of all communities doscovered. 
    Create 2 CSV files containing user data and ther set of communities.
    """
    # Read usernames from input file
    with open(input_csv, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        usernames = [row["username"] for row in reader]

    # Navigate to user profile page by constructing URL
    profiles_data = []
    all_communities = set()  # global set of unique communities across all users
    for username in usernames[:USER_PROFILE_LIMIT]:
        print(f"Processing profile for username: {username}")
        profile_data = scrape_profile_data(page, username)
        
        if profile_data:
            # Collect community names and href from tabs 'Posts'and 'Replies' (where a user has showed any activity)
            communities = collect_communities_of_user(page, username, post_limit)
            profile_data["communities"] = list(communities) 
            profiles_data.append(profile_data)
            
            # Update the global community set
            all_communities.update(communities)

    # Store data from user's profiles
    save_to_csv(output_csv, profiles_data, ["username", "tags", "demographics", "bio", "communities"])
    
    # Store a list of unique community names and their urls
    # Convert set of tuples to list of dict
    communities_list = []
    for (name, url) in sorted(all_communities):
        communities_list.append({"community_name": name, "community_url": url})
    save_to_csv(unique_communities_csv, communities_list, ["community_name", "community_url"])
    print(f"Write {len(all_communities)} unique communities to {unique_communities_csv}.")

# Helper: collect communities' names and URLs    from 'Posts' and 'Replies' tabs on a user's profile
def collect_communities_of_user(page, username, post_limit):
    """
    Navigate to 'Posts' and 'Replies' tabs on a user's profile. 
    Extract community names and href from user's posts/replies.
    Return a set of (community_name, community_url), where a user has posted or replied.
    """
    # Define URLs for 'Posts' and 'Replies' tabs
    tabs_urls = [
        f"https://healthunlocked.com/user/{username}/posts",
        f"https://healthunlocked.com/user/{username}/replies"
    ]
    
    communities = set()    
    for tab_url in tabs_urls:
        print(f"Navigating to: {tab_url}")
        page.goto(tab_url)
        page.wait_for_timeout(2000)
 
        posts_scraped = 0  # track the number of posts already visited; reset counter for each tab
        start_index = 0   # track starting index for each batch of posts loaded

        while posts_scraped <= post_limit:

            # Get currently showed post items
            post_items = page.locator("div[data-sentry-element='PostItem']")
            post_count_current = post_items.count()

            print(f"Found {post_count_current} items on {tab_url} of user {username}.")

            # Loop over newly showed posts, find the community's name and link
            for i in range(start_index, post_count_current):

                # Check if limit is reached (only with loaded posts)
                if posts_scraped > post_limit:
                    print(f"Reached the post limit to scrape from 'Posts' or 'Replies' tab. Limit is: {post_limit}.")
                    # return communities  # exit when limit is reached
                    break  # stop scraping posts for this tab
                    
                post_item = post_items.nth(i)  # only look inside the current post item, not all loaded posts

                # -------------- Extract community's name and link --------------
                community_link = None

                # Case 1: 'Posts' tab (has 2 links: user and community)
                # Within this PostItem, find the "MetaTextWrapper" containing community name and href
                # Get the SECOND <a> tag in MetaTextWrapper, as the FIRST is the userlink
                all_links = post_item.locator("div[data-sentry-element='MetaTextWrapper']").locator("a[href^='/']")  # find all <a> tags
                if all_links.count() >= 2:
                    community_link = all_links.nth(1)
                # Case 2: 'Replies' tab (has only community's link)
                else:
                    community_link = post_item.locator("a[data-testid='profile-reply']")

                # Extract community's name and URL (if found a link)    
                if community_link and community_link.count() > 0:
                    community_url = community_link.get_attribute("href")
                    community_name = community_link.text_content().strip()

                    communities.add((community_name, community_url))
                    posts_scraped += 1
                    print(f"Total posts scraped so far: {posts_scraped}.")
                else:
                    print("No community's link found; skipping this post...")
                # ------------------------------------------------------------------

            # Update start index for next bacth of posts
            start_index = post_count_current
            
            # Check if limit is reached for current tab (before loading more posts)
            if posts_scraped >=  post_limit:
                print(f"Reached the post limit {post_limit}.")
                # return communities  # exit when limit is reached
                break
            
            # Click 'Show more posts' button to load more posts
            show_more_button = page.locator("button:has-text('Show more posts')")
            if show_more_button.count() > 0 and show_more_button.is_visible():
                print("Clicking 'Show more posts' button...")
                show_more_button.wait_for(state="visible", timeout=3000)
                show_more_button.click()
                page.wait_for_timeout(2000)
            else:
                print("No more posts to load.")
                break  # exit when no more posts exist
    return communities

# Collect user's profile information of a community's members
def get_user_profile_from_community(page, input_csv, output_csv):
    """
    Process usernames from a CSV file with a community's memebers with the most contribution
    and collect their profile information.
    
    """
    profiles_data = []
    members = []
    # Read usernames and community names from input CSV
    with open(input_csv, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            members.append({  # convert to list of dict
                "username": row["username"],  
                "community_name": row["community_name"] 
            })
    
    # Process each username
    for member in members:
        username = member["username"]
        community_name = member["community_name"]
        print(f"Processing profile for username: {username} in community: {community_name}")

        # Scrape member's profile information
        profile_data = scrape_profile_data(page, username)
        if profile_data:
            profile_data["community_origin"] = community_name  # add a community name from which the user was found
            profiles_data.append(profile_data)

    # Save profiles data of community's members
    save_to_csv(output_csv, profiles_data, ["username", "tags", "demographics", "bio", "community_origin"])

# Collect usernames from a community page
def get_usernames_by_community(page, input_csv, output_csv, metadata_output_csv, post_limit=None):
    """
    For each community in the unique community list, navigate to the respective community page, 
    go to 'Most Contributors' tab and collect the usernames. Also, save the number of memebers ans posts of the community.
    Creates two CSV files:
    1) Usernames by community (cols: "community_name", "community_url", "members_count", "posts_count", "username").
    2) Unique community list extended by metadata (community_name, community_url, members_count, posts_count).
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
    metadata_data = []  # store metadata for each community
    # Iterate over each community
    for community in communities_name_url:
        comm_name = community["community_name"]
        comm_url = community["community_url"]
        print(f"Collecting usernames from {comm_name} at {comm_url}...")    

        # Navigate to communitiy's most active users ('Most contribution' on 'Members' tab)
        active_members_url = f"https://healthunlocked.com{comm_url}/members?filter=active&page=1"
        print(f"Navigating to: {active_members_url}")
        page.goto(active_members_url)
        page.wait_for_timeout(2000) 

        # Get the metadata of a community: "Anxiety and Depression Support94,251 members•88,014 posts"
        metadata = page.locator("div[data-sentry-component='Details']").text_content().strip()

        # Regex to extract the numbers of members and posts separately
        # \d{1,3}: matches 1–3 digits
        # (?:,\d{3})*: matches groups of ,### (e.g., ,251) for thousands separators
        match = re.search(r"(\d{1,3}(?:,\d{3})*) members•(\d{1,3}(?:,\d{3})*) posts", metadata) 
        if match:
            members_count = int(match.group(1).replace(",", ""))
            posts_count = int(match.group(2).replace(",", "")) 
        print(f"Members: {members_count}, Posts: {posts_count}")

        # Add metadata to metadata_data
        metadata_data.append({
            "community_name": comm_name,
            "community_url": comm_url,
            "members_count": members_count,
            "posts_count": posts_count
        })

        # Collect usernames
        usernames = []
        while True:
            # Locate username links on the current page
            post_elements = page.locator(".community-member-card__username").all()
            
            for element in post_elements:
                username = element.inner_text().strip().split()[0]  # extract username, ignore role/badge if there is
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

    save_to_csv(metadata_output_csv, metadata_data, ["community_name", "community_url", "members_count", "posts_count"])

# Helper: Scrape User Profile Data
def scrape_profile_data(page, username):
    """
    Scrape profile data (tags, demographics, bio, communities) for a given username.
    """
    # Define locator of data elements
    tags_locator = "ul.sc-4bc2cf0e-0.emzbAL li a"
    demographics_locators = {
        "age": "div[data-testid='profile__about_age']",
        "gender": "div[data-testid='profile__about_gender']",
        "country": "div[data-testid='profile__about_country']",
        "ethnicity": "div[data-testid='profile__about_ethnicity']",
    }
    bio_locator = "div[data-sentry-component='ProfileBio']"

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
        # bio_locator = "div[data-testid='profile__about_bio']"
        if page.locator(bio_locator).count() > 0: # Check if bio section exists
            bio = page.locator(bio_locator).text_content().strip()
            # Remove "Read more" and "Read less" if there is
            bio = bio.replace("Read more", "").replace("Read less", "").strip()
        else:
            bio = "N/A" # if no bio
        print(f"username: {username} has bio: {bio}")

        # Return collected info
        return{
            "username": username,
            "tags": tags,
            "demographics": demographics,
            "bio": bio
        }
    except Exception as e:
        print(f"Error collecting user's profile data for {username}: {e}")
        return None

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
        page.wait_for_selector(next_button_selector, timeout=3000)  # Wait for button to appear
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
        # get_usernames_by_keyword(page, GLOBAL_KEYWORDS, USERNAMES_BY_KEYWORD, POST_LIMIT_KEYWORD)

        ## --- Collect User Profiles and Create Unique Community List
        # get_user_profile_and_comm(page, USERNAMES_BY_KEYWORD, PROFILES_DATA, UNIQUE_COMM_LIST, POST_LIMIT_USER)

        ### 2) Community-specific Patterns

        ## --- Collect Usernames from Communities of the Unique Community List
        get_usernames_by_community(page, UNIQUE_COMM_LIST, USERNAMES_BY_COMM, COMM_LIST_METADATA, POST_LIMIT_MEMBERS)

        ## --- Collect User Profiles of Community Members
        # get_user_profile_from_community(page, USERNAMES_BY_COMM, PROFILES_BY_COMM_DATA)

    finally:
        browser.close()
