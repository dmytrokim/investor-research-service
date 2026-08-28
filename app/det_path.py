from app.models import Dimension

DET_PATHS: dict[Dimension, list[str]] = {
    "thesis": [
        "",
        "/about",
        "/investment-thesis",
        "/approach",
    ],
    "portfolio": [
        "/portfolio",
        "/companies",
        "/investments",
    ],
    "key_person": [
        "/team",
        "/people",
        "/partners",
    ],
    "recent_activity": [
        "/news",
        "/blog",
        "/insights",
    ],
}