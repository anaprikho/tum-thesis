import time
from datetime import datetime
import re

from helpers import write_to_json, read_json, pagination
from config import SELECTORS

### Options for pausing while scraping:
# page.wait_for_selector(".some-element", timeout=3000)
# page.wait_for_timeout(2000)
# time.sleep(2)

# Perform global search by a keyword and gather usernames
def scrape_usernames_by_keyword(page, keywords, output_json, usernames_limit):
    """
    Perform global search on HealthUnlocked for each keyword from the list, collect usernames from posts, 
    and save the results into a JSON file.
    Each keyword is assigned to a category for structed search. Handle variations
    e.g. "smoke" - "smoking" using NLTK or spaCy libraries.
    """
    usernames_data = {}

    for category, keyword_list in keywords.items():  # iterate by category in dict { "Mental Health": ["depression", "anxiety"]}
        for keyword in keyword_list:
            print(f"Searching for keyword: {keyword} (Category: {category})")
            

            # Global search on HU using a keyword
            page.goto("https://healthunlocked.com/")
            page.fill(SELECTORS["search_input"], keyword)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            # time.sleep(2)
            print(f"-------- Keyword: {keyword} --------")

            user_post_count= {}  # track post count per user

            while True:
                # Find all post elements which are the serach results
                post_elements = page.locator(SELECTORS["post_items_search_results"]).all()

                for post in post_elements:
                    username = post.text_content().strip()
                    if username:
                        # if username in user_post_count:
                        #     user_post_count[username] += 1
                        # else:
                        #     user_post_count[username] = 1
                        user_post_count[username] = user_post_count.get(username, 0) + 1
                    
                # Stop collection if the limit is reached (entire page processing) OR no 'Next Page'
                if len(user_post_count) >= usernames_limit or not pagination(page, "text=Next page"):
                    print(f"Reached limit of {usernames_limit} distinct usernames OR no more pages -> stop pagination.")
                    break
            
            # Append collected data for this keyword
            for username, count in user_post_count.items():
                if username not in usernames_data:
                    usernames_data[username] = {}  # create a sub-dictionary for the username
                usernames_data[username][keyword] = count  # update the counter

            # ----------- DELETE LATER: UPDATE FIRST 3 ENTRIES ONLY -----------
            # for i, key in enumerate(usernames_data):
            #     if i == 3:  # stop after updating 3 entries
            #         break
            #     usernames_data[key]["test_keyword"] = (i + 1) * 10  # assign test values (10, 20, 30)
            # ---------------------------------
    
    # Save all collected usernames to a JSON file
    write_to_json(output_json, usernames_data)

# Collect user's profile information
def scrape_user_profiles(page, input_json, output_json, unique_communities_json, post_limit):
    """
    For each username in the input file, navigate to the user's profile and gather their personal data 
    (tags, demographics, bio, communities). Also maintain a global set of all communities ever discovered. 
    Create 2 JSON files containing user data and the set of communities.
    """
    # Load communities' unqiue list (if already exist) - global set of unique communities across all users
    try:
        all_communities = read_json(unique_communities_json)
    except FileNotFoundError:
        all_communities = {}

    # Read usernames from input file
    usernames_data = read_json(input_json)  # if JSON structure is a list of dict [ {}, {} ]
    usernames = list(usernames_data.keys()) # if JSON structure is a dict { "key1": {}, "key2": {} }

    profiles_data = {}

    # ------- DELETE LATER: in config.py USER_PROFILE_LIMIT ------------
    for username in usernames[:6]:
        print(f"Processing profile for username: {username}")
        # Collect user's profile info (tags, demographics, bio, communities)
        profile_data = scrape_profile_data(page, username)
        
        if profile_data:
            # Collect community names and href from tabs 'Posts'and 'Replies' (where a user has showed any activity)
            communities = collect_communities_of_user(page, username, post_limit)
            profile_data["communities"] = list(communities) 
            profiles_data[username] = profile_data  # add profile info under username key
            
            # Update the global community set
            for comm_url in communities:
                if comm_url not in all_communities:  # new community is encountered
                    all_communities[comm_url] = {}

    # Store data from user's profiles
    write_to_json(output_json, profiles_data)

    # Store/update a list of unique community names and their urls
    write_to_json(unique_communities_json, all_communities)

# Collect profile information of community's members
def scrape_member_profiles(page, members_by_comm_json, profiles_by_comm_json):
    """
    Process usernames from a JSON file with the most active community's members
    and collect their profile information. Save into a JSON file.
    
    """
    profiles_by_community = {}
    
    # Read usernames and community details from JSON
    communities = read_json(members_by_comm_json)

    # Iterate through communities and their members
    for comm_url, members in communities.items():  # iterate over key-value pairs of a dict
        print(f"Processing community: {comm_url}")

        profiles_by_community[comm_url] = {}
        
        # --------- Delete the limit later!-------------
        for member in members[:2]:
            # Scrape member's profile information
            profile_data = scrape_profile_data(page, member)

            if profile_data:
                profiles_by_community[comm_url][member] = profile_data
        
    write_to_json(profiles_by_comm_json, profiles_by_community)

# Collect usernames and metadata from a community page
def scrape_community_members(page, unqiue_communities_json, members_by_comm_json, pagination_limit=None):
    """
    For each community in the unique community list, navigate to the respective community page, 
    go to 'Most Contributors' tab and collect the usernames. 
    Only scrape a community if its metadata (the number of members and posts) has not been collected yet.
    Update the unique community list with metadata.
    """
    # Read the unique community list (community_url as a key)
    unique_communities = read_json(unqiue_communities_json)

    # Read existing members data (if available) or create an empty dictionary
    try:
        members_by_comm = read_json(members_by_comm_json)
    except FileNotFoundError:
        members_by_comm = {}

    # Iterate over each community
    for comm_url, comm_data in unique_communities.items():
        comm_name = comm_data["comm_name"]

        # Skip communities that already have metadata (i.e. has been scraped already)
        if "posts_count" in comm_data and "members_count" in comm_data:
            print(f"Skipping {comm_name} ({comm_url}), already scraped.")
            continue

        print(f"Collecting usernames from {comm_name} at {comm_url}...")  

        # Collect metadata (number of posts and memebers)
        metadata = extract_community_metadata(page, comm_name, comm_url)
        if metadata:
            unique_communities[comm_url].update(metadata)

        # Collect usernames of most active users
        usernames = []
        pages_scraped = 0  # counter of pages visited
        while True:
            # Locate username links on the current page
            post_elements = page.locator(SELECTORS["community_card_username"]).all()
            
            for element in post_elements:
                username = element.inner_text().strip().split()[0]  # extract username, ignore role/badge if there is
                if username and username not in usernames:
                    usernames.append(username)

            # Check if page limit is reached
            pages_scraped += 1
            if pagination_limit is not None and pages_scraped >= pagination_limit:
                break # while-loop

            # Pagination: check if 'Next page' btn is available
            if not pagination(page, SELECTORS["next_page_button"]): # as returns False, when no more pages exist
                break

        # usernames_comm_data[comm_url] = {"active_members": usernames}
        members_by_comm[comm_url] = usernames

    # Save to JSON
    write_to_json(members_by_comm_json, members_by_comm)
    write_to_json(unqiue_communities_json, unique_communities)

# Helper: Collect metadata (number of posts and memebrs) of a community
def extract_community_metadata(page, comm_name, comm_url):
    """
    Extract metadata (number of members and posts) from a community's page.
    """
    # Navigate to communitiy's most active users ('Most contribution' on 'Members' tab)
    active_members_url = f"https://healthunlocked.com{comm_url}/members?filter=active&page=1"
    print(f"Navigating to: {active_members_url}")
    page.goto(active_members_url)
    page.wait_for_timeout(2000) 

    # Get metadata details: "Anxiety and Depression Support94,251 members•88,014 posts"
    metadata = page.locator(SELECTORS["community_metadata"]).text_content().strip()

    # Regex to extract the numbers of members and posts separately
    # \d{1,3}: matches 1–3 digits
    # (?:,\d{3})*: matches groups of ,### (e.g., ,251) for thousands separators
    match = re.search(r"(\d{1,3}(?:,\d{3})*) members•(\d{1,3}(?:,\d{3})*) posts", metadata)

    if match:
        members_count = int(match.group(1).replace(",", ""))
        posts_count = int(match.group(2).replace(",", "")) 
        print(f"Members: {members_count}, Posts: {posts_count}")

        return {
            "members_count": members_count,
            "posts_count": posts_count
        }
    else:
        print(f"Metadata extraction failed for {comm_name}.")

# Helper: Scrape User Profile Data
def scrape_profile_data(page, username):
    """
    Scrape profile data (tags, demographics, bio, communities) for a given username.
    """
    # Define locator of data elements
    demographics_locators = {
        "joined": SELECTORS["profile_demographics_joined"],
        "age": SELECTORS["profile_demographics_age"],
        "gender": SELECTORS["profile_demographics_gender"],
        "country": SELECTORS["profile_demographics_country"],
        "ethnicity": SELECTORS["profile_demographics_ethnicity"]
    }

    # Navigate to the user's profile page
    profile_url = f"https://healthunlocked.com/user/{username}"
    page.goto(profile_url)
    page.wait_for_timeout(2000)

    # Collect tags, demographic info, bio details, communities
    try:
        # Collect tags
        tags = []
        tag_elements = page.locator(SELECTORS["profile_tags"])
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
            # Check if a field exists and extract its content
            if page.locator(locator).count() > 0:
                value = page.locator(locator).text_content().strip()
                
                # Convert 'joined' field to date format
                if key == 'joined':
                    demographics[key] = datetime.strptime(value, "%B %d, %Y").strftime("%Y-%m-%d")  # YYYY-MM-DD
                else:
                    demographics[key] = value

            else:
                demographics[key] = "N/A"  # if a field is missing
        print(f"username: {username} has demographics: {demographics}")

        # Collect bio
        if page.locator(SELECTORS["profile_bio"]).count() > 0: # Check if bio section exists
            bio = page.locator(SELECTORS["profile_bio"]).text_content().strip()
            # Remove "Read more" and "Read less" if there is
            bio = bio.replace("Read more", "").replace("Read less", "").strip()
        else:
            bio = "N/A" # if no bio
        print(f"username: {username} has bio: {bio}")

        # Return collected info
        return{
            "tags": tags,
            "demographics": demographics,
            "bio": bio
        }
    except Exception as e:
        print(f"Error collecting user's profile data for {username}: {e}")
        return None

# Helper: collect communities' names and URLs    from 'Posts' and 'Replies' tabs on a user's profile
def collect_communities_of_user(page, username, post_limit):
    """
    Navigate to 'Posts' and 'Replies' tabs on a user's profile. 
    Extract community href from user's posts/replies.
    Return a set of communities' URLs, where a user has posted or replied.
    """
    # Define URLs for 'Posts' and 'Replies' tabs
    tabs_urls = [
        f"https://healthunlocked.com/user/{username}/posts",
        f"https://healthunlocked.com/user/{username}/replies"
    ]
    
    all_communities = set()    
    for tab_url in tabs_urls:
        print(f"Navigating to: {tab_url}")

        communities = process_tab(page, tab_url, post_limit)
        all_communities.update(communities)
    return all_communities

# Helper: Process a single tab ('Posts' / 'Replies) individualy.
def process_tab(page, tab_url, post_limit):
    '''
    Process a 'Posts'/'Reply' tabl on a user's profile to collect community URLs.
    Return a set of communities' URLs.
    '''
    communities = set()
    page.goto(tab_url)
    page.wait_for_timeout(2000)

    posts_scraped = 0  # track the number of posts already visited; reset counter for each tab
    start_index = 0   # track starting index for each batch of posts loaded

    while posts_scraped <= post_limit:

        # Get currently showed post items (30 post_items max)
        post_items = page.locator(SELECTORS["post_items"])
        post_count_current = post_items.count()

        print(f"Found {post_count_current} items on {tab_url}")

        # Loop over newly showed posts, find the community's name and link
        for i in range(start_index, post_count_current):

            # Check if limit is reached (only with loaded posts)
            if posts_scraped > post_limit:
                print(f"Reached the post limit to scrape from 'Posts' or 'Replies' tab. Limit is: {post_limit}.")
                # return communities  # exit when limit is reached
                break  # stop scraping posts for this tab
                
            post_item = post_items.nth(i)  # only look inside the current post item, not all loaded posts
            # Extract community's name and link
            community_url = extract_community_url(post_item)

            if community_url:
                communities.add(community_url)
                posts_scraped += 1
                print(f"Total posts scraped so far: {posts_scraped}.")
            else:
                print("No community's link found; skipping this post...")

        # Update start index for next bacth of posts
        start_index = post_count_current

        # Click 'Show more posts' and check if limit is reached
        if not pagination(page, SELECTORS["show_more_posts_button"]) or posts_scraped >= post_limit:
            print(f"Reached the post limit {post_limit} OR no more post items to show.")
            break

        # # Check if limit is reached for current tab (before loading more posts)
        # if posts_scraped >=  post_limit:
        #     print(f"Reached the post limit {post_limit}.")
        #     # return communities  # exit when limit is reached
        #     break
        
        # # Click 'Show more posts' button to load more posts
        # show_more_button = page.locator(SELECTORS["show_more_posts_button"])
        # if show_more_button.count() > 0 and show_more_button.is_visible():
        #     print("Clicking 'Show more posts' button...")
        #     show_more_button.wait_for(state="visible", timeout=3000)
        #     show_more_button.click()
        #     page.wait_for_timeout(2000)
        # else:
        #     print("No more posts to load.")
        #     break  # exit when no more posts exist
    return communities

# Helper: Extract a community's name and link from a user's post item.
def extract_community_url(post_item):
    """
    Extract community's URL from a user's post/reply (post item).
    Returns a community_url or None if not found.
    """
    community_link = None

    ## Case 1: 'Posts' tab (has 2 links: user and community)
    # Within this PostItem, find the "MetaTextWrapper" containing community name and href
    # Get the SECOND <a> tag in MetaTextWrapper, as the FIRST is the userlink
    all_links = post_item.locator(SELECTORS["meta_text_wrapper"]).locator("a[href^='/']")  # find all <a> tags
    if all_links.count() >= 2:
        community_link = all_links.nth(1)

    ## Case 2: 'Replies' tab (has only community's link)
    else:
        community_link = post_item.locator(SELECTORS["replies_tab"])

    # Extract community's URL (if found a link)    
    if community_link and community_link.count() > 0:
        return community_link.get_attribute("href")
    else:
        return None