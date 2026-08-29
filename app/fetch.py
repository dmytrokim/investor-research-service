import asyncio
import os
from urllib.parse import urlparse
from app.models import GroundedPage
from mcp import ClientSession, StdioServerParameters, stdio_client
from contextlib import asynccontextmanager
from app.quality_valid import dimensions_needing_fallback, dedupe_candidates
from app.discovery import build_fallback_queries, filter_hits_by_domain, hits_to_candidates, discover_urls, is_aggregator_host, INVESTOR_SIGNAL_KEYWORDS, SERP_QUERIES
from app import config

async def _run(investor_name, domain):
    async with connect() as session:
        status = await get_status(session)
        if status is None or not status["browser_reachable"]:
            print(status["hint"] if status else "Could not reach Groundhog status endpoint.")
            return [], domain

        if domain is None:
            domain = await resolve_domain_from_name(session, investor_name)
            if domain is None:
                print(f"Could not resolve a domain for {investor_name!r} via search.")
                return [], None

        candidates = discover_urls(domain, investor_name)
        pages = await fetch_candidates(session, candidates)

        needs_fallback = dimensions_needing_fallback(pages)
        for dimension in needs_fallback:
            serp_candidates = []
            for query in build_fallback_queries(investor_name, domain, dimension):
                search_result = await get_search(session, query)
                if search_result is None or not search_result["hits"]:
                    continue
                filtered_hits = filter_hits_by_domain(search_result["hits"], domain)
                if filtered_hits:
                    serp_candidates = hits_to_candidates(filtered_hits, dimension)
                    break
            serp_candidates = dedupe_candidates(serp_candidates, pages)
            serp_pages = await fetch_candidates(session, serp_candidates[:config.MAX_CANDIDATES_PER_DIMENSION])
            pages.extend(serp_pages)

        return pages, domain

def fetch_pages(investor_name, domain):
    return asyncio.run(_run(investor_name, domain))

@asynccontextmanager
async def connect():
    server_params = StdioServerParameters(
        command="uvx",
        args=["groundhog-mcp"],
        env={
            "CDP_URL": os.environ.get("CDP_URL", "http://127.0.0.1:9222"),
            "GROUNDHOG_MIN_DELAY_MS": str(config.GROUNDHOG_MIN_DELAY_MS),
            "GROUNDHOG_MAX_TOKENS": str(config.GROUNDHOG_MAX_TOKENS),
            "GROUNDHOG_BLOCK_PRIVATE_IPS": str(config.GROUNDHOG_BLOCK_PRIVATE_IPS),
            "USER_AGENT": str(config.GROUNDHOG_USER_AGENT),
        },
    )
    async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

async def get_status(session):
    result = await session.call_tool("status", {})
    if result.is_error:
        error_message = result.content[0].text
        print(f"status() call failed: {error_message}")
        return None
    return result.structured_content

async def get_url(session, url, retries=1):
    for attempt in range(retries + 1):
        result = await session.call_tool("read_url", {"url": url})
        if not result.is_error:
            return {
                "title": result.structured_content["title"],
                "final_url": result.structured_content["final_url"],
                "markdown": result.structured_content["markdown"],
                "fetched_at": result.structured_content["fetched_at"],
                "truncated": result.structured_content["truncated"],
            }
        error_message = result.content[0].text
        print(f"Attempt {attempt + 1} failed for {url}: {error_message}")
        if attempt < retries:
            await asyncio.sleep(config.SECURITY_DELAY_MS/1000)
    return None

async def get_search(session, query, limit=config.SERP_RESULT_LIMIT):
    result = await session.call_tool("search", {"query": query, "limit": limit})
    if result.is_error:
        error_message = result.content[0].text
        print(f"Search failed for {query!r}: {error_message}")
        return None
    return result.structured_content

async def fetch_candidates(session, candidates):
    pages = []
    for i, candidate in enumerate(candidates):
        page_data = await get_url(session, str(candidate.url))
        if page_data is not None:
            page = GroundedPage(
                requested_url=str(candidate.url),
                final_url=page_data["final_url"],
                title=page_data["title"],
                markdown=page_data["markdown"],
                fetched_at=page_data["fetched_at"],
                truncated=page_data["truncated"],
                dimension=candidate.dimension,
            )
            pages.append(page)
        if i < len(candidates) - 1:
            await asyncio.sleep(config.SECURITY_DELAY_MS/1000)
    return pages

def hit_looks_like_investor(hit) -> bool:
    text = f"{hit.get('title', '')} {hit.get('snippet', '')}".lower()
    return any(keyword in text for keyword in INVESTOR_SIGNAL_KEYWORDS)

def hit_mentions_investor(hit, investor_name: str) -> bool:
    text = f"{hit.get('title', '')} {hit.get('snippet', '')}".lower()
    name_tokens = [t for t in investor_name.lower().split() if len(t) > 2]
    return any(token in text for token in name_tokens)

async def resolve_domain_from_name(session, investor_name):
    for template in SERP_QUERIES["identity"]:
        query = template.format(investor_name=investor_name)
        search_result = await get_search(session, query)
        if search_result is None or not search_result["hits"]:
            continue
        for hit in search_result["hits"]:
            netloc = urlparse(hit["url"]).netloc
            if is_aggregator_host(netloc):
                continue
            if hit_looks_like_investor(hit) and hit_mentions_investor(hit, investor_name):
                return netloc
    return None
