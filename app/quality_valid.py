from collections import Counter, defaultdict
from app.models import GroundedPage
from app.discovery import ALL_DIMENSIONS, is_known_aggregator_junk

def count_titles(pages):
    title = [page.title for page in pages]
    return Counter(title)

def is_empty_page(page: GroundedPage, title_counts: Counter, min_words: int = 30) -> bool:
    if is_known_aggregator_junk(page):
        return True
    word_count = len(page.markdown.split())
    is_too_short = word_count < min_words
    is_duplicate_title = title_counts[page.title] > 1
    return is_too_short or is_duplicate_title

def group_by_dimension(pages: list[GroundedPage]) -> dict[str, list[GroundedPage]]:
    groups = defaultdict(list)
    for page in pages:
        groups[page.dimension].append(page)
    return groups


def dimensions_needing_fallback(pages: list[GroundedPage]) -> set[str]:
    groups = group_by_dimension(pages)
    title_counts = count_titles(pages)
    needs_fallback = set()

    for dimension in ALL_DIMENSIONS:
        dim_pages = groups.get(dimension, [])
        if all(is_empty_page(p, title_counts) for p in dim_pages):
            needs_fallback.add(dimension)

    return needs_fallback

def dedupe_candidates(candidates, already_fetched_pages):
    already_fetched_urls = {str(p.final_url) for p in already_fetched_pages}
    return [c for c in candidates if str(c.url) not in already_fetched_urls]

