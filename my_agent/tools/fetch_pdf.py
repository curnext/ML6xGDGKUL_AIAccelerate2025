"""
PDF Processing Tool - Extract text with page-aware quotes

Extracts text content from PDF files (local or URLs) with page numbers,
enabling precise citations like "According to page 12 of the report..."
"""

import os
import tempfile
from typing import Dict, List, Optional
from urllib.parse import urlparse

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

from my_agent.utils.http_client import get_http_client
from my_agent.utils.logger import get_logger

logger = get_logger(__name__)


def fetch_pdf(
    path_or_url: str,
    max_pages: int = None,
    extract_metadata: bool = True
):
    """
    Extract text content from a PDF file with page numbers.

    Args:
        path_or_url: Local file path or URL to PDF
        max_pages: Maximum number of pages to extract (None = all pages)
        extract_metadata: Whether to extract PDF metadata (author, title, etc.)

    Returns:
        Dictionary containing:
        - pages: List of {page_num, text} dictionaries
        - metadata: PDF metadata (title, author, creation_date, etc.)
        - total_pages: Total number of pages in document
        - source: Original path/URL

    Example:
        >>> result = fetch_pdf("https://example.com/report.pdf", max_pages=10)
        >>> print(f"Found {result['total_pages']} pages")
        >>> print(result['pages'][0]['text'][:100])  # First 100 chars of page 1
    """
    if PyPDF2 is None:
        return {
            "error": "PyPDF2 not installed. Run: uv add PyPDF2",
            "pages": [],
            "metadata": {},
            "total_pages": 0,
            "source": path_or_url
        }

    logger.info(f"Fetching PDF from {path_or_url}")

    try:
        # Determine if URL or local path
        parsed = urlparse(path_or_url)
        is_url = parsed.scheme in ['http', 'https']

        if is_url:
            # Download PDF to temporary file
            pdf_file = _download_pdf(path_or_url)
            cleanup_temp = True
        else:
            # Use local file
            if not os.path.exists(path_or_url):
                return {
                    "error": f"File not found: {path_or_url}",
                    "pages": [],
                    "metadata": {},
                    "total_pages": 0,
                    "source": path_or_url
                }
            pdf_file = path_or_url
            cleanup_temp = False

        # Extract text with page numbers
        result = _extract_pdf_content(
            pdf_file,
            max_pages=max_pages,
            extract_metadata=extract_metadata
        )
        result["source"] = path_or_url

        # Cleanup temporary file if downloaded
        if cleanup_temp:
            try:
                os.unlink(pdf_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp PDF: {e}")

        logger.info(
            f"Extracted {len(result['pages'])} pages from PDF "
            f"({result['total_pages']} total)"
        )
        return result

    except Exception as e:
        logger.error(f"PDF extraction failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "pages": [],
            "metadata": {},
            "total_pages": 0,
            "source": path_or_url
        }


def _download_pdf(url: str) -> str:
    """Download PDF from URL to temporary file."""
    client = get_http_client()

    try:
        response = client.get(url, timeout=30)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'application/pdf' not in content_type and not url.endswith('.pdf'):
            logger.warning(f"URL may not be PDF: {content_type}")

        # Write to temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        try:
            os.write(temp_fd, response.content)
        finally:
            os.close(temp_fd)

        return temp_path

    except Exception as e:
        logger.error(f"PDF download failed: {e}")
        raise


def _extract_pdf_content(
    pdf_path: str,
    max_pages: int = None,
    extract_metadata: bool = True
):
    """Extract text and metadata from PDF file."""
    pages = []
    metadata = {}

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)

        # Extract metadata
        if extract_metadata and reader.metadata:
            metadata = {
                'title': reader.metadata.get('/Title', ''),
                'author': reader.metadata.get('/Author', ''),
                'subject': reader.metadata.get('/Subject', ''),
                'creator': reader.metadata.get('/Creator', ''),
                'producer': reader.metadata.get('/Producer', ''),
                'creation_date': reader.metadata.get('/CreationDate', ''),
                'modification_date': reader.metadata.get('/ModDate', '')
            }
            # Clean up metadata (remove empty values)
            metadata = {k: v for k, v in metadata.items() if v}

        # Extract text from pages
        num_pages = min(max_pages, total_pages) if max_pages else total_pages

        for page_num in range(num_pages):
            try:
                page = reader.pages[page_num]
                text = page.extract_text()

                # Clean up text (remove excessive whitespace)
                text = ' '.join(text.split())

                pages.append({
                    'page_num': page_num + 1,  # 1-indexed for user display
                    'text': text,
                    'char_count': len(text)
                })

            except Exception as e:
                logger.warning(f"Failed to extract page {page_num + 1}: {e}")
                pages.append({
                    'page_num': page_num + 1,
                    'text': '',
                    'char_count': 0,
                    'error': str(e)
                })

    return {
        'pages': pages,
        'metadata': metadata,
        'total_pages': total_pages,
        'extracted_pages': len(pages)
    }


def extract_quote_from_pdf(
    pdf_result: dict,
    search_text: str,
    max_quote_length: int = 120
):
    """
    Find and extract a quote from PDF results.

    Args:
        pdf_result: Result from fetch_pdf() - dictionary with 'pages' list
        search_text: Text to search for
        max_quote_length: Maximum length of extracted quote

    Returns:
        Dictionary with quote, page_num, and surrounding context, or None if not found
    """
    search_lower = search_text.lower()

    for page in pdf_result.get('pages', []):
        text = page.get('text', '')
        text_lower = text.lower()

        # Find the search text
        idx = text_lower.find(search_lower)
        if idx != -1:
            # Extract quote with context
            start = max(0, idx - 20)  # 20 chars before
            end = min(len(text), idx + len(search_text) + 100)  # More after

            quote = text[start:end].strip()

            # Truncate if needed
            if len(quote) > max_quote_length:
                quote = quote[:max_quote_length - 3] + "..."

            return {
                'quote': quote,
                'page_num': page['page_num'],
                'page_text': text,
                'source': pdf_result.get('source', 'Unknown'),
                'metadata': pdf_result.get('metadata', {})
            }

    return None
