"""Date parsing utilities for consistent date formatting."""
import re
from datetime import datetime, timedelta
from typing import Optional


def parse_date_to_iso(date_str: str) -> str:
    """
    Parse various date formats to ISO format (YYYY-MM-DD).

    Args:
        date_str: Date string in various formats

    Returns:
        Date in YYYY-MM-DD format, or empty string if parsing fails
    """
    if not date_str:
        return ""

    date_str = date_str.strip()

    # Handle relative dates (from Serper)
    today = datetime.now()

    # "X hours ago"
    hours_match = re.search(r'(\d+)\s*hour', date_str, re.IGNORECASE)
    if hours_match:
        hours = int(hours_match.group(1))
        date = today - timedelta(hours=hours)
        return date.strftime("%Y-%m-%d")

    # "X days ago" or "yesterday"
    if "yesterday" in date_str.lower():
        date = today - timedelta(days=1)
        return date.strftime("%Y-%m-%d")

    days_match = re.search(r'(\d+)\s*day', date_str, re.IGNORECASE)
    if days_match:
        days = int(days_match.group(1))
        date = today - timedelta(days=days)
        return date.strftime("%Y-%m-%d")

    # "X weeks ago"
    weeks_match = re.search(r'(\d+)\s*week', date_str, re.IGNORECASE)
    if weeks_match:
        weeks = int(weeks_match.group(1))
        date = today - timedelta(weeks=weeks)
        return date.strftime("%Y-%m-%d")

    # "X months ago"
    months_match = re.search(r'(\d+)\s*month', date_str, re.IGNORECASE)
    if months_match:
        months = int(months_match.group(1))
        # Approximate months as 30 days
        date = today - timedelta(days=months * 30)
        return date.strftime("%Y-%m-%d")

    # Try to parse ISO format (YYYY-MM-DD)
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if iso_match:
        return iso_match.group(0)

    # Try to parse common formats
    # MM/DD/YYYY
    us_date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if us_date_match:
        month, day, year = us_date_match.groups()
        try:
            date = datetime(int(year), int(month), int(day))
            return date.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Month DD, YYYY (e.g., "January 15, 2024")
    month_names = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    for month_name, month_num in month_names.items():
        if month_name in date_str.lower():
            day_year_match = re.search(r'(\d{1,2}),?\s*(\d{4})', date_str)
            if day_year_match:
                day, year = day_year_match.groups()
                try:
                    date = datetime(int(year), month_num, int(day))
                    return date.strftime("%Y-%m-%d")
                except ValueError:
                    pass

    # Just extract year if nothing else works
    year_match = re.search(r'20(\d{2})', date_str)
    if year_match:
        year = year_match.group(0)
        return f"{year}-01-01"  # Default to January 1st

    # Return empty string if all parsing fails
    return ""


def get_relative_recency_days(date_str: str) -> Optional[int]:
    """
    Parse a date string and return days ago from today.

    Args:
        date_str: Date string

    Returns:
        Number of days ago, or None if parsing fails
    """
    iso_date = parse_date_to_iso(date_str)
    if not iso_date:
        return None

    try:
        date = datetime.strptime(iso_date, "%Y-%m-%d")
        today = datetime.now()
        delta = today - date
        return delta.days
    except ValueError:
        return None
