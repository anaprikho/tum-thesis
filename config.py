import os

# Keywords for global search and limits
GLOBAL_KEYWORDS = ["depression", "anxiety"]  # define keywords for global search on HU to collect usernames
USERNAMES_LIMIT_KEYWORD = 7  # Optional: limit number of posts when collecting usernames by a keyword
USER_PROFILE_LIMIT = 6  # Optinal: limit number of user's profile to collect info from (now: hard coded)
POST_LIMIT_USER = 50  # number of posts to go through to collect communities' names and links when on user profile
PAGINATION_LIMIT = 2  # Optional: number of pages to consider when collecting the most active users of a community ('Members'->'Most contribution'). Decided to set at 10.

## Paths and filenames
DATA_OUTPUT_DIR = "data_output"  # directory for data output
os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)  # ensure the data output directory exists

# General patterns of co-occurrence:
USERNAMES_BY_KEYWORD =  os.path.join(DATA_OUTPUT_DIR, "usernames_by_keyword.json")  # file with usernames by a keyword; cols "username", "keyword", "post_count"
PROFILES_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_data.json")  # file with user'profile info; cols "username", "tags", "demographics", "bio", "commmunities"
UNIQUE_COMM_LIST =  os.path.join(DATA_OUTPUT_DIR, "all_communities.json")  # file containg set of communities; cols "community_name", "community_url"

# Community-specific patterns of co-occurrence:
MEMBERS_BY_COMM =  os.path.join(DATA_OUTPUT_DIR, "members_by_comm.json")  # file with usernames by a community; cols "community_name", "community_url", "username"
PROFILES_BY_COMM_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_by_comm_data.json")  # file with profile info of communities' members; ; cols "username", "tags", "demographics", "bio", "commmunity"
COMM_LIST_METADATA = os.path.join(DATA_OUTPUT_DIR, "unique_comm_list_metadata.json")  # unique community list extended by metadata

## Define CSS selectors
SELECTORS = {
    # login
    "login_email": "#email",
    "login_password": "#password",
    "login_button": "button[data-testid='log-in-button']",

    # search by a keyword
    "search_input": "input[placeholder='Search HealthUnlocked']",
    "post_items_search_results": "a[data-sentry-element='Link'][href^='/user/']",

    "next_page_button": "text=Next page", # pagination
    "show_more_posts_button": "button:has-text('Show more posts')",  # show more

    "community_card_username": ".community-member-card__username",  # user's posts on a community's page
    "meta_text_wrapper": "div[data-sentry-element='MetaTextWrapper']",  # community's name and link
    "replies_tab": "a[data-testid='profile-reply']",  # 'Replies' tab on a user's profile
    "community_metadata": "div[data-sentry-component='Details']",  # number of 'members' and 'posts'

    # user's profile
    "profile_tags": "ul[data-sentry-component='HealthTags'] li a",
    "profile_bio": "div[data-sentry-component='ProfileBio']",
    "post_items": "div[data-sentry-element='PostItem']",

    # demographic info
    "profile_demographics_joined": "div[data-testid='profile__about_joined']",
    "profile_demographics_age": "div[data-testid='profile__about_age']",
    "profile_demographics_gender": "div[data-testid='profile__about_gender']",
    "profile_demographics_country": "div[data-testid='profile__about_country']",
    "profile_demographics_ethnicity": "div[data-testid='profile__about_ethnicity']",
}
