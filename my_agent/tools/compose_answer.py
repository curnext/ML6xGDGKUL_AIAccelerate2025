"""Answer composition tool for structured JSON output."""
import json
from typing import List, Dict, Any, Optional


def compose_answer(
    summary: str,
    bullets: List[str],
    quotes: List[Dict[str, str]],
    sources: List[Dict[str, str]],
    queries: List[str],
    hops: int,
    notes: str,
    confidence: str
) -> dict:
    """
    Composes a structured answer with citations following the PRD output contract.

    This tool creates the final structured response with summary, bullet points,
    verbatim quotes with sources, source list, and search methodology transparency.

    Args:
        summary: Brief summary of the answer (1-2 sentences)
        bullets: List of key points as bullet strings
        quotes: List of quote dictionaries, each containing:
            - text: Verbatim quote (≤120 chars)
            - source: Source title
            - url: Source URL
            - date: Publication date (YYYY-MM-DD)
            - page_or_ts: Page number (p.12) or timestamp (01:23), optional
        sources: List of source dictionaries, each containing:
            - title: Source title
            - domain: Source domain
            - url: Source URL
            - date: Publication date (YYYY-MM-DD)
        queries: List of search queries executed
        hops: Number of search hops/iterations performed
        notes: Notes about the search methodology (e.g., "Used recency filter", "Prioritized government sources")
        confidence: Confidence level - must be one of: "low", "medium", "high"

    Returns:
        dict: Structured answer matching PRD contract with all fields

    Example:
        >>> compose_answer(
        ...     summary="The EU AI Act came into effect in January 2024.",
        ...     bullets=["Applies to high-risk AI systems", "Includes fines up to 7% of revenue"],
        ...     quotes=[{
        ...         "text": "The regulation establishes harmonized rules for AI",
        ...         "source": "EU AI Act Official Text",
        ...         "url": "https://ec.europa.eu/...",
        ...         "date": "2024-01-15",
        ...         "page_or_ts": "p.3"
        ...     }],
        ...     sources=[{
        ...         "title": "EU AI Act Official Text",
        ...         "domain": "ec.europa.eu",
        ...         "url": "https://ec.europa.eu/...",
        ...         "date": "2024-01-15"
        ...     }],
        ...     queries=["EU AI Act 2024", "AI regulations Europe"],
        ...     hops=2,
        ...     notes="Prioritized official EU sources",
        ...     confidence="high"
        ... )
    """
    # Validate confidence level
    valid_confidence = ["low", "medium", "high"]
    if confidence not in valid_confidence:
        confidence = "medium"  # Default to medium if invalid

    # Ensure quotes have all required fields with defaults
    formatted_quotes = []
    for quote in quotes:
        formatted_quote = {
            "text": quote.get("text", "")[:120],  # Truncate to 120 chars
            "source": quote.get("source", ""),
            "url": quote.get("url", ""),
            "date": quote.get("date", ""),
            "page_or_ts": quote.get("page_or_ts", "")
        }
        formatted_quotes.append(formatted_quote)

    # Ensure sources have all required fields
    formatted_sources = []
    for source in sources:
        formatted_source = {
            "title": source.get("title", ""),
            "domain": source.get("domain", ""),
            "url": source.get("url", ""),
            "date": source.get("date", "")
        }
        formatted_sources.append(formatted_source)

    # Build final answer structure
    answer = {
        "summary": summary,
        "bullets": bullets,
        "quotes": formatted_quotes,
        "sources": formatted_sources,
        "method": {
            "queries": queries,
            "hops": hops,
            "notes": notes
        },
        "confidence": confidence
    }

    return answer


def format_answer_as_markdown(answer: dict) -> str:
    """
    Format a composed answer as readable markdown (for debugging/display).

    Args:
        answer: Answer dict from compose_answer()

    Returns:
        Formatted markdown string
    """
    md_parts = []

    # Summary
    md_parts.append(f"## Summary\n\n{answer['summary']}\n")

    # Bullets
    if answer.get("bullets"):
        md_parts.append("## Key Points\n")
        for bullet in answer["bullets"]:
            md_parts.append(f"- {bullet}")
        md_parts.append("")

    # Quotes
    if answer.get("quotes"):
        md_parts.append("## Supporting Quotes\n")
        for i, quote in enumerate(answer["quotes"], 1):
            md_parts.append(f"{i}. \"{quote['text']}\"")
            md_parts.append(f"   - Source: {quote['source']}")
            md_parts.append(f"   - Date: {quote['date']}")
            md_parts.append(f"   - URL: {quote['url']}")
            if quote.get("page_or_ts"):
                md_parts.append(f"   - Location: {quote['page_or_ts']}")
            md_parts.append("")

    # Sources
    if answer.get("sources"):
        md_parts.append("## Sources\n")
        for i, source in enumerate(answer["sources"], 1):
            md_parts.append(f"{i}. **{source['title']}** ({source['domain']})")
            md_parts.append(f"   - Date: {source['date']}")
            md_parts.append(f"   - URL: {source['url']}")
            md_parts.append("")

    # Method
    method = answer.get("method", {})
    md_parts.append("## How I Searched\n")
    md_parts.append(f"- **Queries**: {', '.join(method.get('queries', []))}")
    md_parts.append(f"- **Search Hops**: {method.get('hops', 0)}")
    md_parts.append(f"- **Notes**: {method.get('notes', 'N/A')}")
    md_parts.append(f"- **Confidence**: {answer.get('confidence', 'medium').upper()}")

    return "\n".join(md_parts)
