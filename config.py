import os

# ==========================
# Directories
# ==========================
DATA_INPUT_DIR = "data_keywords"  # directory for the file with keywords
DATA_OUTPUT_DIR = "data_output"  # directory for output data
os.makedirs(DATA_INPUT_DIR, exist_ok=True)  # ensure input directory with keywords exists
os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)  # ensure output directory exists

# ==========================
# Limits for scraping
# ==========================
USERNAMES_BY_KEYWORD_LIMIT = 100  # (set to -> 100) number of unqiue usernames when collecting usernames by a keyword
# Delete
USER_PROFILE_LIMIT = 6  # Optinal: limit number of user's profile to collect info from (now: hard coded)
#
POSTS_BY_USER_LIMIT = 50  # number of posts to go through to collect communities' names and links when on user profile
PAGINATION_LIMIT = 10  # (set to -> 10) number of pages to consider when collecting the most active users of a community ('Members'->'Most contribution'). Decided to set at 10.
MAX_RETRIES = 2  # number of attempts to load a page when a certain element (e.g. 'Next Page', 'Show more posts', search bar) is not found

# ==========================
# Paths and filenames
# ==========================

# Log files for tracking failed attempts to scrape
ERROR_LOG_FILE = "scrape_errors.txt"
STATS_LOG_FILE = "scraping_stats.txt"  # statistics
FAILED_USERNAMES_LOG = "failed_general_usernames.txt"  # failed general usernames
FAILED_COMMUNITIES_LOG = "failed_communities.txt"  #  failed communities
FAILED_MEMBERS_LOG = "failed_members.txt"  #  failed members

# Keywords for global search on HU to collect usernames
KEYWORDS_FILE = os.path.join(DATA_INPUT_DIR, "keywords_generated.csv")

categories = [
    # Mental Health - 6
    "Mental Health",
    "Depression",
    "Anxiety",
    "ADHD",
    "Bipolar Disorder",
    "Eating Disorder",

    # Physical Health - 8
    "Diabetes",
    "Arthritis",
    "Hypertension",
    "Chronic Pain",
    "Autoimmune Disorder",
    "Nutrition and Wellness",
    "Sleep Disorder",
    "Neurological Disorder",

    # Women's Health - 4
    "Women's Health",
    "Menopause",
    "PCOS",
    "Ovarian Health",

    # Substance Abuse - 4
    "Alcohol Addiction",
    "Opioid Addiction",
    "Cocaine Dependency",
    "Nicotine Addiction",

    # Terminal Conditions - 4
    "Cancer",
    "ALS",
    "Dementia",
    "HIV"
]

CATEGORIES_OF_KEYWORDS = categories  # in case of scrapingkeywords from  ALL categories

# General patterns of co-occurrence:
USERNAMES_BY_KEYWORD =  os.path.join(DATA_OUTPUT_DIR, "usernames_by_keyword.json")  # file with usernames by a keyword; cols "username", "keyword", "post_count"
GENERAL_PROFILES_DATA =  os.path.join(DATA_OUTPUT_DIR, "general_profiles_data.json")  # file with user'profile info; cols "username", "tags", "demographics", "bio", "commmunities"
UNIQUE_COMM_LIST =  os.path.join(DATA_OUTPUT_DIR, "all_communities.json")  # file containg set of communities; cols "community_name", "community_url"

# Community-specific patterns of co-occurrence:
MEMBERS_BY_COMM =  os.path.join(DATA_OUTPUT_DIR, "members_by_comm.json")  # file with usernames by a community; cols "community_name", "community_url", "username"
PROFILES_BY_COMM_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_by_comm_data.json")  # file with profile info of communities' members; ; cols "username", "tags", "demographics", "bio", "commmunity"

# ==========================
# CSS selectors for scraping
# ==========================
SELECTORS = {
    # login
    "login_email": "#email",
    "login_password": "#password",
    "login_button": "button[data-testid='log-in-button']",

    # search by a keyword
    "search_input": "input[placeholder='Search HealthUnlocked']",
    "post_items_search_results": "a[data-sentry-element='Link'][href^='/user/']",

    # pagination
    "next_page_button": "text=Next page", # pagination
    "show_more_posts_button": "button:has-text('Show more posts')",  # show more

    # various selectors
    "community_card_username": ".community-member-card__username",  # user's posts on a community's page
    "meta_text_wrapper": "div[data-sentry-element='MetaTextWrapper']",  # community's name and link
    "replies_tab": "a[data-testid='profile-reply']",  # 'Replies' tab on a user's profile
    "community_metadata": "div[data-sentry-component='Details']",  # number of 'members' and 'posts'
    "about_comm": "div[data-sentry-component='Description']",  # community's 'About' text field

    # user's profile
    "profile_tags": "ul[data-sentry-component='HealthTags'] li a",
    "profile_bio": "div[data-sentry-component='ProfileBio']",
    "post_items": "div[data-sentry-element='PostItem']",

    # user's demographic info
    "profile_demographics_joined": "div[data-testid='profile__about_joined']",
    "profile_demographics_age": "div[data-testid='profile__about_age']",
    "profile_demographics_gender": "div[data-testid='profile__about_gender']",
    "profile_demographics_country": "div[data-testid='profile__about_country']",
    "profile_demographics_ethnicity": "div[data-testid='profile__about_ethnicity']",
}
