"""
Image Analysis Tool - Gemini Vision for visual understanding

Uses Google's Gemini vision models to analyze images, charts, diagrams,
screenshots, and other visual content. Supports both local files and URLs.
"""

import os
import base64
from typing import Dict, Optional
from urllib.parse import urlparse
import mimetypes

from my_agent.utils.http_client import get_http_client
from my_agent.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Gemini - it should be available from the ADK setup
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except ImportError:
    genai = None
    logger.warning("google.generativeai not available")


def analyze_image(
    path_or_url: str,
    question: str = None,
    detail_level: str = "medium"
):
    """
    Analyze an image using Gemini vision capabilities.

    Args:
        path_or_url: Local file path or URL to image
        question: Specific question about the image (optional)
        detail_level: Analysis depth - "low", "medium", or "high"

    Returns:
        Dictionary containing:
        - description: Overall description of the image
        - details: Detailed analysis based on question or detail_level
        - objects: List of identified objects/elements
        - text: Any text detected in the image (OCR)
        - source: Original path/URL
        - mime_type: Image format

    Example:
        >>> result = analyze_image("chart.png", "What is the trend shown?")
        >>> print(result['description'])
        >>> print(result['details'])
    """
    if genai is None:
        return {
            "error": "Gemini API not configured. Check GOOGLE_API_KEY in .env",
            "description": "",
            "details": "",
            "objects": [],
            "text": "",
            "source": path_or_url
        }

    logger.info(f"Analyzing image from {path_or_url}")

    try:
        # Load image (local or URL)
        image_data, mime_type = _load_image(path_or_url)

        # Build analysis prompt based on detail level
        prompt = _build_vision_prompt(question, detail_level)

        # Call Gemini vision model
        model = genai.GenerativeModel('gemini-1.5-flash')  # Flash for speed

        # Prepare image for Gemini
        image_part = {
            'mime_type': mime_type,
            'data': image_data
        }

        response = model.generate_content([prompt, image_part])

        # Parse response into structured format
        result = _parse_vision_response(response.text, path_or_url, mime_type)

        logger.info(f"Image analysis complete: {len(result['description'])} chars")
        return result

    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        return {
            "error": str(e),
            "description": "",
            "details": "",
            "objects": [],
            "text": "",
            "source": path_or_url
        }


def _load_image(path_or_url: str) -> tuple[bytes, str]:
    """Load image from local path or URL."""
    parsed = urlparse(path_or_url)
    is_url = parsed.scheme in ['http', 'https']

    if is_url:
        # Download from URL
        client = get_http_client()
        response = client.get(path_or_url, timeout=30)
        response.raise_for_status()

        image_data = response.content
        mime_type = response.headers.get('content-type', 'image/jpeg')

    else:
        # Load local file
        if not os.path.exists(path_or_url):
            raise FileNotFoundError(f"Image not found: {path_or_url}")

        with open(path_or_url, 'rb') as f:
            image_data = f.read()

        # Guess MIME type from extension
        mime_type, _ = mimetypes.guess_type(path_or_url)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/jpeg'  # Default fallback

    return image_data, mime_type


def _build_vision_prompt(question: str, detail_level: str) -> str:
    """Build appropriate prompt for vision analysis."""
    if question:
        # Custom question takes precedence
        return f"""Analyze this image and answer the following question:

{question}

Provide a clear, detailed answer based on what you see in the image.
If the image contains text, charts, or diagrams, describe them precisely.
If the question cannot be answered from the image, explain why."""

    # Default comprehensive analysis
    if detail_level == "low":
        return "Describe this image in 2-3 sentences."

    elif detail_level == "high":
        return """Provide a comprehensive analysis of this image:

1. **Overall Description**: What is this image showing?
2. **Key Elements**: What are the main objects, people, or features?
3. **Text Content**: Any visible text, labels, or captions?
4. **Context & Purpose**: What might this image be used for?
5. **Notable Details**: Any interesting or important details?

Be specific and thorough."""

    else:  # medium (default)
        return """Analyze this image and provide:

1. A clear description of what the image shows
2. Key objects, people, or elements present
3. Any visible text or labels
4. The overall context or purpose

Be specific but concise."""


def _parse_vision_response(
    response_text: str,
    source: str,
    mime_type: str
):
    """Parse Gemini vision response into structured format."""
    # For now, return the response as description
    # Future: Could use structured output or additional parsing

    # Simple heuristic: if response has sections, extract them
    lines = response_text.strip().split('\n')

    description = ""
    details = ""
    objects = []
    text_content = ""

    # Try to extract structured info if present
    current_section = "description"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section headers
        lower = line.lower()
        if any(keyword in lower for keyword in ['key element', 'main object', 'objects']):
            current_section = "objects"
            continue
        elif any(keyword in lower for keyword in ['text', 'label', 'caption']):
            current_section = "text"
            continue
        elif any(keyword in lower for keyword in ['detail', 'notable', 'additional']):
            current_section = "details"
            continue

        # Accumulate content
        if current_section == "description" and not description:
            description = line
        elif current_section == "objects" and line.startswith(('-', '•', '*', '1.', '2.')):
            objects.append(line.lstrip('-•*0123456789. '))
        elif current_section == "text":
            text_content += line + " "
        elif current_section == "details":
            details += line + " "

    # Fallback: use full response as description if parsing failed
    if not description:
        description = lines[0] if lines else response_text[:200]

    if not details:
        details = response_text

    return {
        "description": description.strip(),
        "details": details.strip(),
        "objects": objects,
        "text": text_content.strip(),
        "source": source,
        "mime_type": mime_type,
        "full_response": response_text
    }


def analyze_chart(path_or_url: str):
    """
    Specialized function for analyzing charts and graphs.

    Args:
        path_or_url: Path or URL to chart image

    Returns:
        Analysis focused on data visualization elements
    """
    question = """Analyze this chart/graph and provide:

1. **Chart Type**: What type of visualization is this (bar, line, pie, scatter, etc.)?
2. **Axes & Labels**: What are the X and Y axes? What units?
3. **Data Points**: What are the key values or data points?
4. **Trends**: What patterns or trends are shown?
5. **Conclusion**: What is the main takeaway or insight?

Be precise with numbers and units."""

    return analyze_image(path_or_url, question=question, detail_level="high")


def analyze_document(path_or_url: str):
    """
    Specialized function for analyzing document images (receipts, forms, etc.).

    Args:
        path_or_url: Path or URL to document image

    Returns:
        Analysis focused on extracting structured information
    """
    question = """Extract all information from this document:

1. **Document Type**: What kind of document is this?
2. **Text Content**: All visible text, preserving structure
3. **Key Fields**: Important fields (names, dates, amounts, etc.)
4. **Tables/Lists**: Any tabular or list data
5. **Signatures/Stamps**: Any official marks or signatures

Extract text exactly as it appears."""

    return analyze_image(path_or_url, question=question, detail_level="high")
