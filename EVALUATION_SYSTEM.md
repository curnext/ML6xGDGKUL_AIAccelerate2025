# Agent Evaluation System Documentation

## Overview

The `evaluate.py` script is the core evaluation system for assessing your agent's performance in the GDG Hackathon. It tests your agent against a benchmark dataset and provides detailed metrics on accuracy and response times.

## How It Works

### 1. Dataset Loading

The system loads questions from `benchmark/train.json`, which contains:
- **Questions**: Natural language queries for the agent
- **Expected Answers**: Ground truth answers for evaluation
- **Attachments**: Optional file references (from `benchmark/attachments/`)

### 2. Question Processing

For each question, the evaluator:
1. Extracts the question text and expected answer
2. Loads any required attachment files
3. Sends the question to your agent via `server.run_agent()`
4. Records the agent's response and response time

### 3. Two-Stage Evaluation System

The evaluation uses a hierarchical approach:

#### Stage 1: String Matching (Fast & Free)
- **Method**: Case-insensitive exact string comparison
- **Advantage**: Instant evaluation, no API costs
- **When it passes**: Your answer exactly matches the expected answer (ignoring case and whitespace)

```python
# Example:
Agent Response: "the answer is 42"
Expected Answer: "The Answer Is 42"
Result: ✓ MATCH (case-insensitive)
```

#### Stage 2: LLM Judge (Fallback)
- **Model**: Gemini 2.5 Flash Lite
- **Method**: Semantic evaluation of answer equivalence
- **When activated**: Only if string matching fails
- **Evaluation**: Determines if your answer is semantically equivalent to the expected answer

```python
# Example:
Agent Response: "The capital of France is Paris"
Expected Answer: "Paris"
Result: ✓ CORRECT (semantically equivalent)
```

**Important**: The LLM judge is strict but fair. Minor wording variations are acceptable if the core answer is correct.

### 4. Metrics Collected

#### Primary Metric: Accuracy
- **Formula**: `(Correct Answers / Total Questions) × 100`
- **This is your main score** - focus on maximizing this!

#### Secondary Metrics: Response Time
- **Average Response Time (All)**: Mean time across all questions
- **Average Response Time (Correct Only)**: Mean time for correct answers only
- Used as a tiebreaker if accuracy is equal

### 5. Results Output

Results are saved to a JSON file with:
- Timestamp
- Overall accuracy and timing metrics
- Detailed results for each question
- Evaluation method used (string match vs LLM judge)

---

## How to Use the Evaluator

### Evaluate All Questions
```bash
python evaluate.py
```
This runs through the entire benchmark dataset and provides comprehensive results.

### Evaluate a Single Question
```bash
python evaluate.py --question 5
```
Test your agent on question #5 only (0-indexed). Useful for debugging specific failures.

### Specify Output File
```bash
python evaluate.py --output my_results.json
```
Save results to a custom filename instead of the default timestamp format.

---

## What Determines Your Score

### 🎯 Critical Factors (In Order of Importance)

#### 1. **Answer Accuracy** (Primary Score)
- Every correct answer increases your accuracy percentage
- **This is the main metric used for ranking**
- A agent with 80% accuracy beats one with 70%, regardless of speed

#### 2. **Response Time** (Tiebreaker)
- Only matters when accuracy is identical
- Faster agents rank higher in case of ties
- Two metrics tracked:
  - Average time for all questions
  - Average time for correct answers only

#### 3. **Consistency**
- Getting the same questions correct every time
- The evaluation may be run multiple times

---

## Key Areas to Focus On

### 🚀 High-Impact Improvements

#### 1. **Improve Answer Accuracy** ⭐ HIGHEST PRIORITY
Focus your efforts here for maximum score improvement:

- **Understand the question types** in the benchmark
- **Test iteratively**: Use `python evaluate.py --question N` to debug failures
- **Analyze failed questions**: Check `evaluation_results_*.json` to see which questions you're missing
- **Improve reasoning**: Make sure your agent thinks through problems step-by-step
- **Better tool usage**: Ensure your agent is using the right tools for each question type

**Quick Win**: Run a full evaluation, identify the most common failure patterns, and fix those first.

#### 2. **Answer Format Matching**
Many failures happen due to format mismatches:

- **Be concise**: If the expected answer is "42", don't return "The answer to the question is 42"
- **Match format**: If expected answer is a number, return just the number
- **Strip fluff**: Remove unnecessary preambles like "Based on my analysis..."
- **Test formats**: Use `--question` flag to test individual questions and tweak your response format

**Pro Tip**: String matching is instant and free. Format your answers to match exactly and you'll pass faster without using the LLM judge.

#### 3. **Handling Attachments**
Some questions include file attachments:

- **File awareness**: Make sure your agent can process attached files
- **Multiple files**: Some questions have multiple comma-separated files
- **File types**: Handle various file formats (images, documents, data files)
- **Context extraction**: Extract relevant information from files to answer questions

#### 4. **Reduce Unnecessary Processing**
While speed is secondary, it's still important:

- **Optimize tool calls**: Don't make redundant API calls
- **Cache results**: Reuse information when possible
- **Early returns**: Once you have the answer, return immediately
- **Efficient prompting**: Use concise, focused prompts

---

## Evaluation Architecture

```
┌─────────────────────────────────────────────────────┐
│                  evaluate.py                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Load benchmark/train.json                      │
│  2. For each question:                             │
│     ┌─────────────────────────────────────────┐   │
│     │ Call: server.run_agent()                │   │
│     │   ↓                                      │   │
│     │ Your Agent (my_agent/agent.py)          │   │
│     │   ↓                                      │   │
│     │ Agent Response                           │   │
│     └─────────────────────────────────────────┘   │
│  3. Evaluation Pipeline:                           │
│     ┌─────────────────────────────────────────┐   │
│     │ String Match?                           │   │
│     │   ├─ YES → ✓ Correct                    │   │
│     │   └─ NO  → LLM Judge                    │   │
│     │               ├─ Equivalent → ✓ Correct │   │
│     │               └─ Different  → ✗ Wrong   │   │
│     └─────────────────────────────────────────┘   │
│  4. Calculate metrics (accuracy, timing)           │
│  5. Save results to JSON                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Debugging Strategy

### Step-by-Step Debugging Process

1. **Run Full Evaluation**
   ```bash
   python evaluate.py
   ```

2. **Analyze Results**
   - Open the generated `evaluation_results_*.json`
   - Find questions where `"correct": false`
   - Note the `question_idx` for failed questions

3. **Debug Individual Failures**
   ```bash
   python evaluate.py --question <idx>
   ```
   - Watch your agent's response
   - Compare with expected answer
   - Identify the gap

4. **Iterate on Agent Logic**
   - Modify `my_agent/agent.py`
   - Re-test the specific question
   - Once fixed, run full evaluation again

5. **Track Progress**
   - Save each evaluation result with meaningful names
   - Compare accuracy over time
   - Focus on questions you're still missing

---

## Environment Requirements

### Required Environment Variables

Set in `my_agent/.env`:
```bash
GOOGLE_API_KEY=your_api_key_here  # Required for LLM judge
USER_ID=dev_user                   # Optional, defaults to "dev_user"
```

### Required Python Packages

The evaluation system uses:
- `google-genai`: For LLM judge
- `pydantic`: For structured LLM responses
- `colorama`: For colored terminal output
- `pyfiglet`: For ASCII art banner
- `dotenv`: For environment variable loading

---

## Common Pitfalls to Avoid

### ❌ Don't Do This

1. **Over-explaining answers**
   - Bad: "After careful analysis, I believe the answer is 42"
   - Good: "42"

2. **Ignoring answer format**
   - If expected answer is lowercase, match it
   - If expected answer is a number, return just the number

3. **Not handling files**
   - Questions with attachments need file processing
   - Missing file handling = guaranteed failures

4. **Making agent too slow**
   - While accuracy matters most, extreme slowness may indicate inefficiency
   - If your agent takes >60s per question, consider optimization

5. **Not testing incrementally**
   - Always test individual questions after changes
   - Don't wait to run full evaluation

### ✅ Do This Instead

1. **Format answers concisely**
2. **Test often with `--question` flag**
3. **Analyze failure patterns in JSON results**
4. **Focus on accuracy first, speed second**
5. **Handle all attachment types properly**

---

## Score Improvement Checklist

Use this checklist to systematically improve your score:

- [ ] Run initial full evaluation to establish baseline
- [ ] Identify top 3 failure patterns from results JSON
- [ ] Fix formatting issues (common quick win)
- [ ] Ensure file attachment handling works
- [ ] Test each fix with `--question` before full re-evaluation
- [ ] Optimize agent reasoning and tool usage
- [ ] Run multiple full evaluations to ensure consistency
- [ ] Compare response formats with expected answers
- [ ] Reduce unnecessary processing time
- [ ] Final full evaluation run for submission

---

## Summary: The Path to High Scores

### Priority 1: Maximize Accuracy ⭐⭐⭐
- This is 90% of your score
- Focus all effort here first
- Every correct answer matters

### Priority 2: Format Answers Correctly ⭐⭐
- String matches are instant wins
- Match expected answer format exactly
- Remove unnecessary context from responses

### Priority 3: Optimize Response Time ⭐
- Only matters for tiebreaking
- Don't sacrifice accuracy for speed
- But avoid obviously wasteful operations

**Bottom Line**: A agent that gets 100% accuracy in 30 seconds beats one with 95% accuracy in 5 seconds. Accuracy is king!

---

## Questions?

If you're unsure about evaluation behavior:
1. Check the `evaluation_results_*.json` for details
2. Run `python evaluate.py --question N` to debug specific questions
3. Review your agent's responses vs expected answers
4. Refer to this documentation for evaluation methodology

Good luck! 🚀

