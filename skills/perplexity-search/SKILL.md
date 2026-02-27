---
name: perplexity-search
description: AI-powered search with citations via Perplexity API. Supports basic search, conversational search, and deep research.
homepage: https://www.perplexity.ai
metadata: {"clawdbot":{"emoji":"🔍","requires":{"bins":["node"],"env":["PERPLEXITY_API_KEY"]},"primaryEnv":"PERPLEXITY_API_KEY"}}
---

# Perplexity Search

AI-powered search engine with real-time web access and source citations. Designed for research and fact-checking.

## Quick Start

```bash
# Basic search
node {baseDir}/scripts/search.mjs "latest AI news"

# Conversational search (with context)
node {baseDir}/scripts/ask.mjs "What is AIOS?" --context "previous answer about AI systems"

# Deep research (multi-round)
node {baseDir}/scripts/research.mjs "self-improving AI systems" --depth 3
```

## Commands

### 1. Basic Search
```bash
node {baseDir}/scripts/search.mjs "query" [options]
```

**Options:**
- `-n <count>`: Number of results (default: 5, max: 10)
- `--model <model>`: Model to use (default: sonar-pro)
  - `sonar-pro`: Best quality, slower
  - `sonar`: Fast, good quality
  - `sonar-reasoning`: Deep reasoning mode
- `--json`: Output JSON format

**Example:**
```bash
node {baseDir}/scripts/search.mjs "Perplexity AI funding 2026" -n 5 --model sonar-pro
```

### 2. Conversational Search
```bash
node {baseDir}/scripts/ask.mjs "question" [options]
```

**Options:**
- `--context <text>`: Previous conversation context
- `--model <model>`: Model to use
- `--json`: Output JSON format

**Example:**
```bash
node {baseDir}/scripts/ask.mjs "How does it compare to ChatGPT?" --context "Perplexity is an AI search engine"
```

### 3. Deep Research
```bash
node {baseDir}/scripts/research.mjs "topic" [options]
```

**Options:**
- `--depth <n>`: Research depth (1-5, default: 3)
- `--model <model>`: Model to use
- `--output <file>`: Save report to file

**Example:**
```bash
node {baseDir}/scripts/research.mjs "AIOS architecture patterns" --depth 3 --output report.md
```

## Models

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| `sonar-pro` | Slow | Best | Deep research, complex questions |
| `sonar` | Fast | Good | Quick searches, simple questions |
| `sonar-reasoning` | Slowest | Best | Multi-step reasoning, analysis |

## API Key

Get your API key from: https://www.perplexity.ai/settings/api

Set environment variable:
```bash
# Windows
set PERPLEXITY_API_KEY=pplx-xxxxx

# Linux/Mac
export PERPLEXITY_API_KEY=pplx-xxxxx
```

## Output Format

**Text format (default):**
```
Query: latest AI news
Model: sonar-pro
---
[Answer with citations]

Sources:
1. https://example.com/article1
2. https://example.com/article2
```

**JSON format (`--json`):**
```json
{
  "query": "latest AI news",
  "answer": "...",
  "citations": [
    {"url": "https://...", "title": "..."}
  ],
  "model": "sonar-pro"
}
```

## Integration with AIOS

### As a Skill
```python
# Direct call from AIOS
result = await run_skill("perplexity-search", {
    "query": "latest AI trends",
    "model": "sonar-pro"
})
```

### As an Agent Tool
```json
{
  "agent": "Researcher",
  "tools": ["perplexity-search"],
  "workflow": [
    "Understand research question",
    "Use perplexity-search for initial search",
    "Verify sources",
    "Generate report"
  ]
}
```

## Notes

- **Rate Limits:** Free tier has limits, Pro ($20/month) for unlimited
- **Citations:** Always included, great for fact-checking
- **Real-time:** Searches live web, not cached data
- **Context:** Conversational mode remembers previous questions

## Comparison

| Feature | Perplexity | Tavily | Google Search |
|---------|-----------|--------|---------------|
| Real-time | ✅ | ✅ | ✅ |
| Citations | ✅ Detailed | ✅ Basic | ❌ |
| Conversational | ✅ | ❌ | ❌ |
| AI-optimized | ✅ | ✅ | ❌ |
| Cost | $20/month | $0.005/search | Free |

**When to use:**
- **Perplexity:** Deep research, need citations, conversational search
- **Tavily:** Quick searches, cost-sensitive, simple queries
- **Google:** High-volume, basic search, no API needed
