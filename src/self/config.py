from environs import env

env.read_env()

API_ID = env.int("API_ID")
API_HASH = env.str("API_HASH")
ADMIN_ID = env.int("ADMIN_ID")
DISCUSSION_GROUP_ID = env.int("DISCUSSION_GROUP_ID")
NTFY_TOPIC_ID = env.str("NTFY_TOPIC_ID")
