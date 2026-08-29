from app.models import DimensionResult, InvestorProfile, Strategy, GroundedPage, Fact
from app.discovery import ALL_DIMENSIONS
import json
from pydantic import ValidationError
from collections import defaultdict
from app.yharvest_context import YHARVEST_CONTEXT
from app import config
from string import Template


EXTRACTION_SYSTEM_PROMPT = Template("""You extract verified facts about ONE SPECIFIC TARGET INVESTOR from the text of ONE web page that was already fetched for you. You have NO web access.

TARGET INVESTOR:
$investor_name

TARGET DIMENSION:
$dimension

SOURCE_URL:
$source_url

Rules — follow exactly:

1. Use ONLY the page content provided below. Do not use outside knowledge.
2. The target investor is exactly "$investor_name". Extract facts only when they are explicitly about this target investor, or about an organization/person that the page explicitly connects to this target investor.
3. The page's canonical URL is SOURCE_URL. Every fact MUST use exactly this SOURCE_URL as its source_url. Never output any other URL.
4. Extract only facts relevant to TARGET_DIMENSION.
5. If the page has nothing relevant to the TARGET INVESTOR and TARGET_DIMENSION, return found=false with empty facts.
6. Do NOT treat a page as relevant merely because:
   - it was discovered using the target investor's domain;
   - its URL contains a generic path such as /people, /team, /portfolio, /news, or /blog;
   - it discusses the same industry, event, geography, or organization without explicitly connecting the content to the target investor.
7. If the page discusses another person, company, investor, fund, or organization, do NOT extract facts about that entity unless the page explicitly establishes its connection to the target investor.
8. A page discussing investments, activities, achievements, or opinions of OTHER investors or people is NOT evidence about the target investor.
9. Only extract facts specific to THIS target investor's actual thesis, holdings, people, affiliations, or activity.
10. Only extract a portfolio company if the page explicitly connects that company to the target investor or to an investment organization that the target investor is explicitly identified as representing.
11. Do NOT infer relationships. For example, the following are NOT sufficient evidence:
   - "Investor X attended an event where Company Y was discussed."
   - "Company Y appears on the same page as Investor X."
   - "Investor X works in the same industry as Company Y."
   - "Investor X is associated with an organization that mentions Company Y somewhere else."
   The connection must be explicitly stated on the page.
12. Do NOT extract generic definitions, dictionary meanings, or explanations of what TARGET_DIMENSION means as a general concept (e.g. "what is a portfolio" or "what a team leader does"). If the page only defines or explains the term itself rather than describing this specific investor's concrete situation, treat it as found=false.
13. If a page contains a long, repetitive list of similar items (e.g., dozens of portfolio companies or many news items), do NOT enumerate every single one. Extract at most 8 of the most notable/significant items as individual facts, plus ONE aggregate fact summarizing the rest.
14. Do not convert general website/event activity into investor activity. For example, a startup competition announced on an investor's associated website is not evidence that the investor personally launched, invested in, or participated in it unless the page explicitly says so.
15. If the page mentions the target investor only incidentally but the substantive content concerns another entity, return found=false.
16. If the page contains information about the target investor but it does not belong to TARGET_DIMENSION, do not extract it. Return found=false.
17. Confidence describes how explicitly the page supports the fact:
   - high = directly and unambiguously stated;
   - medium = supported by the page but requires a small amount of interpretation;
   - low = weakly supported.
   Do not use low confidence to justify an unsupported inference.
18. Output ONLY valid JSON matching this shape, no prose, no markdown fences: {"dimension": "...", "found": true/false, "facts": [{"field": "...", "value": "...", "source_url": "...", "confidence": "high"|"medium"|"low"}], "notes": "..."}
"""
)
STRATEGY_PROMPT = """
You are a fundraising strategist. Given a VERIFIED investor profile and a fixed company
context, produce a strategy for approaching this investor.

Rules:
1. Never present company-context facts as investor facts.
2. Never present investor-profile facts as company facts.
3. Base every claim ONLY on the provided profile facts. Do not invent investor facts.
4. This is judgment, not fact — be explicit where you infer.
5. Strategic recommendations may be inferences, but the reasoning must be grounded in the provided investor profile and company context.
6. If data_completeness is "sparse", start with a clear caveat/warning.
7. Direct and concrete. No filler. Max 3 angles.
8. Do not claim that the investor has invested in a sector/company unless that is explicitly present in the VERIFIED INVESTOR PROFILE.
9. Do not claim a geographic, stage, check-size, or portfolio preference unless supported by the VERIFIED INVESTOR PROFILE.
10. Never infer geography, nationality, ownership, or political alignment from a domain name, TLD, or URL structure — including country-code TLDs (e.g. ".ua", ".de", ".io"). A domain is a registration choice, not proof of where an organization operates. However it does NOT restrict you from stating geography, location, or regional focus that is evident from the context of the verified facts — place names, named institutions, described events, or regions mentioned in the extracted content are legitimate evidence, not inference. If the verified facts contain no such textual evidence at all, treat geography as unknown — do not guess, and do not present a guess as a red flag.
11. Output ONLY valid JSON matching this exact shape, no prose, no markdown fences, for fit_score use ONLY PRESENTED VALUES: {"thesis_fit": "...", "fit_score": "strong"|"possible"|"weak"|"no_fit", "top_angles": ["...", "..."], "likely_objections": ["...", "..."], "red_flags": ["...", "..."], "recommended_next_step": "..."}
"""



def build_extraction_prompt(page):
    return f"""SOURCE_URL: {page.final_url}
TARGET_DIMENSION: {page.dimension}
PAGE CONTENT:
{page.markdown}"""

def strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0]
    return text.strip()


def call_extraction(client, investor_name, page) -> DimensionResult:
    prompt = build_extraction_prompt(page)
    system_prompt = EXTRACTION_SYSTEM_PROMPT.substitute(
        investor_name = investor_name,
        dimension = page.dimension,
        source_url = page.final_url,
    )
    try:
        response = client.messages.create(
            model=config.MODEL_ID,
            max_tokens=config.EXTRACTION_MAX_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text
        cleaned = strip_markdown_fences(raw_text)
        if config.DEBUG_MODE:
            print("=== RAW CLEANED TEXT ===")   # debug
            print(repr(cleaned)) 
            print("=== END ===")
        data = json.loads(cleaned)
        return DimensionResult(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Failed to parse extraction result for {page.final_url}: {e}")
        return DimensionResult(dimension=page.dimension, found=False, facts=[], notes="Extraction failed: could not parse model output.")

def call_strategy(client, profile: InvestorProfile) -> Strategy:
    prompt = build_strategy_prompt(profile)
    try:
        response = client.messages.create(
            model=config.MODEL_ID,
            max_tokens=config.STRATEGY_MAX_TOKENS,
            system=STRATEGY_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text
        cleaned = strip_markdown_fences(raw_text)
        if config.DEBUG_MODE:
            print("=== RAW CLEANED TEXT ===") #debug, rm later
            print(repr(cleaned))
            print("=== END ===")
        data = json.loads(cleaned)
        return Strategy(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Failed to parse strategy result: {e}")
        return Strategy(thesis_fit="", fit_score="no_fit", top_angles=[], likely_objections=[], red_flags=[], recommended_next_step="Strategy generation failed: could not parse model output.")

        
def fact_matches_source(fact: Fact, page: GroundedPage) -> bool:
    return str(fact.source_url) == str(page.final_url)

def fact_is_valid(fact: Fact, page: GroundedPage) -> bool:
    return fact_matches_source(fact, page) and bool(fact.value.strip())

def apply_post_filter(result: DimensionResult, page: GroundedPage) -> DimensionResult:
    valid_facts = [fact for fact in result.facts if fact_is_valid(fact, page)]
    return DimensionResult(
        dimension=result.dimension,
        found=len(valid_facts) > 0,
        facts=valid_facts,
        notes=result.notes,
    )

def merge_dimension_results(results, dimension):
    all_facts = []
    for r in results:
        all_facts.extend(r.facts)

    found = any(r.found for r in results)
    if found:
        notes_parts = [r.notes for r in results if r.found and r.notes]
    else:
        notes_parts = [r.notes for r in results if r.notes]
    notes = " | ".join(notes_parts)

    return DimensionResult(dimension=dimension, found=found, facts=all_facts, notes=notes)

def merge_all_dimensions(results: list[DimensionResult]) -> list[DimensionResult]:
    grouped = defaultdict(list)
    for r in results:
        grouped[r.dimension].append(r)

    merged = []
    for dimension in ALL_DIMENSIONS:
        if dimension in grouped:
            merged.append(merge_dimension_results(grouped[dimension], dimension))
        else:
            merged.append(DimensionResult(
                dimension=dimension, found=False, facts=[],
                notes="No candidate pages survived quality filtering for this dimension.",
            ))
    return merged

def compute_data_completeness(dimension_results: list[DimensionResult]) -> str:
    found_count = sum(1 for r in dimension_results if r.found)
    if found_count >= 3:
        return "rich"
    elif found_count >= 1:
        return "partial"
    else:
        return "sparse"

def build_investor_profile(investor_name: str, domain: str, pages: list[GroundedPage], results: list[DimensionResult]) -> InvestorProfile:
    merged_results = merge_all_dimensions(results)
    completeness = compute_data_completeness(merged_results)

    return InvestorProfile(
        investor_name=investor_name,
        domain=domain,
        dimensions=merged_results,
        fetched_pages=pages,
        data_completeness=completeness,
    )



def build_strategy_prompt(profile: InvestorProfile) -> str:
    dimensions_json = json.dumps([d.model_dump(mode="json") for d in profile.dimensions], indent=2)
    return f"""OUR COMPANY (Yharvest):
{YHARVEST_CONTEXT}

INVESTOR PROFILE ({profile.investor_name}):
DATA_COMPLETENESS: {profile.data_completeness}

DIMENSIONS:
{dimensions_json}"""