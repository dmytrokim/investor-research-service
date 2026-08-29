from urllib.parse import urlparse
from pydantic import HttpUrl
from app.models import DiscoveryCandidate
from app.det_path import DET_PATHS
from collections import Counter
from app.models import GroundedPage
import re

ALL_DIMENSIONS = ["thesis", "portfolio", "key_person", "recent_activity"]
INVESTOR_SIGNAL_KEYWORDS = ["venture", "capital", "fund", "invest", "portfolio", "vc", "partner", "syndicate", "angel",]

SERP_QUERIES = {
    "identity": [
        '"{investor_name}" investor',
        '"{investor_name}" venture capital',
        '"{investor_name}" investments',
    ],

    "thesis": [
        '"{investor_name}" {domain} investment strategy',
        '"{investor_name}" investment strategy',
        '"{investor_name}" invests in',
    ],

    "portfolio": [
        '"{investor_name}" {domain} portfolio',
        '"{investor_name}" portfolio',
        '"{investor_name}" invested in',
    ],

    "key_person": [
        '"{investor_name}" {domain} team',
        '"{investor_name}" founders partners',
        '"{investor_name}" leadership team',
    ],

    "recent_activity": [
        '"{investor_name}" {domain} news',
        '"{investor_name}" investment 2026',
        '"{investor_name}" invested 2026',
    ],
}

AGGREGATOR_HOSTS = {
    "crunchbase.com",
    "linkedin.com",
    "dealroom.co",
    "wellfound.com",
}

def is_aggregator_host(netloc: str) -> bool:
    netloc = netloc.lower()
    return any(netloc == host or netloc.endswith("." + host) for host in AGGREGATOR_HOSTS)

def build_fallback_queries(investor_name: str, domain: str | None, dimension: str) -> list[str]:
    queries = []
    for template in SERP_QUERIES[dimension]:
        if "{domain}" in template and not domain:
            continue
        queries.append(template.format(investor_name=investor_name, domain=domain or ""))
    return queries

def discover_urls(domain: str | None, investor_name: str) -> list[DiscoveryCandidate]:
    candidates = []

    if domain:
        for dimension, paths in DET_PATHS.items():
            for path in paths:
                candidates.append(
                    DiscoveryCandidate(url=f"https://{domain}{path}", dimension=dimension, source="deterministic")
                )

    candidates.extend(aggregator_candidates(investor_name))
    return candidates

def normalize_domain(domain: str) -> str:
    domain = domain.strip()
    domain = domain.removeprefix("https://")
    domain = domain.removeprefix("http://")
    return domain.rstrip("/")

def is_same_domain(url: str, domain: str) -> bool:
    host = urlparse(url).netloc
    return host == domain or host.endswith("." + domain)

def filter_hits_by_domain(hits, domain):
    return [hit for hit in hits if is_same_domain(hit["url"], domain)]

def hits_to_candidates(hits, dimension: str) -> list[DiscoveryCandidate]:
    candidates = []
    for hit in hits:
        candidates.append(
            DiscoveryCandidate(
                url=HttpUrl(hit["url"]),
                dimension=dimension,
                source="serp",
            )
        )
    return candidates

def slugify(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")

def aggregator_candidates(investor_name: str) -> list[DiscoveryCandidate]:
    slug = slugify(investor_name)
    return [
        DiscoveryCandidate(
            url=f"https://www.crunchbase.com/person/{slug}",
            dimension="key_person",
            source="deterministic",
        ),
        DiscoveryCandidate(
            url=f"https://wellfound.com/u/{slug}",
            dimension="key_person",
            source="deterministic",
        ),
        DiscoveryCandidate(
            url=f"https://dealroom.co/investors/{slug}/",
            dimension="key_person",
            source="deterministic",
            ),  
    ]