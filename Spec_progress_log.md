# Testing and milestones
- __M0/T0__: is __Done__
- __M1__ is __Done__
- __M2__: `det_path.py` and `discovery.py`, post filter in `extract.py` -> `fetch.py` to call serp
    - T2: is __Done__
    - T3: is __Done__ via `python -m pytest app/test.py -v`
- __M3__: is __Done__ via `extract.py`: `build_investor_profille` and `compute_data_completeness`
- __M4__: is __Done__ Strategy generated from template in `extract.py` and brief in `gen_brief.py`
    - T4: is __Done__ via `extract.py` `compute_data_completeness`
    - T5: is __Done__ via `quality_valid.py` and by defaulting or returning clear error. Also added debug mode for easier diagnosis.
    - T6: is __Particularly done__ Rate-limit excists in `config.py`: delay between retries and new fetches. None are less then 5 sec by default. No logs yet implemented.
- __M5__: is __Not Done__

# By paragraph
## 5 — Groundhog MCP setup
__Done.__ `connect()` in `fetch.py` spins up `groundhog-mcp` via `stdio_client`, passes correct .env values. `status()` check gates the rest of the run.
## 6.1 — Input handling
__Done.__ `investor_name` required with a hard error on empty input; `domain` optional, resolved via SERP (`resolve_domain_from_name`) when omitted(Порожній ввід → чітка помилка.)
## 6.2-A — Deterministic discovery
__Mostly done.__
- __Done:__ `discover_urls(domain, investor_name, domain_is_trusted)` builds `DET_PATHS` candidates +  `aggregator_candidates()` guesses. Added **`domain_is_trusted` in version 0.2: `DET_PATHS` guessing now only runs when the domain came directly from the user, not from SERP resolution. Resolved domain often turns out to be a third-party site with no real nav structure of its own, so guessing `/about`, `/team`, etc. against it just pointless. Confirmed through testing with names only(ex. Oleksandr Kolb - itarena.ua, startupintros.com and mhp(not uppercase MHP) to mhpinvestors.com)
- __Done:__ `aggregator_candidates()` now includes both person- and org-type guesses
- __Done:__ `KNOWN_AGGREGATOR_JUNK_TITLES` hardcoded agregators junk pages. They unice enough to pass through `is_empty_page` check, so SERP fallback never trigers, leaving dimension filled with wrong data and just burning an extraction call every run.
- __Needs conformation:__ `DET_PATHS` is English-only, so localized sites (like MHP's `/uk/pro-kompaniiu`) are unreachable by design. Should i fix it?
- __Note:__ aggregator guessing (`aggregator_candidates`, `slugify`, the Crunchbase/LinkedIn/Wellfound patterns) is a feature designed from `crunchbase.com/organization/{slug}`s example. 
## 6.2-B — SERP discovery
- __Done:__ `SERP_QUERIES` per-dimension query templates, `build_fallback_queries` (skips `{domain}`-templates when no domain), the fallback loop in `_run()`.
- __Done:__ domain-resolution credibility check — `hit_looks_like_investor` (vocabulary match) __and__ `hit_mentions_investor` (investor's own name tokens in the hit)
- __Note:__ used `session.call_tool("search", ...)`, groundhog native tool
## 6.3 — Fetch
- __Done__ `fetch_candidates` fetches each candidate via `read_url`, with a retry-with-backoff on failure inside `get_url`.
## 6.4 — Extraction
- __Done:__ During testing extraction prompt was changed to handle several issues, like extracting general definitions from ex. Wikipedia
## 6.5 — Post-filter
- __Done:__ Both conditions enforced: `source_url` must match the fetched page, __and__ `value` must be non-empty, via `apply_post_filter`
## 6.7 — Strategy generation
- __Done:__ `DATA_COMPLETENESS` is now passed to the model, so now it gets real computed value instead of guessing its own.
- __Done:__ Geography/TLD inference rule. Fixed issue where investor geographical focus was guessed wrong(ex. Toloka.vc is located in Russia)
## 6.8 — Brief output
- __Done:__ `main.py` writes `output/brief_<investor_name>.md` to disk.
## §13 — Config
__Mostly done.__ 
`DISCOVERY_MODE` (`deterministic | serp | api`) is fully wired into `_run()`'s two branch points — domain resolution and the dimension-fallback loop. `"deterministic"` mode with no domain given proceeds on aggregator-only guesses. `"api"` raises `NotImplementedError` clearly rather than silently no-op'ing. `api` mode itself has no implementation yet. 

