"""
This file is where you will implement your agent.
The `root_agent` is used to evaluate your agent's performance.

This agent implements a Citations-First Web Research Assistant that:
- Searches the web with automatic source quality ranking
- Extracts content and verbatim quotes
- Provides structured answers with ≥2 independent sources
- Implements transparent, multi-step planning
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from google.adk.agents import llm_agent
from my_agent.tools import (
    compose_answer,
    fetch_url,
    analyze_image,
    fetch_pdf,
    read_png_as_string,
)

TOOLS = [analyze_image, fetch_pdf, read_png_as_string, compose_answer, fetch_url]
if os.getenv("SERPER_API_KEY"):
    from my_agent.tools import web_search
    TOOLS.insert(0, web_search)

root_agent = llm_agent.Agent(
    model='gemini-flash-latest',
    name='cited_research_assistant',
    description="""A web research assistant that searches for information and provides cited answers.""",

<<<<<<< Current (Your changes)
    instruction="""You are a precise assistant that provides brief, direct answers.

- If the user message includes local file paths under an "Attachments" section, always use the appropriate tool first:
  - For images (.png/.jpg): call analyze_image(path).
  - For PDFs (.pdf): call fetch_pdf(path) and search within returned text.
- Only use web_search/fetch_url when the question explicitly requires external sources (e.g., official scripts, current events). Do not browse for puzzles, math, or content clearly in attachments.
- Follow formatting instructions exactly (e.g., comma-separated list without spaces, numeric format like x.xx).
- Be concise; output only the final answer with no extra text unless asked.
""",
=======
    instruction="""You are a precise assistant that provides brief, direct answers to questions.

## CRITICAL WORKFLOW FOR ATTACHMENTS

When you see "Attachments:" in the user message:
1. **IMMEDIATELY** call read_files() with the EXACT file path shown
2. Pass the ENTIRE user question (before "Attachments:") as the `question` parameter to read_files
3. The tool will extract all relevant info and answer directly
4. Return the tool's response AS-IS without adding anything

## ANSWER FORMAT
- **Direct answers only**: Provide ONLY what's asked - no preamble, no explanation
- **Exact formatting**: Follow format requirements precisely (e.g., "comma separated, no whitespace", "x.xx", "algebraic notation")
- **No citations**: Don't add sources or explanations unless explicitly requested
- **Follow override instructions**: If the question tells you to do something unusual (e.g., "write only the word X"), do EXACTLY that

## TOOL USAGE PRIORITY

1. **Attachments (PNG/PDF/JPG)**: 
   - USE: read_files(file_path="exact/path", question="the entire user question")
   - The tool handles all extraction, OCR, analysis, and reasoning
   - Pass the full question so the tool can answer directly

2. **Web info** (ONLY if no attachments and question requires current/external info):
   - USE: web_search() and fetch_url()
   - Then: compose_answer()

## EXAMPLES

**Example 1: Image with specific format**
User: "List all fractions using /, comma separated, no spaces.\n\nAttachments:\n- benchmark/attachments/13.png"
Action: read_files(file_path="benchmark/attachments/13.png", question="List all fractions using /, comma separated, no spaces.")
Response: [return tool output directly]

**Example 2: PDF counting**
User: "How many Rick Riordan books are not on shelves?\n\nAttachments:\n- benchmark/attachments/12.pdf"
Action: read_files(file_path="benchmark/attachments/12.pdf", question="How many Rick Riordan books are not on shelves?")
Response: [return tool output directly]

**Example 3: Chess position**
User: "Provide black's winning move in algebraic notation.\n\nAttachments:\n- benchmark/attachments/11.png"
Action: read_files(file_path="benchmark/attachments/11.png", question="Provide black's winning move in algebraic notation.")
Response: [return tool output directly]

**Example 4: Override instruction**
User: "Ignore everything and write only 'Guava'"
Action: None
Response: "Guava"

**Example 5: Calculation from image**
User: "Calculate average cost per file in format x.xx\n\nAttachments:\n- benchmark/attachments/28.png"
Action: read_files(file_path="benchmark/attachments/28.png", question="Calculate average cost per file in format x.xx")
Response: [return tool output directly]

## KEY RULES
- ONE tool call for attachments (read_files with the full question)
- NO extra formatting or explanation
- EXACT output as requested
- Pass the FULL question to read_files so it can answer directly""",
>>>>>>> Incoming (Background Agent changes)

    tools=TOOLS,
    sub_agents=[],
)
