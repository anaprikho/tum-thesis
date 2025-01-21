import os

DATA_OUTPUT_DIR = "data_output"  # directory for data output
os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)  # ensure the data output directory exists

GLOBAL_KEYWORDS = ["depression", "anxiety"]  # define keywords for global search on HU to collect usernames
POST_LIMIT_KEYWORD = 70  # Optional: limit number of posts when collecting usernames by a keyword
USER_PROFILE_LIMIT = 6  # Optinal: limit number of user's profile to collect info from
POST_LIMIT_USER = 100  # number of posts to go through to collect communities' names and links when on user profile
POST_LIMIT_MEMBERS = 10  # Optional: number of most active users of a community to collect ('Members'->'Most contribution')

# General patterns of co-occurrence:
USERNAMES_BY_KEYWORD =  os.path.join(DATA_OUTPUT_DIR, "usernames_by_keyword.json")  # file with usernames by a keyword; cols "username", "keyword", "post_count"
PROFILES_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_data.json")  # file with user'profile info; cols "username", "tags", "demographics", "bio", "commmunities"
UNIQUE_COMM_LIST =  os.path.join(DATA_OUTPUT_DIR, "unique_comm_list.json")  # file containg set of communities; cols "community_name", "community_url"

# Community-specific patterns of co-occurrence:
USERNAMES_BY_COMM =  os.path.join(DATA_OUTPUT_DIR, "usernames_by_comm_data.json")  # file with usernames by a community; cols "community_name", "community_url", "username"
PROFILES_BY_COMM_DATA =  os.path.join(DATA_OUTPUT_DIR, "profiles_by_comm_data.json")  # file with profile info of communities' members; ; cols "username", "tags", "demographics", "bio", "commmunity"
COMM_LIST_METADATA = os.path.join(DATA_OUTPUT_DIR, "unique_comm_list_metadata.json")  # unique community list extended by metadata