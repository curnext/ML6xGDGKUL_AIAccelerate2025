"""Source quality assessment and ranking logic."""
from enum import IntEnum
from typing import Dict, List, Any
from urllib.parse import urlparse
import re


class SourceQualityTier(IntEnum):
    """Source quality tiers from PRD."""
    TIER_1_PRIMARY = 1      # Gov, standards bodies, company IR
    TIER_2_TOP_JOURNALISM = 2  # Reuters, FT, WSJ, NYT, Bloomberg
    TIER_3_OTHER = 3        # Other outlets, blogs
    TIER_4_UNDATED = 4      # Penalized undated sources


# Domain patterns for quality tiers
TIER_1_DOMAINS = {
    # Government
    "gov", "mil", "europa.eu", "parliament.uk", "gov.uk",
    "bundesregierung.de", "gouvernement.fr",
    # Standards bodies
    "sec.gov", "fda.gov", "epa.gov", "cdc.gov", "nih.gov",
    "who.int", "un.org", "oecd.org", "imf.org", "worldbank.org",
    # Academic/Research
    "edu", "ac.uk", "arxiv.org", "nature.com", "science.org",
    # Company IR (investor relations)
    "ir.", "investors.", "investor."
}

TIER_2_DOMAINS = {
    "reuters.com", "ft.com", "wsj.com", "nytimes.com", "bloomberg.com",
    "economist.com", "bbc.com", "bbc.co.uk", "apnews.com", "afp.com",
    "theguardian.com", "washingtonpost.com", "time.com", "forbes.com"
}


def get_source_quality_tier(url: str, has_date: bool = True) -> SourceQualityTier:
    """
    Determine the quality tier of a source based on URL and date presence.

    Args:
        url: The source URL
        has_date: Whether the source has a publication date

    Returns:
        SourceQualityTier enum value
    """
    # Penalize undated sources
    if not has_date:
        return SourceQualityTier.TIER_4_UNDATED

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)

        # Check Tier 1 (government, standards, academic, IR)
        for pattern in TIER_1_DOMAINS:
            if domain.endswith(pattern) or pattern in domain:
                return SourceQualityTier.TIER_1_PRIMARY

        # Check Tier 2 (top journalism)
        for pattern in TIER_2_DOMAINS:
            if pattern in domain:
                return SourceQualityTier.TIER_2_TOP_JOURNALISM

        # Default to Tier 3 (other)
        return SourceQualityTier.TIER_3_OTHER

    except Exception:
        return SourceQualityTier.TIER_3_OTHER


def rank_search_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank search results by source quality and recency.

    Args:
        results: List of search result dicts with 'link', 'date' (optional), etc.

    Returns:
        Sorted list of results (highest quality first)
    """
    def quality_score(result: Dict[str, Any]) -> tuple:
        """
        Calculate quality score for ranking.
        Returns tuple (tier, recency_score) for sorting.
        Lower tier number = better quality.
        Higher recency_score = more recent.
        """
        url = result.get("link", "")
        date_str = result.get("date", "")
        has_date = bool(date_str)

        tier = get_source_quality_tier(url, has_date)

        # Recency score (prioritize recent content)
        # Date format from Serper typically: "YYYY-MM-DD" or relative like "2 days ago"
        recency_score = 0
        if date_str:
            # Simple heuristic: if date string contains recent indicators
            if "hour" in date_str.lower() or "today" in date_str.lower():
                recency_score = 1000
            elif "day" in date_str.lower() or "yesterday" in date_str.lower():
                recency_score = 100
            elif "week" in date_str.lower():
                recency_score = 10
            else:
                # Try to parse year for older content
                year_match = re.search(r'20(\d{2})', date_str)
                if year_match:
                    year = int(year_match.group(1))
                    recency_score = year  # 2024 = 24, 2023 = 23, etc.

        # Return tuple for sorting: (tier, -recency_score)
        # Negative recency so higher recency comes first within same tier
        return (tier.value, -recency_score)

    # Sort by quality tier first, then by recency
    sorted_results = sorted(results, key=quality_score)
    return sorted_results


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL for display."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        domain = re.sub(r'^www\.', '', domain)
        return domain
    except Exception:
        return url
