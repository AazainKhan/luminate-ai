# LLM Configuration Guide

## Overview

Luminate AI uses a centralized LLM configuration system that supports multiple AI providers. You can easily switch between providers by updating your `.env` file - no code changes required.

## Supported Providers

| Provider | Models | Cost | Speed | Notes |
|----------|--------|------|-------|-------|
| **Google Gemini** | gemini-2.0-flash, gemini-1.5-pro | Free tier available | Very fast | ✅ Recommended |
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | Paid | Fast | Requires API key |
| **Anthropic** | claude-3-5-sonnet, claude-3-opus | Paid | Medium | Excellent for reasoning |
| **Ollama** | llama3.2, mistral, mixtral | Free | Slow (local) | Privacy-first, runs locally |
| **Azure OpenAI** | gpt-4o, gpt-4-turbo | Paid | Fast | Enterprise option |

## Quick Setup

### 1. Choose Your Provider

Edit `.env` in the project root:

```bash
# Set your provider (gemini, openai, anthropic, ollama, azure)
LLM_PROVIDER=gemini

# Set your model
MODEL_NAME=gemini-2.0-flash

# Add your API key
GOOGLE_API_KEY=your_api_key_here
```

### 2. Get API Keys

#### Google Gemini (Recommended - Free Tier)
1. Visit https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy to `GOOGLE_API_KEY` in `.env`

#### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to `OPENAI_API_KEY` in `.env`

#### Anthropic Claude
1. Visit https://console.anthropic.com/settings/keys
2. Create API key
3. Copy to `ANTHROPIC_API_KEY` in `.env`

#### Ollama (Local - No API Key)
1. Install: `brew install ollama` (macOS)
2. Pull model: `ollama pull llama3.2`
3. Set `LLM_PROVIDER=ollama` in `.env`
4. No API key needed!

## Model Recommendations

### For Navigate Mode (Fast Queries)
- **Best**: `gemini-2.0-flash` - Extremely fast, free tier
- **Alternative**: `gpt-4o-mini` - Fast, affordable
- **Local**: `llama3.2` - Free, privacy-first

### For Educate Mode (Complex Tutoring)
- **Best**: `gemini-1.5-pro` - Excellent reasoning
- **Alternative**: `claude-3-5-sonnet-20241022` - Superior pedagogy
- **Local**: `mixtral` - Good for complex tasks

## Configuration Examples

### Example 1: Google Gemini (Default)
```bash
LLM_PROVIDER=gemini
MODEL_NAME=gemini-2.0-flash
GOOGLE_API_KEY=AIzaSy...
```

### Example 2: OpenAI GPT-4
```bash
LLM_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=sk-proj-...
```

### Example 3: Local with Ollama
```bash
LLM_PROVIDER=ollama
MODEL_NAME=llama3.2
# No API key needed!
```

### Example 4: Anthropic Claude
```bash
LLM_PROVIDER=anthropic
MODEL_NAME=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

## Testing Your Configuration

Run the configuration test:

```bash
python development/backend/langgraph/llm_config.py
```

You should see:
```
✓ LLM initialized successfully
✓ All tests passed!
```

## Switching Providers

To switch providers:

1. Update `.env`:
   ```bash
   LLM_PROVIDER=openai  # Change to your new provider
   MODEL_NAME=gpt-4o-mini
   OPENAI_API_KEY=your_key
   ```

2. Restart services:
   ```bash
   # Kill existing FastAPI server
   pkill -f "python main.py"
   
   # Restart
   cd development/backend/fastapi_service
   source ../../../.venv/bin/activate
   python main.py
   ```

3. Test:
   ```bash
   python development/tests/test_langgraph_navigate.py
   ```

## Cost Optimization

### Free Tier Options
1. **Gemini**: 1,500 requests/day (gemini-2.0-flash)
2. **Ollama**: Unlimited (runs locally)

### Paid Options (Approximate)
- **GPT-4o-mini**: ~$0.15 per 1M input tokens
- **GPT-4o**: ~$5 per 1M input tokens
- **Claude 3.5 Sonnet**: ~$3 per 1M input tokens

### Recommendations
- **Development**: Use `gemini-2.0-flash` (free)
- **Production**: Use `gpt-4o-mini` or `gemini-2.0-flash`
- **Privacy-critical**: Use `ollama` with `llama3.2`

## Troubleshooting

### Error: "API key not found"
- Check `.env` file exists in project root
- Verify correct key name (`GOOGLE_API_KEY`, `OPENAI_API_KEY`, etc.)
- Ensure no spaces around `=` in `.env`

### Error: "Rate limit exceeded"
- Switch to different provider temporarily
- Wait for rate limit reset (usually 1 minute)
- Upgrade to paid tier

### Error: "Model not found"
- Check model name spelling in `MODEL_NAME`
- Verify model is available for your provider
- See "Supported Models" section

## Advanced Configuration

### Custom Temperature
Agents automatically set appropriate temperatures:
- Query Understanding: 0.3 (balanced)
- Retrieval: 0.1 (focused)
- Formatting: 0.2 (structured)

To override, edit `development/backend/langgraph/llm_config.py`

### Max Tokens
Set via `max_tokens` parameter:
```python
llm = get_llm(temperature=0.3, max_tokens=2000)
```

### Provider-Specific Options
```python
# Gemini with safety settings
llm = get_llm(
    temperature=0.3,
    safety_settings={
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE"
    }
)
```

## Security Best Practices

1. **Never commit `.env` to git** (already in `.gitignore`)
2. **Rotate API keys regularly** (every 90 days)
3. **Use environment-specific keys** (dev vs prod)
4. **Monitor usage** to detect anomalies
5. **Use Ollama** for sensitive data

## Support

Having issues? Check:
1. API key is valid and active
2. Provider has available quota
3. Internet connection (except Ollama)
4. Latest LangChain packages installed

For provider-specific issues:
- **Gemini**: https://ai.google.dev/docs
- **OpenAI**: https://platform.openai.com/docs
- **Anthropic**: https://docs.anthropic.com
- **Ollama**: https://ollama.ai/docs
