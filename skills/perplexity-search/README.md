# Perplexity Search - Quick Start

## 1. Get API Key (2 minutes)

1. Go to https://www.perplexity.ai/settings/api
2. Sign up (free tier available)
3. Copy your API key (starts with `pplx-`)

## 2. Set Environment Variable (30 seconds)

**Windows:**
```cmd
set PERPLEXITY_API_KEY=pplx-xxxxx
```

**Linux/Mac:**
```bash
export PERPLEXITY_API_KEY=pplx-xxxxx
```

## 3. Test (30 seconds)

```bash
cd C:\Users\A\.openclaw\workspace\skills\perplexity-search
node test.mjs
```

Expected: `✅ All Tests Passed`

## 4. Try It

### Basic Search
```bash
node scripts/search.mjs "Perplexity AI funding 2026"
```

### Conversational Search
```bash
node scripts/ask.mjs "How does it compare to ChatGPT?" --context "Perplexity is an AI search engine"
```

### Deep Research
```bash
node scripts/research.mjs "AIOS architecture patterns" --depth 3 --output report.md
```

## 5. Use in AIOS

**Simple search:**
```
User: 搜索 Perplexity AI 最新消息
AIOS: [uses perplexity-search skill]
```

**Deep research:**
```
User: 研究 AIOS 自我改进系统
AIOS: [uses Perplexity_Researcher agent]
```

## Troubleshooting

**"API key not set"** → Check step 2
**"401 error"** → Invalid API key, get a new one
**"429 error"** → Rate limit, wait or upgrade to Pro

## Next Steps

- Read `SKILL.md` for full documentation
- Read `INTEGRATION.md` for AIOS integration details
- Try different models: `--model sonar` (fast) or `--model sonar-pro` (best)

---

**Total setup time:** ~3 minutes
**Status:** Ready to use! 🚀
