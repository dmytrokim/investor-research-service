# Wellcome to Investor Assistant service! 
This service will help you quickly and without much effort brief you about your enterprise and your choosen investor. 

The service takes an investor name (and optionally a domain), discovers candidate pages via deterministic path-guessing + SERP fallback, fetches them through a self-hosted Groundhog MCP server, extracts verified facts per dimension (thesis, portfolio, key_person, recent_activity) via Claude, and renders a sourced Markdown brief plus a generated outreach strategy.

>__Keep in mind that you should not fully rely on AI to make decisions for you — this tool exists only to help you make one.__

This service was built while relying on AI-generated content, e.g. via "vibe-coding."

## What it does
You give it an investor's name (and, optionally, a domain). It:
1. __Discovers candidate pages__ — guesses likely URLs on the investor's own site (`/about`, `/portfolio`, `/team`, etc.) if you gave a domain, guesses likely profile URLs on a handful of known investor-data aggregators (Crunchbase, LinkedIn, Wellfound, Dealroom), and falls back to real search queries (via Groundhog's search tool) to fill in whatever the guesses miss.
2. __Fetches each candidate__ through a self-hosted [Groundhog](https://github.com/dmytrome/groundhog) MCP server
3. __Extracts verified facts__ from each fetched page via Claude, organized into four dimensions: __thesis__ (what they invest in and why), __portfolio__ (companies they've backed), __key_person__ (who's behind the fund), and __recent_activity__ (what they've done lately).
4. __Filters out anything not traceable to an actually-fetched page__ — a post-filter barrier rejects any fact whose source doesn't match a real, fetched URL, and rejects empty values.
5. __Synthesizes a profile__ with an honest `data_completeness` rating (`rich` / `partial` / `sparse`) based on how many dimensions actually turned up real facts.
6. __Generates an outreach strategy__ — a fit assessment, angles, likely objections, and red flags.
7. __Writes a sourced Markdown brief__ to `output/brief_<investor_name>.md`

## Quick start
__Important:__ this service requires [Groundhog](https://github.com/dmytrome/groundhog) to function. Set that up first before proceeding.

This project uses environment variables for local configuration. An `example.env` file is provided with the required variable structure.
1. Copy the example file to create your own local `.env` file:

```bash
cp example.env .env
```

`example.env`
```env
ANTHROPIC_API_KEY=my_anthropic_key   # paste your Claude API key here
CDP_URL=http://127.0.0.1:9222        # groundhog default
```

2. Start service:

```bash
python -m app.main
```
 
```
Enter the investor name: <your investor>
Enter the domain (optional, press Enter to skip): <your domain>
```
The generated brief is written to `output/brief_<investor_name>.md`.

## Configuration
All configuration lives in `config.py`:
 
```python
MODEL_ID = "claude-haiku-4-5-20251001"  # model used by default
DISCOVERY_MODE = "serp"                 # deterministic | serp | api — api not yet implemented
DEBUG_MODE = False                      # set True to see raw JSON output from extraction/strategy calls
EXTRACTION_MAX_TOKENS = 2048
STRATEGY_MAX_TOKENS = 2048
SERP_RESULT_LIMIT = 5                   # max SERP hits requested per query
GROUNDHOG_MIN_DELAY_MS = 5000           # Groundhog's own per-domain rate limit
GROUNDHOG_MAX_TOKENS = 20000            # max tokens for Groundhog responses
GROUNDHOG_BLOCK_PRIVATE_IPS = True
GROUNDHOG_USER_AGENT = "UA"
SECURITY_DELAY_MS = 5000                # delay between fetch retries
MAX_CANDIDATES_PER_DIMENSION = 3
```
`DISCOVERY_MODE` controls how aggressively the service searches:
- `deterministic` — only guessed URLs (no search calls at all)
- `serp` — guessed URLs, plus real search queries to fill gaps (default)
- `api` — reserved for a future dedicated search-API integration; not implemented yet

## Limitations

- Some sources (Crunchbase, LinkedIn) are frequently blocked by bot-detection walls and may not return usable content.
- `DISCOVERY_MODE`'s `api` option is a placeholder and not yet implemented.
- Most likely SERP limitation: short/acronym investor names (e.g. "MHP") can resolve to a completely different, equally legitimate real company sharing the same acronym (mhpinvestors.com)


