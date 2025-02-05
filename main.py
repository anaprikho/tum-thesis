from playwright.sync_api import sync_playwright

from helpers import login
from scrapers import scrape_usernames_by_keyword, scrape_user_profiles, scrape_community_members, scrape_member_profiles
from config import (GLOBAL_KEYWORDS, CATEGORIES_OF_KEYWORDS, USERNAMES_BY_KEYWORD, USERNAMES_BY_KEYWORD_LIMIT, 
                    GENERAL_PROFILES_DATA, UNIQUE_COMM_LIST, POSTS_BY_USER_LIMIT, 
                    MEMBERS_BY_COMM, PAGINATION_LIMIT, 
                    PROFILES_BY_COMM_DATA)

def scrape_general_patterns(page):
    # Collect Usernames from Posts using a Keyword
    scrape_usernames_by_keyword(page, GLOBAL_KEYWORDS, CATEGORIES_OF_KEYWORDS, USERNAMES_BY_KEYWORD, USERNAMES_BY_KEYWORD_LIMIT)

    # Collect User Profiles and Create Unique Community List
    scrape_user_profiles(page, USERNAMES_BY_KEYWORD, GENERAL_PROFILES_DATA, UNIQUE_COMM_LIST, POSTS_BY_USER_LIMIT)    

def scrape_community_patterns(page):
    # Collect Usernames from Communities of the Unique Community List
    scrape_community_members(page, UNIQUE_COMM_LIST, MEMBERS_BY_COMM, PAGINATION_LIMIT)

    # Collect User Profiles of Community Members
    scrape_member_profiles(page, MEMBERS_BY_COMM, PROFILES_BY_COMM_DATA)


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)  # True - for headless mode
        page = browser.new_page()
        try:
            login(page)

            #  1) General Patterns
            # scrape_usernames_by_keyword(page, GLOBAL_KEYWORDS, CATEGORIES_OF_KEYWORDS, USERNAMES_BY_KEYWORD, USERNAMES_BY_KEYWORD_LIMIT)
            # scrape_user_profiles(page, USERNAMES_BY_KEYWORD, GENERAL_PROFILES_DATA, UNIQUE_COMM_LIST, POSTS_BY_USER_LIMIT)
            # scrape_general_patterns(page)

            # 2) Community-specific Patterns
            # scrape_community_members(page, UNIQUE_COMM_LIST, MEMBERS_BY_COMM, PAGINATION_LIMIT)
            scrape_member_profiles(page, MEMBERS_BY_COMM, PROFILES_BY_COMM_DATA)
            # scrape_community_patterns(page)
        finally:
            browser.close()