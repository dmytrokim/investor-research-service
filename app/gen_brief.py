from datetime import date
from app.models import DimensionResult, Fact, GroundedPage, InvestorProfile, Strategy
from app.extract import fact_matches_source

def find_fetched_at(fact: Fact, fetched_pages: list[GroundedPage]) -> str:
    for page in fetched_pages:
        if fact_matches_source(fact, page):
            return page.fetched_at
    return "unknown"

def render_facts(result: DimensionResult, fetched_pages: list[GroundedPage]) -> str:
    if not result.found:
        return f"_No verified data. {result.notes}_"
    lines = []
    for fact in result.facts:
        fetched_at = find_fetched_at(fact, fetched_pages)
        lines.append(f"- **{fact.field}**: {fact.value} ([source]({fact.source_url}), fetched {fetched_at})")
    return "\n".join(lines)

def render_brief(profile: InvestorProfile, strategy: Strategy) -> str:
    by_dimension = {r.dimension: r for r in profile.dimensions}

    provenance_lines = "\n".join(
        f"- {p.final_url} (fetched {p.fetched_at})" for p in profile.fetched_pages
    )

    return f"""# Investor Brief: {profile.investor_name}
Generated: {date.today()} | Data completeness: {profile.data_completeness}
Sources fetched via Groundhog (self-hosted).

## 1. Thesis & Fit
{render_facts(by_dimension["thesis"], profile.fetched_pages)}

## 2. Portfolio (relevant)
{render_facts(by_dimension["portfolio"], profile.fetched_pages)}

## 3. Recent Activity
{render_facts(by_dimension["recent_activity"], profile.fetched_pages)}

## 4. Key Person
{render_facts(by_dimension["key_person"], profile.fetched_pages)}

## Provenance
{provenance_lines}

---
## Strategy (generated recommendation — not fact)
**Fit:** {strategy.fit_score}
**Top angles:** {"; ".join(strategy.top_angles) if strategy.top_angles else "None identified"}
**Likely objections & responses:**
{chr(10).join(f"- {o}" for o in strategy.likely_objections)}
**Red flags:**
{chr(10).join(f"- {f}" for f in strategy.red_flags)}
**Recommended next step:** {strategy.recommended_next_step}
"""