

import os
from typing import Optional

from google import genai
from google.genai import types

api_key = os.getenv("GOOGLE_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)

def read_files(file_path: str, question: Optional[str] = None) -> str:
    """Reads a file (PNG, PDF, etc.) and returns the content as a string.
    If you are provided a file path to a PNG, PDF, or other file, you MUST invoke this tool to
    read the file and use the content to answer the question.

    Args:
        file_path (str): The path to the file.
        question (str): Optional specific question about the file content.

    Returns:
        str: The content of the file described as text.
    """
    if client is None:
        raise ValueError("GOOGLE_API_KEY not set. Cannot read file.")

    # Check if file exists
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    # Determine MIME type based on file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    mime_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.pdf': 'application/pdf',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }

    mime_type = mime_type_map.get(file_extension)
    if not mime_type:
        return f"Error: Unsupported file type: {file_extension}"

    try:
        # Read file content
        with open(file_path, 'rb') as file:
            file_content = file.read()

        # Create optimized prompt based on whether a specific question is provided
        if question:
            # User has a specific question - provide it directly with clear instructions
            prompt = f"""Answer the following question based on the content in this file.

Question: {question}

Instructions:
- Extract ALL relevant information from the file (text, numbers, formulas, tables, diagrams, etc.)
- Be extremely precise with numbers, fractions, notation, and formatting
- If the question asks for a specific format (e.g., "comma separated", "x.xx", "algebraic notation"), follow it EXACTLY
- Answer directly - provide ONLY what's asked, no extra explanation
- For math/calculations: Show your work briefly, then provide the final answer
- For data extraction: List items exactly as they appear

Answer:"""
        else:
            # General extraction - comprehensive and structured
            prompt = """Extract and describe ALL content from this file in extreme detail:

1. TEXT: All visible text, labels, titles, headings, captions (preserve exact wording and formatting)
2. NUMBERS: All numerical values, fractions, formulas, equations (preserve exact notation)
3. TABLES/LISTS: All tabular data, lists, structured information (preserve structure)
4. VISUAL ELEMENTS: Charts, graphs, diagrams, images (describe layout and key elements)
5. METADATA: Document type, page numbers, dates, authors (if visible)

Be extremely thorough and precise. Extract everything that could be relevant."""

        # Generate content using Gemini with optimized configuration
        response = client.models.generate_content(
            model='gemini-2.5-pro',  # Use flash model for speed
            contents=[
                types.Part.from_bytes(
                    data=file_content,
                    mime_type=mime_type,
                ),
                prompt
            ]
        )

        return response.text

    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"
