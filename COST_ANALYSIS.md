# Cost Analysis & Optimization Strategy

## Executive Summary

**Target Budget**: $300/month
**Current Architecture Cost**: $425/month at 30K searches
**Optimized Cost**: $143-185/month with recommended changes

## Baseline Assumptions

- **Query Volume**: 30,000 user queries per month
- **Search Multiplier**: 2 Serper searches per user query = 60,000 searches/month
- **Fetch Operations**: 3 URL fetches per query = 90,000 fetches/month
- **LLM Token Usage**: 2K input tokens, 10K output tokens per response

## Current Cost Breakdown (30K queries/month)

### 1. Search API: Serper.dev

**Pricing Tiers**:
- Free: 2,500 searches/month (testing only)
- Developer: $50/month for 10,000 searches
- Scale: $5 per 1,000 searches for higher volumes

**Our Usage**: 60,000 searches/month
- Cost: 60 × $5 = **$300/month**

**Rate Limits**: 1,000 requests/minute (sufficient for our needs)

### 2. LLM: Gemini 2.0 Flash

**Pricing** (as of Jan 2025):
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Context Caching: 75% discount on cached tokens

**Our Usage**:
- Input: 30K queries × 2K tokens = 60M input tokens
  - System instruction: ~2K tokens per query
  - User query: ~100 tokens per query
  - Tool responses: ~1K tokens average
- Output: 30K responses × 10K tokens = 300M output tokens
  - Structured JSON output
  - Citations, quotes, methodology

**Cost**:
- Input: 60M × $0.075/1M = $4.50
- Output: 300M × $0.30/1M = $90.00
- **Total: $94.50/month**

### 3. Infrastructure: GCP

**Cloud Run**:
- vCPU: 1 vCPU × 730 hours/month = 730 vCPU-hours
- Memory: 512MB × 730 hours = 365 GB-hours
- Requests: 30,000 requests/month
- Cost: ~$20/month

**Bandwidth**:
- URL fetches: 90K × 50KB average = 4.5 GB egress
- Cost: ~$10/month

**Total Infrastructure**: $30/month

### 4. Dependencies: Trafilatura

- Open source (Python library)
- No API costs
- CPU overhead minimal (included in Cloud Run costs)

## Total Current Cost: $424.50/month

**Breakdown**:
- Search API (Serper): $300
- LLM (Gemini): $95
- Infrastructure (GCP): $30

**Exceeds budget by**: $124.50/month (42% over)

## Cost Optimization Strategies

### Strategy 1: Alternative Search APIs

Replace Serper with cheaper alternatives:

#### Option A: Exa.ai

**Pricing**: $0.30 per 1,000 searches (17× cheaper)

**Cost at 60K searches**: 60 × $0.30 = **$18/month**
**Savings**: $282/month

**Pros**:
- Neural search (semantic understanding)
- Good for academic/research queries
- Clean, well-structured results
- 1,000 searches/day free tier (testing)

**Cons**:
- Smaller index than Google
- May miss some recent news
- API rate limit: 100 req/min (sufficient)

**Implementation**:
```python
# Exa API call (drop-in replacement)
import exa_py

client = exa_py.Exa(api_key=os.getenv("EXA_API_KEY"))
results = client.search(
    query="AI regulations 2024",
    num_results=10,
    use_autoprompt=True
)
```

#### Option B: Tavily AI

**Pricing**: $0.001 per search (5000× cheaper!)

**Cost at 60K searches**: 60K × $0.001 = **$60/month**
**Savings**: $240/month

**Pros**:
- Purpose-built for AI agents
- Extremely cost-effective
- Good accuracy for factual queries
- 1,000 searches/month free tier

**Cons**:
- Smaller index
- Less control over ranking
- Beta product (may have stability issues)

**Implementation**:
```python
# Tavily API call
from tavily import TavilyClient

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
results = client.search(
    query="AI regulations 2024",
    max_results=10,
    search_depth="advanced"
)
```

#### Option C: Google Custom Search API

**Pricing**: $5 per 1,000 queries (same as Serper)

**Cost at 60K searches**: 60 × $5 = **$300/month**
**Savings**: $0 (no savings)

**Pros**:
- Official Google results
- Massive index coverage
- Reliable and stable

**Cons**:
- Same cost as Serper
- More complex setup (requires search engine ID)
- 100 queries/day free tier (very limited)

**Not recommended** for cost optimization.

### Strategy 2: Search Result Caching

Implement semantic caching to reduce duplicate searches.

**Approach**:
1. Embed query using Gemini text-embedding-004
2. Check cache for similar queries (cosine similarity > 0.9)
3. Return cached results if hit, otherwise search and cache

**Expected Hit Rate**: 30-50% (based on Anthropic research)

**Savings**:
- 40% hit rate = 24K fewer searches
- At Serper: 24K × $5/1K = $120 saved
- At Exa: 24K × $0.30/1K = $7.20 saved
- At Tavily: 24K × $0.001 = $24 saved

**Implementation Cost**:
- Embedding API: 60K queries × 2K tokens = 120M tokens
- Gemini embedding cost: $0.025 per 1M tokens (Batch API)
- Cost: 120 × $0.025 = **$3/month**
- Redis cache: $10-20/month (Cloud Memorystore)

**Net Savings with Serper**: $120 - $3 - $15 (Redis) = $102/month
**Net Savings with Exa**: $7.20 - $3 - $15 = **-$10.80/month** (not worth it)

**Recommendation**: Only implement if using Serper. Not cost-effective with Exa/Tavily.

### Strategy 3: LLM Optimization

#### 3a. Context Caching

Enable context caching for system instruction (reused across all queries).

**Savings**:
- System instruction: ~2K tokens per query
- With caching: 75% discount on cached tokens
- Savings: 30K × 2K × 75% = 45M tokens × $0.075/1M = **$3.38/month**

**Implementation**:
```python
# Enable context caching in ADK
root_agent = llm_agent.Agent(
    model='gemini-flash-lite-latest',
    instruction=SYSTEM_INSTRUCTION,  # This will be cached
    tools=[web_search, fetch_url, compose_answer],
    # Context caching enabled automatically for long instructions
)
```

**Effort**: Minimal (ADK handles automatically)
**Recommendation**: Implement immediately (free optimization)

#### 3b. Reduce Output Tokens

Optimize compose_answer to generate more concise responses.

**Target**: Reduce from 10K to 5K output tokens per response

**Approach**:
- Limit quotes to 3 per answer (vs current 5)
- Shorten summary to 1 sentence (vs 2)
- Reduce bullet points to 3 key points (vs 5)

**Savings**:
- 30K responses × 5K fewer tokens = 150M tokens
- 150M × $0.30/1M = **$45/month**

**Trade-off**: May reduce answer completeness, potentially lowering accuracy

**Recommendation**: Test carefully, ensure accuracy >80% before deploying

#### 3c. Batch Processing (Future)

For non-interactive queries, use Batch API (50% discount).

**Savings**: $47.50/month (50% of current $95 LLM cost)

**Trade-off**: 24-hour latency (not suitable for interactive use)

**Recommendation**: Only for offline evaluation/benchmarking

### Strategy 4: Budget-Based Early Termination

Reduce max_fetches from 5 to 3 for Quick mode.

**Savings**:
- 30K queries × 2 fewer fetches = 60K fewer fetch operations
- Fetch cost: Minimal (Trafilatura is free)
- Indirect savings: Faster responses = lower Cloud Run CPU time

**Estimated Savings**: $5-10/month (Cloud Run CPU)

**Trade-off**: May reduce citation quality (fewer sources available)

**Recommendation**: Test with benchmark, ensure accuracy maintained

## Recommended Optimization Plan

### Phase 1: Quick Wins (Implement Immediately)

1. **Enable context caching** for system instruction
   - Savings: $3.38/month
   - Effort: 5 minutes (already supported by ADK)

2. **Switch from Serper to Exa.ai**
   - Savings: $282/month
   - Effort: 2-3 hours (refactor web_search.py)
   - Risk: Low (Exa has good documentation, similar API)

**Total Phase 1 Savings**: $285.38/month
**New Monthly Cost**: $139.12/month ✅ UNDER BUDGET

### Phase 2: Additional Optimizations (If Needed)

3. **Reduce output tokens** (10K → 5K)
   - Savings: $45/month
   - Effort: 1-2 hours (adjust prompts, test)
   - Risk: Medium (may impact accuracy)

4. **Implement search caching** (if using Serper)
   - Net savings: $102/month with Serper
   - Effort: 4-6 hours (Redis setup, embedding logic)
   - Risk: Low (improves latency too)

### Phase 3: Long-Term (Future Optimization)

5. **Migrate to async architecture** (httpx → aiohttp)
   - Savings: Indirect (lower Cloud Run costs via faster responses)
   - Effort: 1-2 days
   - Risk: Medium (significant refactor)

6. **Implement smart budget allocation**
   - Detect simple queries (reduce to 1 search, 2 fetches)
   - Reserve full budget for complex queries
   - Savings: ~20% reduction in average API usage

## Cost Comparison: Search API Options

| Search API | Cost (60K searches) | Index Size | Rate Limit | Free Tier | Best For |
|-----------|---------------------|------------|------------|-----------|----------|
| Serper.dev | $300/month | Massive (Google) | 1000/min | 2.5K/month | Production quality |
| Exa.ai | $18/month | Large | 100/min | 1K/day | Cost-optimized, semantic search |
| Tavily AI | $60/month | Medium | Varies | 1K/month | Agent-specific, budget |
| Google CSE | $300/month | Massive | 100/day | 100/day | Official Google results |

**Recommendation**: Start with Exa.ai for cost optimization. If accuracy issues arise, fallback to Serper or Tavily.

## Final Optimized Cost (Phase 1 + 2)

| Component | Original Cost | Optimized Cost | Savings |
|-----------|--------------|----------------|---------|
| Search API | $300 (Serper) | $18 (Exa) | $282 |
| LLM Input | $4.50 | $1.12 (caching) | $3.38 |
| LLM Output | $90 | $45 (fewer tokens) | $45 |
| Infrastructure | $30 | $30 | $0 |
| **TOTAL** | **$424.50** | **$94.12** | **$330.38** |

**Final Cost**: $94.12/month
**Budget**: $300/month
**Under Budget By**: $205.88/month (69% savings)
**Runway Extended**: 3.2× longer (from budget perspective)

## Risk Assessment

### Switching to Exa.ai

**Risks**:
- Smaller index may miss some sources
- Different ranking algorithm may affect source quality
- Less tested for news/current events

**Mitigation**:
- Run A/B test on benchmark (Serper vs Exa)
- Implement fallback: if Exa returns <5 results, retry with Serper
- Monitor accuracy closely in first month

**Expected Impact**: 5-10% accuracy drop acceptable if cost savings maintained

### Reducing Output Tokens

**Risks**:
- Fewer quotes = less citation depth
- May fail PRD requirement of "≥2 sources per claim"

**Mitigation**:
- Ensure min_sources=2 enforced in all cases
- Quality over quantity: keep best quotes, drop weaker ones

**Expected Impact**: Minimal if done carefully (quotes are redundant)

## Monitoring & Alerts

Set up cost alerts in GCP:

```bash
# Set budget alert at $250/month (before hitting $300 limit)
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Cited Research Assistant Budget" \
  --budget-amount=250 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

Track key metrics:
- **Daily search volume**: Alert if >2,500/day (75K/month trajectory)
- **LLM token usage**: Alert if >15M output tokens/day
- **Cache hit rate**: Target >30% (if caching enabled)
- **Fetch success rate**: Monitor for expensive failures

## Conclusion

**Recommended Path**:

1. **Implement Phase 1 immediately** (Exa + context caching)
   - Cost: $139/month
   - Time: 2-3 hours
   - Risk: Low

2. **Monitor benchmark accuracy** for 1 week
   - Target: >80% accuracy maintained
   - If <80%: Revert to Serper, implement caching instead

3. **If budget allows, keep Serper** ($300 search + $95 LLM + $30 infra = $425)
   - Fund additional $125/month for better quality
   - Still reasonable for production use

4. **Long-term: Implement caching + async** for optimal cost/performance

**Bottom line**: With Exa.ai, you'll be well under budget at $139/month while maintaining acceptable accuracy. This leaves $161/month buffer for unexpected usage spikes or future feature development.
