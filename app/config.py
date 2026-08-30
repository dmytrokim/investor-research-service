MODEL_ID = "claude-haiku-4-5-20251001"  # model used by default
DISCOVERY_MODE = "serp" #deterministic | serp | api
DEBUG_MODE = True   # Set True to see raw JSON output of your fetches

EXTRACTION_MAX_TOKENS = 2048
STRATEGY_MAX_TOKENS = 2048
SERP_RESULT_LIMIT = 5   # Max SERP hits requested per query
GROUNDHOG_MIN_DELAY_MS = 5000   # Groundhog's own per-domain rate limit
GROUNDHOG_MAX_TOKENS = 20000    # Max tokens for Groundhog responses
GROUNDHOG_BLOCK_PRIVATE_IPS = True
GROUNDHOG_USER_AGENT = "UA"
SECURITY_DELAY_MS = 5000    #Delay between retries
MAX_CANDIDATES_PER_DIMENSION = 3

