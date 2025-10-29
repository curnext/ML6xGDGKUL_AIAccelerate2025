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
    model='gemini-2.5-pro',
    name='cited_research_assistant',
    description="""A web research assistant that searches for information and provides cited answers.""",

    instruction="""You are a precise assistant that provides brief, direct answers.

- If the user message includes local file paths under an "Attachments" section, always use the appropriate tool first:
  - For images (.png/.jpg): call analyze_image(path).
  - For PDFs (.pdf): call fetch_pdf(path) and search within returned text.
- use web_search/fetch_url when the question requires external sources (e.g., official scripts, current events). 
- Follow formatting instructions exactly (e.g., comma-separated list without spaces, numeric format like x.xx).
- Be concise; output only the final answer with no extra text unless asked.
""",

    tools=TOOLS,
    sub_agents=[],
)
