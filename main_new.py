from helpers import login, read_json, write_to_json
from scrapers import get_usernames_by_keyword, get_user_profiles, get_members_of_community, get_member_profiles
from config import (GLOBAL_KEYWORDS, USERNAMES_BY_KEYWORD, POST_LIMIT_KEYWORD, 
                    PROFILES_DATA, UNIQUE_COMM_LIST, POST_LIMIT_USER, 
                    USER_PROFILE_LIMIT, USERNAMES_BY_COMM, COMM_LIST_METADATA, POST_LIMIT_MEMBERS, 
                    PROFILES_BY_COMM_DATA)

from playwright.sync_api import sync_playwright

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)  # True - for headless mode
        page = browser.new_page()

        try:
            login(page)
            ### 1) General Patterns

            ## --- Collect Usernames from Posts using a Keyword
            # get_usernames_by_keyword(page, GLOBAL_KEYWORDS, USERNAMES_BY_KEYWORD, POST_LIMIT_KEYWORD)

            ## --- Collect User Profiles and Create Unique Community List
            get_user_profiles(page, USERNAMES_BY_KEYWORD, PROFILES_DATA, UNIQUE_COMM_LIST, POST_LIMIT_USER)

            ### 2) Community-specific Patterns

            ## --- Collect Usernames from Communities of the Unique Community List
            # get_members_of_community(page, UNIQUE_COMM_LIST, USERNAMES_BY_COMM, COMM_LIST_METADATA, POST_LIMIT_MEMBERS)

            ## --- Collect User Profiles of Community Members
            # get_member_profiles(page, USERNAMES_BY_COMM, PROFILES_BY_COMM_DATA)
        finally:
            browser.close()