"""Quote extraction utilities for citations."""
import re
from typing import List, Dict, Any


def extract_quotes_from_text(
    text: str,
    max_quote_length: int = 120,
    min_quote_length: int = 20,
    max_quotes: int = 5
) -> List[str]:
    """
    Extract relevant verbatim quotes from text.

    Args:
        text: The source text to extract quotes from
        max_quote_length: Maximum quote length in characters
        min_quote_length: Minimum quote length in characters
        max_quotes: Maximum number of quotes to extract

    Returns:
        List of extracted quote strings
    """
    if not text:
        return []

    quotes = []

    # Strategy 1: Extract sentences (simple period-based splitting)
    sentences = re.split(r'[.!?]+', text)

    for sentence in sentences:
        sentence = sentence.strip()

        # Skip if too short or too long
        if len(sentence) < min_quote_length or len(sentence) > max_quote_length:
            continue

        # Skip if contains too many special characters (likely not prose)
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', sentence)) / max(len(sentence), 1)
        if special_char_ratio > 0.3:
            continue

        # Skip if too many numbers (likely tables/data)
        number_ratio = len(re.findall(r'\d', sentence)) / max(len(sentence), 1)
        if number_ratio > 0.4:
            continue

        quotes.append(sentence)

        if len(quotes) >= max_quotes:
            break

    return quotes[:max_quotes]


def create_quote_dict(
    quote_text: str,
    source_title: str,
    source_url: str,
    source_date: str,
    page_or_timestamp: str = ""
) -> Dict[str, Any]:
    """
    Create a quote dictionary matching the PRD output contract.

    Args:
        quote_text: The verbatim quote text (≤120 chars)
        source_title: Title of the source document
        source_url: URL of the source
        source_date: Publication date (YYYY-MM-DD format)
        page_or_timestamp: Optional page number (p.12) or timestamp (01:23)

    Returns:
        Quote dictionary
    """
    # Truncate quote if too long
    if len(quote_text) > 120:
        quote_text = quote_text[:117] + "..."

    return {
        "text": quote_text,
        "source": source_title,
        "url": source_url,
        "date": source_date,
        "page_or_ts": page_or_timestamp
    }


def extract_quotes_with_context(
    text: str,
    query: str,
    max_quotes: int = 3
) -> List[str]:
    """
    Extract quotes that are contextually relevant to the query.

    Args:
        text: The source text
        query: The original search query (for relevance)
        max_quotes: Maximum number of quotes to extract

    Returns:
        List of relevant quote strings
    """
    if not text or not query:
        return []

    # Extract all potential quotes
    all_quotes = extract_quotes_from_text(text, max_quotes=max_quotes * 2)

    # Score quotes by query term overlap (simple relevance)
    query_terms = set(re.findall(r'\b\w+\b', query.lower()))

    def relevance_score(quote: str) -> int:
        quote_terms = set(re.findall(r'\b\w+\b', quote.lower()))
        return len(query_terms & quote_terms)

    # Sort by relevance and take top N
    scored_quotes = [(quote, relevance_score(quote)) for quote in all_quotes]
    scored_quotes.sort(key=lambda x: x[1], reverse=True)

    return [quote for quote, score in scored_quotes[:max_quotes]]
