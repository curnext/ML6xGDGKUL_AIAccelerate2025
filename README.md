# GDG Hackathon - ML6 Agent Challenge

AI agent built with Google's Agent Development Kit (ADK) to answer complex multi-modal questions requiring web research, document analysis, and multi-step reasoning.

## Quick Setup

### 1. Install uv Package Manager

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Configure Environment

```bash
# Copy environment template
copy my_agent\.local_env .env          # Windows
cp my_agent/.local_env .env            # macOS/Linux

# Edit .env and add your API keys:
# GOOGLE_API_KEY="your_google_api_key"
# SERPER_API_KEY="your_serper_api_key"  # Optional for web search
```

Get keys:
- [Google API Key](https://aistudio.google.com/api-keys) (required)
- [Serper API Key](https://serper.dev) (optional, 2,500 free searches/month)

### 3. Install Dependencies

```bash
uv sync
```

### 4. Run Evaluation

```bash
# Evaluate all questions
uv run python evaluate.py

# Test specific question
uv run python evaluate.py --question 0

# Use different training set
uv run python evaluate.py --benchmark benchmark/train_1.json
```

**Interactive development:**
```bash
uv run adk web  # Opens web UI at http://127.0.0.1:8000
```

## Technology Stack

### Core Framework
- **Agent Framework:** Google ADK (Agent Development Kit)
- **LLM:** Gemini 2.5 Pro
- **Package Manager:** uv (fast Python package manager)

### Tools & APIs
- **Web Search:** Serper.dev API (Google Search wrapper)
- **Content Extraction:** Trafilatura (web page text extraction)
- **PDF Processing:** PyPDF2
- **HTTP Client:** Custom client with retries and rate limiting

### Dependencies
```toml
google-adk        # Agent framework
colorama          # Terminal colors
pyfiglet          # ASCII banners
pypdf2            # PDF parsing
trafilatura       # Web scraping
```

## Agent Design & Workflow

### Architecture

```
┌─────────────────────────────────────────────────┐
│           User Question + Attachments           │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│         Gemini 2.5 Pro Agent (ADK)              │
│  • Analyzes question and attachments            │
│  • Plans multi-step reasoning strategy          │
│  • Selects and invokes appropriate tools        │
└─────────────────┬───────────────────────────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Local   │  │  Web    │  │Document │
│ Files   │  │Research │  │Analysis │
└─────────┘  └─────────┘  └─────────┘
     │            │            │
     ▼            ▼            ▼
┌─────────────────────────────────────────────────┐
│              Structured Answer                  │
│     (with citations and sources)                │
└─────────────────────────────────────────────────┘
```

### Agent Workflow

**1. Question Analysis**
   - Checks for local attachments (PDFs, images)
   - Determines if web research is needed
   - Plans tool execution strategy

**2. Tool Selection & Execution**

| Tool | Purpose | When Used |
|------|---------|-----------|
| `analyze_image` | Image understanding via Gemini Vision | Charts, graphs, photos, documents |
| `fetch_pdf` | Extract text from PDFs | Document analysis |
| `read_png_as_string` | Read text from images | Simple text extraction |
| `web_search` | Search web via Serper | Current events, external facts |
| `fetch_url` | Extract webpage content | Deep-dive into sources |
| `compose_answer` | Format structured JSON response | Final answer with citations |

**3. Multi-Step Reasoning**
   - **Attachment-first strategy:** Always prioritize local files
   - **Web fallback:** Use web search only when needed
   - **Iterative refinement:** Multiple tool calls if needed
   - **Citation tracking:** Record sources for answers

**4. Response Formatting**
   - Brief, direct answers
   - Follow format instructions exactly (e.g., comma-separated, numeric)
   - Include citations when using web sources

### Project Structure

```
my_agent/
├── agent.py              # Agent configuration (model, tools, instructions)
├── tools/                # Agent tools
│   ├── web_search.py     # Serper API integration
│   ├── fetch_url.py      # URL content extraction
│   ├── fetch_pdf.py      # PDF text extraction
│   ├── analyze_image.py  # Gemini Vision for images
│   ├── read_files.py     # Text file reading
│   └── compose_answer.py # Structured JSON output
└── utils/
    ├── http_client.py    # HTTP client with retries
    └── logger.py         # Logging utilities

benchmark/
├── train.json            # Training dataset (5 questions)
├── train_1.json to       # Additional training sets (10 more)
│   train_10.json
└── attachments/          # PDFs and images

evaluate.py               # Evaluation script
utils/server.py           # ADK server management
pyproject.toml            # Project dependencies
```

## Key Configuration

**Agent Configuration** ([my_agent/agent.py](my_agent/agent.py)):

```python
root_agent = llm_agent.Agent(
    model='gemini-2.5-pro',
    name='cited_research_assistant',

    instruction="""
    - If attachments exist, use appropriate tools first
      (analyze_image for images, fetch_pdf for PDFs)
    - Only use web_search when external sources needed
    - Follow format instructions exactly
    - Be concise, output only final answer
    """,

    tools=[web_search, analyze_image, fetch_pdf,
           read_png_as_string, compose_answer, fetch_url]
)
```

## Commands Reference

```bash
# Development
uv run adk web                               # Interactive web UI
uv run python -c "import my_agent.agent"     # Verify agent loads

# Evaluation
uv run python evaluate.py                    # Full evaluation
uv run python evaluate.py --question N       # Test question N
uv run python evaluate.py --benchmark FILE   # Use specific dataset

# Environment Check
uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GOOGLE_API_KEY:', 'OK' if os.getenv('GOOGLE_API_KEY') else 'MISSING')"
```

## Troubleshooting

**Agent not responding:**
- Verify `.env` file exists in root directory
- Check [my_agent/agent.py:16](my_agent/agent.py#L16) has `load_dotenv()`

**Type hint errors:**
- Use simple types: `str`, `int`, `dict`, `list`
- Avoid: `Dict`, `Optional`, `Union` from `typing`

**Module not found:**
```bash
uv sync  # Reinstall dependencies
```

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/) - Complete framework guide
- [ADK Samples](https://github.com/google/adk-samples) - Example implementations
- [Gemini API Docs](https://ai.google.dev/docs) - Model reference
- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) - Design patterns

## About

**Challenge:** Build an AI agent that answers complex questions requiring multi-step reasoning, document analysis, and web research.

**Evaluation Criteria:**
- 40% Answer Accuracy (hidden test set)
- 10% Response Speed
- 20% Technical Demo & Insights
- 30% Business Application & ROI

Built for GDG x ML6 AI Accelerate Hackathon 2025.
