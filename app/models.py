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
    final_url: HttpUrl        # канонічний URL після редиректів — ЄДИНЕ джерело провенансу
    title: str | None
    markdown: str
    fetched_at: str           # UTC ISO-8601 від Groundhog
    truncated: bool
    dimension: str            # цільовий напрям, присвоєний на discovery

class Fact(BaseModel):
    field: str
    value: str
    source_url: HttpUrl       # МАЄ дорівнювати final_url сторінки, з якої взято
    confidence: Literal["high", "medium", "low"]

class DimensionResult(BaseModel):
    dimension: str            # "thesis" | "portfolio" | "recent_activity" | "key_person"
    found: bool
    facts: list[Fact]
    notes: str = ""

class InvestorProfile(BaseModel):
    investor_name: str
    domain: str | None
    dimensions: list[DimensionResult]
    fetched_pages: list[GroundedPage]                 # для провенансу і пост-фільтра
    data_completeness: Literal["rich", "partial", "sparse"]

class Strategy(BaseModel):
    thesis_fit: str
    fit_score: Literal["strong", "possible", "weak", "no_fit"]
    top_angles: list[str]           # максимум 3
    likely_objections: list[str]
    red_flags: list[str]
    recommended_next_step: str

