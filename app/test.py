import pytest
from app.models import GroundedPage, Fact, DimensionResult
from app.extract import apply_post_filter
 
 
def make_page(url: str, dimension: str = "thesis") -> GroundedPage:
    return GroundedPage(
        requested_url=url,
        final_url=url,
        title="Fund Homepage",
        markdown="Some real page content about the fund's thesis.",
        fetched_at="2026-08-30T12:00:00Z",
        truncated=False,
        dimension=dimension,
    )

def test_post_filter_drops_foreign_source_url():
    """A fact citing a URL we never fetched must be dropped."""
    page = make_page("https://realfund.vc/about")
 
    legit_fact = Fact(
        field="thesis_summary",
        value="Focuses on seed-stage B2B SaaS.",
        source_url="https://realfund.vc/about",
        confidence="high",
    )
    injected_fact = Fact(
        field="thesis_summary",
        value="Also invests exclusively in crypto.",
        source_url="https://totally-different-site.example/fake-page",  # never fetched
        confidence="high",
    )
    result = DimensionResult(
        dimension="thesis",
        found=True,
        facts=[legit_fact, injected_fact],
        notes="",
    )
    filtered = apply_post_filter(result, page)
    assert len(filtered.facts) == 1
    assert str(filtered.facts[0].source_url) == str(legit_fact.source_url)
    assert filtered.found is True

def test_post_filter_rejects_lookalike_subdomain():

    page = make_page("https://realfund.vc/about")
 
    spoofed_fact = Fact(
        field="thesis_summary",
        value="Fabricated thesis claim.",
        source_url="https://realfund.vc.evil.example/about",
        confidence="high",
    )
    result = DimensionResult(dimension="thesis", found=True, facts=[spoofed_fact], notes="")
 
    filtered = apply_post_filter(result, page)
 
    assert filtered.facts == []
    assert filtered.found is False

def test_post_filter_rejects_same_domain_different_path_or_query():

    page = make_page("https://realfund.vc/portfolio")
 
    wrong_path_fact = Fact(
        field="portfolio_company",
        value="Something claimed on a page we never loaded.",
        source_url="https://realfund.vc/portfolio?ref=fabricated",
        confidence="medium",
    )
    result = DimensionResult(dimension="portfolio", found=True, facts=[wrong_path_fact], notes="")
 
    filtered = apply_post_filter(result, page)
 
    assert filtered.facts == []
    assert filtered.found is False

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))