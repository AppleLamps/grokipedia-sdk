# Usage Guide

## Quick Start

### 1. Install Dependencies

**Windows:**
```bash
cd chatbot_app
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
cd chatbot_app
pip install -r requirements.txt
```

Or use the setup script:
- Windows: Run `setup.bat`
- Linux/Mac: Run `bash setup.sh`

### 2. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx
```

**Get your API key:** Visit [OpenRouter Keys](https://openrouter.ai/keys)

### 3. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 4. Use the Chatbot

1. Open your browser and go to `http://localhost:5000`
2. Type a message in the input field
3. Press Enter or click Send
4. The chatbot will respond using Grok-4-Fast
5. When appropriate, it will automatically fetch information from Grokipedia

## Example Questions

Try asking these questions to see the Grokipedia integration in action:

- "Tell me about Joe Biden"
- "What do you know about Tesla?"
- "Who is Elon Musk?"
- "Tell me about artificial intelligence"

## How It Works

### Architecture Flow

```
User Message
    ↓
Flask Backend (app.py)
    ↓
OpenRouter API (Grok-4-Fast)
    ↓
LLM Analysis & Response
    ↓
Check for [USE_GROKIPEDIA: ...] marker
    ↓
If marker found → Grokipedia SDK fetches article
    ↓
Combine LLM response + Grokipedia info
    ↓
Send to user
```

### Key Components

1. **Frontend** (`templates/index.html`, `static/script.js`)
   - Modern chat interface
   - Real-time message updates
   - Loading indicators

2. **Backend** (`app.py`)
   - Flask web server
   - OpenRouter API integration
   - Grokipedia SDK integration
   - Message handling and processing

3. **Grokipedia SDK** (`../grokipedia-sdk/`)
   - Fetches article summaries
   - Handles errors gracefully
   - Returns structured data

## Troubleshooting

### "OPENROUTER_API_KEY not found"
- Make sure you created `.env` file
- Check that the API key is correctly set
- Restart the application after creating `.env`

### "Could not import grokipedia_sdk"
- Ensure the `grokipedia-sdk` directory exists in the parent folder
- The SDK should be accessible at `../grokipedia-sdk`

### Chatbot not responding
- Check console for error messages
- Verify your OpenRouter API key is valid
- Ensure you have internet connectivity

### Grokipedia not fetching
- Check if the article exists on Grokipedia
- Look for error messages in the console
- The LLM decides when to use Grokipedia automatically

## Features

✅ **Real-time chat interface**
✅ **Powered by Grok-4-Fast**
✅ **Automatic Grokipedia integration**
✅ **Modern, responsive UI**
✅ **Error handling**
✅ **Loading indicators**
✅ **Conversation history**

## API Reference

### POST /chat

Send a message to the chatbot.

**Request:**
```json
{
  "message": "Your message here",
  "history": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

**Response:**
```json
{
  "response": "Chatbot response text",
  "grokipedia_used": true
}
```

## Configuration

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)

### Model Configuration

The chatbot uses `x-ai/grok-4-fast` model with these settings:
- Temperature: 0.7
- Max tokens: 1000

You can modify these in `app.py` if needed.

## Security Notes

- Never commit your `.env` file
- Keep your API key secure
- The `.gitignore` is configured to exclude sensitive files

