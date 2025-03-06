from datetime import datetime
import re

from helpers import write_to_json, read_json, pagination
from config import SELECTORS, MAX_RETRIES, ERROR_LOG_FILE, STATS_LOG_FILE, FAILED_USERNAMES_LOG, FAILED_COMMUNITIES_LOG, FAILED_MEMBERS_LOG
from keywords_handler import load_and_process_keywords_from_csv

# Perform global search by a keyword and gather usernames
def scrape_usernames_by_keyword(page, keywords_csv, categories, output_json, usernames_limit):
    """
    Perform global search on HealthUnlocked for each keyword from the provided categories.
    Collect usernames from posts and save the results into a JSON file.
    Each keyword is assigned to a category for structed search i.e. { "Mental Health": ["depression", "anxiety"]}.
    Handle variations in keywords (e.g. "smoke" - "smoking") using NLTK.
    Logs statistics on how many usernames were collected per category and in total.
    """
    # Load and extend the original list of keywords by their lemmas
    keywords = load_and_process_keywords_from_csv(keywords_csv)  # extended list of keywords by their lemmas (e.g. smoking -> smoke)
    
    # Identify which passed categories are valid
    valid_categories = []
    for category in categories:
        if category in keywords:  # check if category exists as a key in original 'keywords' dict
            valid_categories.append(category)
    if not valid_categories:
        print(f"Error: None of the provided categories {categories} exist in the keywords CSV file.")
        return  # exit    
    print(f"Perform search for validated categories: {valid_categories}")

    usernames_data = {}
    category_stats = {}  # track usernames collected per category

    for category in valid_categories:  # iterate by (valid) categories in dict { "Mental Health": ["depression", "anxiety"]}
        keyword_list = keywords[category]
        print(f"Process category: {category} with keywords: {keyword_list}")

        category_count = 0  # track number of usernames for the current category        
        for keyword in keyword_list:
            print(f"Searching for keyword: {keyword} (Category: {category})")

            user_post_count= {}  # track post count per user
            retries = 0  # track number of retries to scrape

            while retries < MAX_RETRIES:
                try:
                    # Reload page before retrying
                    if retries > 0:
                        print(f"Retry {retries} for keyword: {keyword}")
                        page.reload()
                        page.wait_for_timeout(2000)

                    # Global search on HU using a keyword
                    page.goto("https://healthunlocked.com/")
                    page.fill(SELECTORS["search_input"], keyword)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(2000)

                    print(f"-------- Keyword: {keyword} --------")

                    while True:
                        # Find all post elements which are the serach results
                        post_elements = page.locator(SELECTORS["post_items_search_results"]).all()

                        for post in post_elements:
                            username = post.text_content().strip()
                            if username:
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
                        category_count += 1

                    # Save progress after each keyword
                    write_to_json(output_json, usernames_data)

                    break  # exit retry block if success

                except Exception as e:  # unexpected error occurs
                    error_message = str(e).lower()

                    retries += 1
                    print(f"Error on keyword '{keyword}': {error_message}. Retrying ({retries}/{MAX_RETRIES})...")

                    # Handle network error
                    network_errors = ["ns_error", "timeout", "connection", "network", "reset", "refused", "aborted", "failed"]

                    if any(err in error_message for err in network_errors):
                        print(f"Network issue {error_message} for {keyword}. Reconnecting...")
                        page.wait_for_timeout(15000)
                    
                    page.reload()
                    page.wait_for_timeout(2000)

            if retries == MAX_RETRIES:
                with open(ERROR_LOG_FILE, "a") as log_file:
                    log_file.write(f"{keyword} | Error: {error_message}\n")
                print(f"Logged failed keyword: {keyword}")

        # stats for the current category
        category_stats[category] = category_count
    
    # Log stats after scraping all categories
    total_usernames = sum(category_stats.values())
    with open(STATS_LOG_FILE, "a") as log_file:
        log_file.write(f"\nUsernames scraped - scrape_usernames_by_keyword() :\n")
        for category, count in category_stats.items():
            log_file.write(f"-{category}: {count} usernames\n")
        log_file.write(f"Total usernames by keywords scraped: {total_usernames}\n")
    print(f"Statistics logged in {STATS_LOG_FILE}")

# Collect user's profile information
def scrape_user_profiles(page, input_json, output_json, unique_communities_json, post_limit):
    """
    For each username in the input file, navigate to the user's profile and gather their personal data 
    (tags, demographics, bio, communities). Implement retry mechanism for a username if scraping fails.
    Also maintain a global set of all communities ever discovered. 
    Create 2 JSON files containing user data and the set of communities. Save progress continuously.
    Log statistics on how many profiles were scraped.
    """
    # Load communities' unqiue list (if already exist) - global set of unique communities across all users
    try:
        all_communities = read_json(unique_communities_json)
    except FileNotFoundError:
        all_communities = {}

    # Load existing scraped profiles (to prevent overwriting old data)
    try:
        profiles_data = read_json(output_json)  # Load previous data
    except FileNotFoundError:
        profiles_data = {}


    # Read usernames from input file
    usernames_data = read_json(input_json)  # if JSON structure is a list of dict [ {}, {} ]
    usernames = list(usernames_data.keys()) # if JSON structure is a dict { "key1": {}, "key2": {} }

    total_profiles_scraped = 0  # track number of successfully scraped profiles

    # Log input file and number of usernames
    with open(STATS_LOG_FILE, "a") as log_file:
        log_file.write(f"\nStarting (general) profile scraping - scrape_user_profiles() :\n")
        log_file.write(f"Input file: {input_json}\n")
        log_file.write(f"Total usernames to process: {len(usernames)}\n")

    # Identify last scraped username
    scraped_usernames = set(profiles_data.keys())  # Get usernames already scraped
    last_scraped_username = max(scraped_usernames, key=lambda x: list(profiles_data.keys()).index(x)) if scraped_usernames else None

    # If scraping was interrupted, find the index of the last scraped username and start from the next one
    # Start from the beginning if no previous data
    start_index = usernames.index(last_scraped_username) + 1 if last_scraped_username in usernames else 0

    # ------- DELETE LIMIT LATER: in config.py USER_PROFILE_LIMIT ------------
    for i, username in enumerate(usernames[start_index:], start=start_index + 1):  # [:6]
        print(f"\nProcessing profile {i}/{len(usernames)} for username: {username}")

        retries = 0
        while retries < MAX_RETRIES:
            try:
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

                    # Store/update data from user's profiles (after each username)
                    write_to_json(output_json, profiles_data)

                    # Store/update a list of unique community names and their urls
                    write_to_json(unique_communities_json, all_communities)

                    total_profiles_scraped += 1

                break  # exit retry block if success
            except Exception as e:  # unexpected error occurs
                error_message = str(e).lower()

                retries += 1
                print(f"Error processing profile '{username}': {error_message}. Retrying ({retries}/{MAX_RETRIES})...")

                # Handle network error
                network_errors = ["ns_error", "timeout", "connection", "network", "reset", "refused", "aborted", "failed"]

                if any(err in error_message for err in network_errors):
                    print(f"Network issue {error_message} for {username}. Reconnecting...")
                    page.wait_for_timeout(15000)

                page.reload()
                page.wait_for_timeout(2000)

        if retries == MAX_RETRIES:
            print(f"Skipping user '{username}' after {MAX_RETRIES} retries.")
            with open(FAILED_USERNAMES_LOG, "a") as log_file:
                log_file.write(f"{username}\n")
    
    # Log stats of profile scraping process
    with open(STATS_LOG_FILE, "a") as log_file:
        log_file.write(f"Total (general) profiles successfully scraped: {total_profiles_scraped}\n")

    print(f"Statistics logged in {STATS_LOG_FILE}")

# Collect profile information of community's members
def scrape_member_profiles(page, members_by_comm_json, profiles_by_comm_json):
    """
    Process usernames from a JSON file with the most active community's members
    and collect their profile information. Save into a JSON file.
    
    """    
    # Read existing members' prfile data (if available) or create an empty dictionary
    try:
        profiles_by_community = read_json(profiles_by_comm_json)
    except FileNotFoundError:
        profiles_by_community = {}
    # profiles_by_community = {}
    
    # Read usernames and community details from JSON
    communities = read_json(members_by_comm_json)

    # Iterate through communities and their members
    # for comm_url, members in communities.items():  # iterate over key-value pairs of a dict
    for i, (comm_url, members) in enumerate(communities.items(), start=1):  # iterate over key-value pairs of a dict
    # for i, (comm_url, members) in enumerate(communities[start_index:].items(), start=start_index +1):
    # for i, username in enumerate(usernames[start_index:], start=start_index + 1):  # [:6]

        print(f"\nProcessing community {i}/{len(communities)}: {comm_url}")

        profiles_by_community[comm_url] = {}
        
        for member in members:  # [:2]
            
            retries = 0

            while retries < MAX_RETRIES:
                try:

                    # Scrape member's profile information
                    profile_data = scrape_profile_data(page, member)

                    if profile_data:
                        profiles_by_community[comm_url][member] = profile_data

                        write_to_json(profiles_by_comm_json, profiles_by_community)

                    break  # exit retry block if success

                except Exception as e:  # unexpected error occurs
                    error_message = str(e).lower()

                    retries += 1
                    print(f"Error processing member profile '{member}': {error_message}. Retrying ({retries}/{MAX_RETRIES})...")

                    # Handle network error
                    network_errors = ["ns_error", "timeout", "connection", "network", "reset", "refused", "aborted", "failed"]

                    if any(err in error_message for err in network_errors):
                        print(f"Network issue {error_message} for {member}. Reconnecting...")
                        page.wait_for_timeout(15000)

                    page.reload()
                    page.wait_for_timeout(2000)

            if retries == MAX_RETRIES:
                print(f"Skipping member '{member}' after {MAX_RETRIES} retries.")
                with open(FAILED_MEMBERS_LOG, "a") as log_file:
                    log_file.write(f"{member}\n")
        
    # write_to_json(profiles_by_comm_json, profiles_by_community)

# Collect usernames and metadata from a community page
def scrape_community_members(page, unqiue_communities_json, members_by_comm_json, pagination_limit=None):
    """
    For each community in the unique community list, navigate to the respective community page, 
    go to 'Most Contributors' tab and collect the usernames. 
    Only scrape a community if its metadata (the number of members and posts) has not been collected yet.
    Implements retry mechanism for each community if scraping fails.
    Update the unique community list with metadata.
    """
    # Read the unique community list (community_url as a key)
    unique_communities = read_json(unqiue_communities_json)

    # Read existing members data (if available) or create an empty dictionary
    try:
        members_by_comm = read_json(members_by_comm_json)
    except FileNotFoundError:
        members_by_comm = {}

    failed_communities = []  # track communities that were not scraped

    # Log stats of input file
    with open(STATS_LOG_FILE, "a") as log_file:
        log_file.write(f"\nStarting communities scraping - scrape_community_members() :\n")
        log_file.write(f"Total communities to process: {len(unique_communities)}\n")

    for i, (comm_url, comm_data) in enumerate(unique_communities.items(), start=1):

        # Skip communities that already have metadata (i.e. has been scraped already)
        if "posts_count" in comm_data and "members_count" in comm_data:
            print(f"Skipping {comm_url}, already scraped.")
            continue

        print(f"\nProcessing community {i}/{len(unique_communities)}: {comm_url}")

        retries = 0
        while retries < MAX_RETRIES:
            try:
                # Reload before retrying
                if retries > 0:
                    print(f"Retrying {comm_url}... Attempt {retries}/{MAX_RETRIES}")
                    page.reload()
                    page.wait_for_timeout(2000)

                # Collect metadata (number of posts and memebers), community's name and text field 'About'                
                metadata = extract_community_metadata(page, comm_url)
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

                members_by_comm[comm_url] = usernames

                # Save to / update JSON continuously
                write_to_json(members_by_comm_json, members_by_comm)
                write_to_json(unqiue_communities_json, unique_communities)
                
                break  # exit retry block if success
            except Exception as e:
                error_message = str(e).lower()
                
                retries += 1
                print(f"Error scraping community '{comm_url}': {error_message}. Retrying ({retries}/{MAX_RETRIES})...")

                # Handle network error
                network_errors = ["ns_error", "timeout", "connection", "network", "reset", "refused", "aborted", "failed"]

                if any(err in error_message for err in network_errors):
                    print(f"Network issue {error_message} for {comm_url}. Reconnecting...")
                    page.wait_for_timeout(15000)
                
                page.reload()
                page.wait_for_timeout(2000)

        if retries == MAX_RETRIES:
            print(f"Failed to scrape {comm_url} after {MAX_RETRIES} retries. Logging failed community.")
            failed_communities.append(comm_url)

    # Log failed communities
    if failed_communities:
        with open(FAILED_COMMUNITIES_LOG, "a") as log_file:
            for comm_url in failed_communities:
                log_file.write(f"{comm_url}\n")
        print(f"Failed communities logged in {FAILED_COMMUNITIES_LOG}")

    # Log stats
    with open(STATS_LOG_FILE, "a") as log_file:
        log_file.write(f"Total successfully scraped communities: {len(unique_communities)-len(failed_communities)}\n")
        log_file.write(f"Total failed communities: {len(failed_communities)}\n")
    print(f"Statistics logged in {STATS_LOG_FILE}")

# Helper: Collect metadata (number of posts and memebrs) of a community
def extract_community_metadata(page, comm_url):
    """
    Extract metadata (number of members and posts), name and text field 'About' 
    (only first 100 characters) from a community's page.
    """

    # Firstly, navigate to communitiy's 'About' tab
    about_tab_url = f"https://healthunlocked.com{comm_url}/about"
    print(f"Navigating to: {about_tab_url}")
    page.goto(about_tab_url)
    page.wait_for_timeout(2000)

    # Extract first 100 characters from 'About' section
    about_comm = page.locator(SELECTORS["about_comm"]).text_content().strip()[:150] if page.locator(SELECTORS["about_comm"]).count() > 0 else "N/A"

    # Secondly, navigate to communitiy's most active users ('Most contribution' on 'Members' tab)
    active_members_url = f"https://healthunlocked.com{comm_url}/members?filter=active&page=1"
    print(f"Navigating to: {active_members_url}")
    page.goto(active_members_url)
    page.wait_for_timeout(2000) 

    # Get metadata details: "Anxiety and Depression Support94,251 members•88,014 posts"
    metadata = page.locator(SELECTORS["community_metadata"]).text_content().strip()

    # Regex to extract community's name (right before the first digit)
    match = re.search(r"^(.*?)(?=\d)", metadata)
    community_name = match.group(1).strip() if match else "N/A"

    # Regex to extract the numbers of members and posts separately
    # \d{1,3}: matches 1–3 digits
    # (?:,\d{3})*: matches groups of ,### (e.g., ,251) for thousands separators
    match = re.search(r"(\d{1,3}(?:,\d{3})*) members•(\d{1,3}(?:,\d{3})*) posts", metadata)
    members_count = int(match.group(1).replace(",", "")) if match else "N/A"
    posts_count = int(match.group(2).replace(",", "")) if match else "N7A"

    return {
        "comm_name": community_name,
        "members_count": members_count,
        "posts_count": posts_count,
        "about_comm": about_comm
    }

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