from pydantic import BaseModel, HttpUrl
from typing import Literal

Dimension = Literal[
    "thesis",
    "portfolio",
    "recent_activity",
    "key_person",
]

DiscoverySource = Literal[
    "deterministic",
    "serp",
    "api",
]

class DiscoveryCandidate(BaseModel):
    url: HttpUrl
    dimension: Dimension
    source: DiscoverySource
    
class GroundedPage(BaseModel):
    """Те, що повернув Groundhog по одному URL."""
    requested_url: str
    final_url: HttpUrl
    title: str | None
    markdown: str
    fetched_at: str
    truncated: bool
    dimension: str

class Fact(BaseModel):
    field: str
    value: str
    source_url: HttpUrl
    confidence: Literal["high", "medium", "low"]

class DimensionResult(BaseModel):
    dimension: str
    found: bool
    facts: list[Fact]
    notes: str = ""

class InvestorProfile(BaseModel):
    investor_name: str
    domain: str | None
    dimensions: list[DimensionResult]
    fetched_pages: list[GroundedPage]
    data_completeness: Literal["rich", "partial", "sparse"]

class Strategy(BaseModel):
    thesis_fit: str
    fit_score: Literal["strong", "possible", "weak", "no_fit"]
    top_angles: list[str]
    likely_objections: list[str]
    red_flags: list[str]
    recommended_next_step: str

