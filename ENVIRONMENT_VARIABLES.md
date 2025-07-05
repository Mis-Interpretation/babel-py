# Environment Variables Configuration

This document explains all the configurable environment variables for the FastAPI backend.

## Required Variables

### OpenAI Configuration
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

## Optional Variables

### Server Configuration
```env
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
```

### Chat Configuration
```env
MAX_TOKENS=6000
MAX_RECENT_MESSAGES=22
```

## Variable Details

### `MAX_TOKENS`
- **Purpose**: Maximum tokens for OpenAI responses
- **Default**: 6000
- **Range**: 1 - 16,000 (for GPT-4o-mini)
- **Recommendations**:
  - 4000-6000: Standard conversations
  - 6000-8000: Detailed analysis or with images
  - 8000+: Complex tasks requiring long responses

### `MAX_RECENT_MESSAGES`
- **Purpose**: Maximum number of recent messages to keep in chat history
- **Default**: 22
- **Note**: Counts ALL messages (user + assistant + system)
- **Recommendations**:
  - 10-20: Short conversations, limited memory
  - 20-40: Standard conversations with good context
  - 40+: Long conversations with full context

## How to Use

1. Create a `.env` file in your project root
2. Add the variables you want to customize
3. Restart your application

### Example `.env` file:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
MAX_TOKENS=8000
MAX_RECENT_MESSAGES=30
SERVER_PORT=8080
```

## Notes
- If a variable is not set, the default value will be used
- Invalid values (non-numeric for numeric fields) will fallback to defaults
- Changes require application restart to take effect
- Environment variables override any hardcoded values 