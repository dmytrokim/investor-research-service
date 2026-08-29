## Wellcome to Investor Assistant service! 
This service will help you quickly and without much effort brief you about your enterprise and your choosen investor. 

The service takes an investor name (and optionally a domain), discovers candidate pages via deterministic path-guessing + SERP fallback, fetches them through a self-hosted Groundhog MCP server, extracts verified facts per dimension (thesis, portfolio, key_person, recent_activity) via Claude, and renders a sourced Markdown brief plus a generated outreach strategy.

!!!Keep in mind that you should not fully rely on AI to make decisions for you, this tool exists only to help you make one!!!
This serviece was biult while relying on AI-generated content, e.g. via "vibe-coding"

## Quick start
__Important:__ Service require [groundhog_mcp by dmytrome]("https://github.com/dmytrome/groundhog") to function. Set up first before proceeding.

This project uses environment variables for local configuration. An `example.env` file is provided with the required variable structure.
1. Copy the example file to create your own local `.env` file:
>`bash`
> cp example.env .env

>`example.env`
>ANTHROPIC_API_KEY = my_anthropic_key #paste your Claude API key here
>CDP_URL = http://127.0.0.1:9222 #groundhog default

2. Start service:
>`bash`
>python -m app.main

>Enter the investor name: __input_your_investor__
>Enter the domain (optional, press Enter to skip): __input_your_domain__

## Configuration
All possible configurations are located in `config.py`
>MODEL_ID = "claude-haiku-4-5-20251001" # Model used by default
>DISCOVERY_MODE = "serp"                #deterministic | serp | api NOT implemented
>DEBUG_MODE = False                     #Use to see raw json output

>EXTRACTION_MAX_TOKENS = 2048           
>STRATEGY_MAX_TOKENS = 2048 
>SERP_RESULT_LIMIT = 5                  # Max serp output
>GROUNDHOG_MIN_DELAY_MS = 5000          
>GROUNDHOG_MAX_TOKENS = 20000           # Max tokens for Groundhog responses
>GROUNDHOG_BLOCK_PRIVATE_IPS = True
>GROUNDHOG_USER_AGENT = "UA"
>SECURITY_DELAY_MS = 5000 
>MAX_CANDIDATES_PER_DIMENSION = 3

