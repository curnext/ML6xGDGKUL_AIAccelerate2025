# Welcome to the GDG Hackathon - ML6 Agent Challenge!

This guide will help you get started quickly with building your AI agent.

## Quick Start (5 minutes)

### 1. Setup Your API Key
```bash
# Copy the example environment file
cp my_agent/.local_env my_agent/.env

# Edit my_agent/.env and add your API key:
# GOOGLE_API_KEY="your_actual_api_key_here"
# USER_ID="user"
```

Get your API key from: https://aistudio.google.com/api-keys

### 2. Install Dependencies
```bash
uv sync
```

### 3. Test Your Agent
```bash
# Interactive web interface (recommended for development)
uv run adk web
# Then open http://127.0.0.1:8000 in your browser

# Or run evaluation against the training dataset
uv run python evaluate.py
```

## Understanding the "Database"

**Important:** This project doesn't use a traditional database. Here's where the data is:

### Training Dataset
- **Location:** `benchmark/train.json`
- **Contains:** 5 questions with answers
- **Format:**
  ```json
  {
    "dataset": [
      {
        "question": "What is...",
        "answer": "The answer is...",
        "file_name": "optional_attachment.pdf"
      }
    ]
  }
  ```

### How to "Search" the Database
```python
# In your code, you can load the dataset:
import json

with open("benchmark/train.json", "r") as f:
    data = json.load(f)
    questions = data["dataset"]

# Access specific questions:
first_question = questions[0]["question"]
first_answer = questions[0]["answer"]
```

### Attachments
- **Location:** `benchmark/attachments/`
- Some questions reference files (PDFs, images, etc.)
- These are automatically loaded during evaluation

## Customizing Your Agent

### Main Configuration File
**File:** `my_agent/agent.py`

This is where you configure:
- The AI model to use
- System instructions (how the agent behaves)
- Available tools

### Changing the Model

To use `gemini-flash-lite-latest` (or any other model):

```python
# In my_agent/agent.py, change the model parameter:
root_agent = llm_agent.Agent(
    model='gemini-flash-lite-latest',  # Change this line
    name='agent',
    description="An AI agent that can answer complex questions",
    instruction="Your system instructions here",
    tools=[web_search],
)
```

Available models:
- `gemini-flash-lite-latest` (default - fast and lightweight)
- `gemini-2.5-pro` (for accuracy)

### Adding Custom Tools

Tools extend what your agent can do. Create new tools in `my_agent/tools/`:

```python
# Example: my_agent/tools/my_tool.py
from google.genai import types

def my_tool(parameter: str) -> str:
    """Tool description that the agent sees."""
    # Your tool logic here
    return "result"

# Then register in my_agent/agent.py:
from .tools.my_tool import my_tool

root_agent = llm_agent.Agent(
    # ...
    tools=[web_search, my_tool],  # Add your tool here
)
```

## Development Workflow

1. **Edit your agent:** Modify `my_agent/agent.py`
2. **Test interactively:** Run `uv run adk web` and chat with your agent
3. **Check performance:** Run `uv run python evaluate.py` to see accuracy
4. **Iterate:** Improve your prompts and tools based on results

## Evaluation Options

```bash
# Evaluate all 5 questions
uv run python evaluate.py

# Test just one question (0-4)
uv run python evaluate.py --question 0

# Save results to custom file
uv run python evaluate.py --output my_results.json
```

## Project Structure

```
ML6xGDGKUL_AIAccelerate2025/
├── my_agent/              # YOUR WORKSPACE
│   ├── agent.py          # Main agent configuration (EDIT THIS)
│   ├── tools/            # Custom tools directory
│   │   └── web_search.py # Example tool (currently mock)
│   └── .env              # API keys (DO NOT COMMIT)
│
├── benchmark/            # Training data (READ ONLY)
│   ├── train.json       # 5 questions and answers
│   └── attachments/     # Files referenced by questions
│
├── utils/               # Infrastructure (READ ONLY)
│   └── server.py       # ADK server management
│
└── evaluate.py         # Evaluation script
```

## Tips for Success

1. **Start simple:** Get basic responses working before adding complexity
2. **Read the questions:** Check `benchmark/train.json` to understand what's being asked
3. **Test incrementally:** Use the web interface to test each change
4. **Use tools:** Search, calculation, and file reading are crucial for complex questions
5. **Iterate:** Improve based on evaluation results

## Troubleshooting

### "Module not found" errors
```bash
uv sync  # Reinstall dependencies
```

### "API key not found"
- Check that `my_agent/.env` exists (not `.local_env`)
- Verify your API key is correct
- Make sure the file has: `GOOGLE_API_KEY="your_key_here"`

### "Port already in use"
- Stop the running server: Look for process using port 8000
- Or use a different port (check ADK documentation)

## Resources

- **ADK Documentation:** https://googleapis.github.io/python-genai/adk/
- **ADK Samples:** https://github.com/googleapis/python-genai/tree/main/samples/adk
- **Gemini API Docs:** https://ai.google.dev/
- **Agent Design Guide:** https://ai.google.dev/gemini-api/docs/thinking-mode

## What to Focus On

For the hackathon, you need:

1. **Code:** A working agent that can answer the training questions
2. **Presentation:**
   - Section 1: Demo and insights from your agent
   - Section 2: Real-world business application

### Judging Criteria
- 40% Accuracy on evaluation dataset
- 10% Speed of responses
- 50% Quality of presentation

Good luck! 🚀
