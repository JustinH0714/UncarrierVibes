import re
from typing import Dict, Optional, Tuple

# Minimal city dictionary for keyword-based extraction
# Extend as needed
_CITY_DB: Dict[str, Tuple[float, float, str]] = {
    # city_lower: (lat, lon, state_abbrev)
    "seattle": (47.6062, -122.3321, "WA"),
    "chicago": (41.8781, -87.6298, "IL"),
    "new york": (40.7128, -74.0060, "NY"),
    "los angeles": (34.0522, -118.2437, "CA"),
    "miami": (25.7617, -80.1918, "FL"),
    "austin": (30.2672, -97.7431, "TX"),
    "san francisco": (37.7749, -122.4194, "CA"),
    "boston": (42.3601, -71.0589, "MA"),
    "dallas": (32.7767, -96.7970, "TX"),
    "houston": (29.7604, -95.3698, "TX"),
    "atlanta": (33.7490, -84.3880, "GA"),
    "denver": (39.7392, -104.9903, "CO"),
    "phoenix": (33.4484, -112.0740, "AZ"),
    "portland": (45.5152, -122.6784, "OR"),
    "las vegas": (36.1699, -115.1398, "NV"),
    "san diego": (32.7157, -117.1611, "CA"),
    "minneapolis": (44.9778, -93.2650, "MN"),
    "charlotte": (35.2271, -80.8431, "NC"),
    "nashville": (36.1627, -86.7816, "TN"),
}

# Precompile regex patterns for word-boundary matches
_PATTERNS: Dict[str, re.Pattern] = {
    # Allow city names adjacent to punctuation or within longer phrases (avoid full strict word boundary issues)
    key: re.compile(r"(?<![A-Za-z0-9])" + re.escape(key) + r"(?![A-Za-z0-9])", flags=re.IGNORECASE)
    for key in _CITY_DB.keys()
}


def extract_location(text: str) -> Optional[Tuple[str, float, float]]:
    """
    Return ("City, ST", lat, lon) if a known city keyword is found in text; else None.

    This is a lightweight heuristic for hackathon use. For broader coverage, replace with
    a proper NER model (spaCy) and a geocoder.
    """
    lowered = text.lower() if text else ""
    for key, pattern in _PATTERNS.items():
        if pattern.search(lowered):
            lat, lon, st = _CITY_DB[key]
            # Title-case city for display
            city_title = " ".join([w.capitalize() for w in key.split()])
            return f"{city_title}, {st}", lat, lon
    return None
