# Grokipedia Chatbot

A web-based chatbot powered by Grok-4-Fast (via OpenRouter) with Grokipedia integration.

## Features

- 🤖 Powered by Grok-4-Fast model via OpenRouter API
- 📚 Automatic Grokipedia integration when appropriate
- 💬 Real-time chat interface
- 🎨 Modern, responsive UI

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your OpenRouter API key:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_api_key_here
```

You can get an API key from [OpenRouter](https://openrouter.ai/keys).

### 3. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## How It Works

1. **User sends a message** through the web interface
2. **Flask backend** receives the message and prepares it for the LLM
3. **OpenRouter API** is called with the message using the Grok-4-Fast model
4. **LLM analyzes** the request and may indicate when Grokipedia information would be useful
5. **Grokipedia SDK** fetches relevant information when triggered
6. **Combined response** is sent back to the user

## Grokipedia Integration

The chatbot automatically fetches information from Grokipedia when the LLM identifies that it would be helpful. The LLM outputs a special marker like:

```
[USE_GROKIPEDIA: article_slug]
```

The backend then:
- Extracts the article slug from the marker
- Uses the Grokipedia SDK to fetch article summary
- Combines the LLM response with Grokipedia information
- Returns enriched content to the user

## Architecture

```
chatbot_app/
├── app.py              # Flask backend
├── templates/
│   └── index.html      # Frontend HTML
├── static/
│   └── script.js       # Frontend JavaScript
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
└── README.md          # This file
```

## Notes

- The application requires the `grokipedia-sdk` to be accessible from the parent directory
- Make sure the OpenRouter API key is set in the `.env` file
- The chatbot is configured to use the `x-ai/grok-4-fast` model

