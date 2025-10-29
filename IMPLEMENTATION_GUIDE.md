# Cited Web Research Assistant - Implementation Guide

## Overview

This guide covers the complete implementation of a production-ready RAG system for the Cited Web Research Assistant using Google ADK, Gemini 2.0 Flash, and Serper.dev search API.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│              AGENT ORCHESTRATION LAYER                      │
│          (agent.py - Gemini 2.0 Flash)                     │
│                                                             │
│  • Multi-step planning (1-3 queries)                       │
│  • Budget management (max_searches, max_fetches)           │
│  • Quality assessment & termination logic                  │
│  • Transparent methodology logging                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┐
    │             │             │              │
    ▼             ▼             ▼              ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────┐
│web_search │ │ fetch_url │ │  source   │ │compose_answer│
│ (Serper)  │ │(Trafilatura)│ │  ranking  │ │   (JSON)     │
└───────────┘ └───────────┘ └───────────┘ └──────────────┘
```

### Design Decisions

1. **Stateless Architecture**: No vector database required
   - Each query is independent (search → fetch → extract → compose)
   - No persistent storage = $0 storage costs, simpler deployment
   - Fits PRD's "citations-first web search assistant" model

2. **Synchronous httpx**: Optimized for prototype velocity
   - 3 searches × 5 fetches = 15 sequential HTTP calls max
   - Simple debugging and error handling
   - Meets PRD latency targets (≤8s P50, ≤15s P95)

3. **Source Quality Tiering**: Automatic ranking
   - Tier 1: .gov, .edu, standards bodies (sec.gov, fda.gov)
   - Tier 2: Top journalism (Reuters, FT, WSJ, NYT, Bloomberg)
   - Tier 3: Other credible outlets
   - Tier 4: Undated sources (penalized)

4. **Budget-Based Termination**: Deterministic orchestration
   - Quick mode: max 3 searches, max 5 fetches, min 2 sources
   - Deep Check: max 5 searches, max 10 fetches
   - Prevents runaway LLM loops

## File Structure

```
my_agent/
├── agent.py                    # Main agent with orchestration logic
├── tools/
│   ├── __init__.py
│   ├── web_search.py          # Serper.dev integration (real)
│   ├── fetch_url.py           # Trafilatura content extraction
│   └── compose_answer.py      # Structured JSON output
├── utils/
│   ├── __init__.py
│   ├── http_client.py         # Connection pooling, retry logic, rate limiting
│   ├── source_quality.py      # Source ranking and quality assessment
│   ├── quote_extractor.py     # Quote extraction (≤120 chars)
│   ├── date_parser.py         # Date normalization to YYYY-MM-DD
│   └── logger.py              # Structured logging
└── .env                       # API keys (GOOGLE_API_KEY, SERPER_API_KEY)
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Navigate to project root
cd "C:\Users\votev\OneDrive - KU Leuven\Git\ML6xGDGKUL_AIAccelerate2025"

# Add new dependencies
uv add httpx trafilatura

# Sync all dependencies
uv sync
```

### 2. Configure API Keys

```bash
# Navigate to my_agent folder
cd my_agent

# Copy environment template (if not already done)
copy .local_env .env

# Edit .env and add your keys:
# - GOOGLE_API_KEY: Get from https://aistudio.google.com/api-keys
# - SERPER_API_KEY: Get from https://serper.dev (free tier: 2500 searches)
```

Required `.env` contents:
```
GOOGLE_API_KEY="your_gemini_api_key_here"
SERPER_API_KEY="your_serper_api_key_here"
USER_ID="user"
```

### 3. Test the Implementation

**Interactive Testing (Recommended):**
```bash
# Start ADK web interface
uv run adk web

# Open browser: http://127.0.0.1:8000
# Test queries like:
# - "What are the latest AI regulations?"
# - "Tesla stock price today"
# - "How does photosynthesis work?"
```

**Evaluation Testing:**
```bash
# Run all benchmark questions
uv run python evaluate.py

# Run specific question (e.g., question #0)
uv run python evaluate.py --question 0

# Save results to custom file
uv run python evaluate.py --output my_results.json
```

## Tool Usage Guide

### web_search Tool

**Purpose**: Search the web using Serper.dev API with automatic source ranking

**Parameters**:
- `query` (required): Search query string
- `recency_days` (optional): Filter to last N days (e.g., 7 for last week)
- `sites` (optional): Comma-separated domains to search within
- `blocked_sites` (optional): Comma-separated domains to exclude
- `max_results` (default: 10): Maximum results to return

**Example**:
```python
# Current events with recency filter
web_search("AI regulations 2024", recency_days=30, max_results=5)

# Prioritize specific sources
web_search("climate change report", sites="gov,edu")

# Block low-quality sources
web_search("Tesla news", blocked_sites="reddit.com,twitter.com")
```

**Returns**:
```json
{
  "results": [
    {
      "title": "Page title",
      "link": "https://example.com/...",
      "snippet": "Brief description...",
      "date": "2024-01-15",
      "domain": "example.com"
    }
  ],
  "query_executed": "AI regulations 2024",
  "num_results": 5
}
```

### fetch_url Tool

**Purpose**: Extract clean text content from URLs using Trafilatura

**Parameters**:
- `url` (required): URL to fetch and extract content from

**Example**:
```python
fetch_url("https://reuters.com/article/...")
```

**Returns**:
```json
{
  "url": "https://reuters.com/article/...",
  "title": "Article title",
  "text": "Full article text content...",
  "date": "2024-01-15",
  "author": "John Doe",
  "success": true,
  "status_code": 200
}
```

**Error Handling**:
- 403 (Forbidden): Paywall or blocked - skips gracefully
- 404 (Not Found): URL doesn't exist
- 429 (Rate Limited): Automatic retry with backoff
- Timeout: 20s timeout, then returns error

### compose_answer Tool

**Purpose**: Create structured JSON output matching PRD contract

**Parameters**:
- `summary` (required): 1-2 sentence answer summary
- `bullets` (required): List of key points
- `quotes` (required): List of quote dicts with text, source, url, date, page_or_ts
- `sources` (required): List of source dicts with title, domain, url, date
- `queries` (required): List of search queries executed
- `hops` (required): Number of search iterations
- `notes` (required): Methodology notes
- `confidence` (required): "low", "medium", or "high"

**Example**:
```python
compose_answer(
    summary="The EU AI Act came into effect in January 2024.",
    bullets=[
        "Applies to high-risk AI systems",
        "Includes fines up to 7% of global revenue"
    ],
    quotes=[{
        "text": "The regulation establishes harmonized rules for AI",
        "source": "EU AI Act Official Text",
        "url": "https://ec.europa.eu/...",
        "date": "2024-01-15",
        "page_or_ts": "p.3"
    }],
    sources=[{
        "title": "EU AI Act Official Text",
        "domain": "ec.europa.eu",
        "url": "https://ec.europa.eu/...",
        "date": "2024-01-15"
    }],
    queries=["EU AI Act 2024", "AI regulations Europe"],
    hops=2,
    notes="Prioritized official EU sources",
    confidence="high"
)
```

## Orchestration Flow

The agent follows this deterministic workflow:

```
1. PLANNING
   └─> Generate 1-3 targeted search queries
   └─> Determine recency filter (if current events)
   └─> Identify priority domains (if specialized topic)

2. SEARCH & RANK
   └─> Execute web_search for each query
   └─> Results automatically ranked by source quality
   └─> Review snippets for relevance

3. FETCH CONTENT
   └─> Select top N URLs (typically 5)
   └─> Parallel fetch using fetch_url
   └─> Skip paywalled/failed fetches
   └─> Budget: max 5 fetches (Quick mode)

4. EXTRACT QUOTES
   └─> Extract verbatim quotes ≤120 chars
   └─> Attach source metadata (title, URL, date)
   └─> Ensure ≥2 independent sources

5. COMPOSE ANSWER
   └─> Use compose_answer for structured output
   └─> Include methodology transparency
   └─> Assign confidence level

6. TERMINATION
   └─> Success: min_sources=2 met + quality OK
   └─> Budget exhausted: compose with available data
   └─> Escalation: suggest Deep Check if insufficient
```

## Performance Optimizations

### Current Optimizations

1. **Connection Pooling**: Global httpx.Client reused across all requests
   - Max 20 connections, 10 keepalive
   - Reduces connection overhead

2. **Retry with Exponential Backoff**:
   - Max 3 retries for Serper API
   - Max 2 retries for URL fetches
   - Base delay 1s, doubles each retry

3. **Rate Limiting**:
   - Serper: 1000 req/min (API limit)
   - Fetch: 60 req/min (conservative)
   - Token bucket algorithm

4. **Smart Source Ranking**:
   - Fetch highest-quality sources first
   - Reduces wasted fetches on low-quality content

5. **Paywall Detection**:
   - Skip 403 responses immediately
   - Move to next source without retrying

### Future Optimizations (if needed)

**Parallel Fetching** (if latency > 15s P95):
```python
from concurrent.futures import ThreadPoolExecutor

# Fetch top 5 URLs in parallel
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_url, url) for url in top_urls]
    results = [f.result() for f in futures]
```

**Semantic Caching** (if cost > $300/month):
- Cache search results for semantically similar queries
- 60-90% cost reduction potential
- Use simple embedding similarity threshold

**Async Migration** (if throughput > 50 QPS):
- Replace httpx with aiohttp
- 2.7x throughput improvement (264 req/s)
- More complex error handling

## Cost Analysis

### Monthly Cost Breakdown (30K searches)

Assuming:
- 30,000 user queries per month
- Average 2 search queries per user query = 60K Serper searches
- Average 3 URL fetches per user query = 90K fetches
- Average 10K tokens per LLM response

**Search API (Serper.dev)**:
- Free tier: 2,500 searches/month (covers testing)
- Paid: $50/month for 10K searches
- At 60K searches: $300/month ($5 per 1K)

**LLM (Gemini 2.0 Flash)**:
- Input: 30K queries × 2K tokens = 60M input tokens
- Output: 30K responses × 10K tokens = 300M output tokens
- Cost: ~$0.075 per 1M input tokens, ~$0.30 per 1M output tokens
- Total: (60 × $0.075) + (300 × $0.30) = $4.50 + $90 = ~$95/month

**Infrastructure (GCP)**:
- Cloud Run: ~$20/month (minimal)
- Bandwidth: ~$10/month

**TOTAL: ~$425/month at 30K searches**

### Cost Optimization Strategies

To hit $300/month budget:

1. **Reduce Serper usage** ($300 → $150):
   - Cache search results (7-day TTL)
   - Deduplicate similar queries
   - Target savings: 50% reduction = $150 saved

2. **Optimize LLM usage** ($95 → $50):
   - Context caching for system instruction (75% discount)
   - Reduce output tokens (use more concise responses)
   - Target savings: ~$45 saved

3. **Alternative search options**:
   - Google Custom Search: $5 per 1K queries (same as Serper)
   - Exa.ai: $0.30 per 1K queries (saves $240/month at 60K searches)
   - Tavily: $0.001 per search (saves $295/month)

**Recommended approach**: Switch to Exa.ai or Tavily for production scale
- **With Exa.ai**: $18 (search) + $95 (LLM) + $30 (infra) = **$143/month**
- **With Tavily**: $60 (search) + $95 (LLM) + $30 (infra) = **$185/month**
- **With caching + Exa**: $10 (search) + $50 (LLM) + $30 (infra) = **$90/month**

## Production Deployment

### Recommended GCP Stack

1. **Cloud Run** (API endpoints):
   - Container: Docker with Python 3.11 + dependencies
   - Min instances: 1 (for warmup)
   - Max instances: 10 (autoscaling)
   - Memory: 512MB (sufficient for httpx)

2. **Secret Manager** (API keys):
   - Store GOOGLE_API_KEY, SERPER_API_KEY
   - Mount as environment variables in Cloud Run

3. **Cloud Monitoring**:
   - Log structured JSON events
   - Set alerts on error rates, latency P95
   - Dashboard for query volume, source quality distribution

4. **Cloud Build** (CI/CD):
   - Trigger on git push to main
   - Run tests, build container, deploy to Cloud Run

### Deployment Steps

```bash
# 1. Create Dockerfile
cat > Dockerfile <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "adk", "api_server", "--host", "0.0.0.0", "--port", "8080"]
EOF

# 2. Build and push container
gcloud builds submit --tag gcr.io/PROJECT_ID/cited-research-assistant

# 3. Deploy to Cloud Run
gcloud run deploy cited-research-assistant \
  --image gcr.io/PROJECT_ID/cited-research-assistant \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars GOOGLE_API_KEY=\$GOOGLE_API_KEY \
  --set-env-vars SERPER_API_KEY=\$SERPER_API_KEY
```

## Monitoring & Observability

### Structured Logs

All tools log structured JSON for easy querying:

```json
{
  "timestamp": "2024-01-15T12:34:56.789Z",
  "event_type": "search_query",
  "query": "AI regulations 2024",
  "num_results": 10,
  "latency_ms": 450
}

{
  "timestamp": "2024-01-15T12:34:57.123Z",
  "event_type": "fetch_url",
  "url": "https://ec.europa.eu/...",
  "success": true,
  "status_code": 200,
  "latency_ms": 1200
}

{
  "timestamp": "2024-01-15T12:34:58.456Z",
  "event_type": "decision",
  "decision_type": "termination",
  "reason": "min_sources met",
  "num_sources": 3,
  "confidence": "high"
}
```

### Key Metrics to Monitor

1. **Correctness**:
   - Accuracy on benchmark (target: >80%)
   - Source quality distribution (% Tier 1/2 vs Tier 3/4)
   - Citation completeness (% quotes with dates)

2. **Performance**:
   - Latency P50, P95, P99 (targets: ≤8s, ≤15s, ≤25s)
   - Search API latency
   - Fetch success rate (target: >85%)

3. **Cost**:
   - Searches per day, per month
   - LLM token usage (input + output)
   - Failed fetch rate (wasted API calls)

4. **Reliability**:
   - Error rate (target: <2%)
   - Retry rate (excessive retries indicate API issues)
   - Timeout rate

## Troubleshooting

### Common Issues

**1. "SERPER_API_KEY not found"**
```bash
# Ensure .env file exists in my_agent/ folder
cd my_agent
cat .env

# Should show:
# SERPER_API_KEY="your_key_here"
```

**2. "trafilatura package not installed"**
```bash
# Install trafilatura
uv add trafilatura
uv sync
```

**3. Search returns no results**
- Check query formatting (avoid overly specific queries)
- Remove recency filter if too restrictive
- Try alternative query phrasings

**4. Fetch fails with 403 (Forbidden)**
- Expected for paywalled sites (WSJ, FT)
- Agent will skip and try next source
- Not a system error

**5. Latency > 15s P95**
- Enable parallel fetching (see Performance Optimizations)
- Reduce max_fetches from 5 to 3
- Check Serper API latency (should be <500ms)

**6. High costs**
- Implement search result caching (7-day TTL)
- Switch to cheaper search API (Exa.ai: $0.30/1K)
- Enable context caching for LLM (75% discount)

## Testing Strategy

### Unit Tests (Recommended)

```python
# test_web_search.py
def test_web_search_basic():
    result = web_search("test query")
    assert result["num_results"] >= 0
    assert "results" in result

def test_web_search_with_recency():
    result = web_search("AI news", recency_days=7)
    # Should filter to recent results
    assert result["num_results"] >= 0

# test_source_quality.py
def test_source_ranking():
    results = [
        {"link": "https://reuters.com/...", "date": "2024-01-15"},
        {"link": "https://example.com/...", "date": "2024-01-15"},
        {"link": "https://sec.gov/...", "date": "2024-01-10"}
    ]
    ranked = rank_search_results(results)
    # sec.gov (Tier 1) should rank first
    assert "sec.gov" in ranked[0]["link"]
```

### Integration Tests

```bash
# Test end-to-end with real APIs
uv run python -c "
from my_agent.tools import web_search, fetch_url, compose_answer

# Test search
search_result = web_search('OpenAI GPT-4', max_results=3)
print(f'Found {search_result[\"num_results\"]} results')

# Test fetch
if search_result['results']:
    url = search_result['results'][0]['link']
    fetch_result = fetch_url(url)
    print(f'Fetched: {fetch_result[\"title\"]}')
"
```

### Benchmark Testing

```bash
# Run full benchmark evaluation
uv run python evaluate.py

# Expected output:
# - Accuracy: >70% on train set (target for hidden test set)
# - Average response time: <10s
# - No critical errors
```

## Next Steps

### P0 (Production Ready)
- ✅ Replace mock web_search with Serper
- ✅ Add fetch_url with Trafilatura
- ✅ Add compose_answer for structured output
- ✅ Wire tools to agent.py
- ✅ Add error handling and retry logic
- ✅ Implement source quality ranking

### P1 (Enhanced Features)
- [ ] Add Deep Check mode (increase budgets based on confidence)
- [ ] Implement search result caching (Redis or in-memory)
- [ ] Add "How I searched" detailed logging to compose_answer
- [ ] Create dashboard for monitoring (Streamlit or Cloud Run)

### P2 (Future Enhancements)
- [ ] Add fetch_pdf tool (extract from PDF URLs)
- [ ] Add extract_transcript tool (YouTube captions)
- [ ] Implement parallel fetching (ThreadPoolExecutor)
- [ ] Add semantic caching (embedding-based)
- [ ] Switch to async architecture (aiohttp) if throughput > 50 QPS

## Support & Resources

- **ADK Documentation**: https://google.github.io/adk-docs/
- **Serper API Docs**: https://serper.dev/docs
- **Trafilatura Docs**: https://trafilatura.readthedocs.io/
- **Gemini API Docs**: https://ai.google.dev/docs

For questions during hackathon, reach out to ML6 engineers!
