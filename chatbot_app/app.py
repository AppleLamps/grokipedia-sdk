"""Flask backend for the chatbot application"""

import os
import sys
import re
import json
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Add parent directory to path to import grokipedia_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'grokipedia-sdk'))

try:
    from grokipedia_sdk import Client, ArticleNotFound
except ImportError:
    print("Warning: Could not import grokipedia_sdk. Make sure it's installed.")
    Client = None
    ArticleNotFound = None

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not found in environment variables")

# OpenRouter API endpoint
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# System prompt that instructs the LLM to use Grokipedia when appropriate
SYSTEM_PROMPT = """You are a helpful AI assistant with access to Grokipedia, a knowledge base.

When answering questions, analyze if the information might be available in Grokipedia. If so, output a special marker in this format:
[USE_GROKIPEDIA: <article_slug_or_search_term>]

For example:
- If someone asks about Joe Biden: [USE_GROKIPEDIA: Joe_Biden]
- If someone asks about Tesla: [USE_GROKIPEDIA: Tesla]
- If you're unsure of the exact slug, use a search term: [USE_GROKIPEDIA: artificial intelligence]

If the information doesn't need Grokipedia or you're not sure, respond normally without the marker.

Always provide helpful responses and use Grokipedia to enhance your answers when appropriate."""


def call_openrouter(messages):
    """Call OpenRouter API with the given messages"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Chatbot App"
    }
    
    payload = {
        "model": "x-ai/grok-4-fast",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter: {e}")
        return None


def extract_grokipedia_marker(text):
    """Extract Grokipedia marker from text"""
    pattern = r'\[USE_GROKIPEDIA:\s*([^\]]+)\]'
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None


def fetch_grokipedia_info(search_term):
    """Fetch information from Grokipedia using the SDK"""
    if not Client:
        print("Grokipedia SDK not available")
        return None
    
    try:
        client = Client()
        
        # Try to get summary of the article
        # Handle both slugs and search terms
        slug = search_term.replace(' ', '_')
        
        try:
            summary = client.get_summary(slug)
            client.close()
            
            # Return structured info
            return {
                "title": summary.title,
                "summary": summary.summary,
                "url": summary.url,
                "table_of_contents": summary.table_of_contents[:5]  # First 5 sections
            }
        except ArticleNotFound:
            client.close()
            print(f"Article not found in Grokipedia: {slug}")
            return None
        except Exception as e:
            client.close()
            print(f"Error fetching Grokipedia info for '{slug}': {e}")
            return None
    except Exception as e:
        print(f"Error initializing Grokipedia client: {e}")
        return None


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Handle incoming chat messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Prepare messages for the LLM
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenRouter API
        openrouter_response = call_openrouter(messages)
        
        if not openrouter_response:
            return jsonify({'error': 'Failed to get response from OpenRouter'}), 500
        
        # Extract LLM response
        llm_message = openrouter_response['choices'][0]['message']['content']
        
        # Check if LLM wants to use Grokipedia
        grokipedia_term = extract_grokipedia_marker(llm_message)
        
        # Remove the marker from the response
        llm_message_clean = re.sub(r'\[USE_GROKIPEDIA:[^\]]+\]', '', llm_message).strip()
        
        # Fetch Grokipedia info if needed
        grokipedia_info = None
        if grokipedia_term:
            grokipedia_info = fetch_grokipedia_info(grokipedia_term)
        
        # Combine responses
        if grokipedia_info:
            combined_response = (
                f"{llm_message_clean}\n\n"
                f"📚 **From Grokipedia:**\n"
                f"**{grokipedia_info['title']}**\n\n"
                f"{grokipedia_info['summary']}\n\n"
                f"**Sections:** {', '.join(grokipedia_info['table_of_contents'])}\n\n"
                f"Learn more: {grokipedia_info['url']}"
            )
        else:
            combined_response = llm_message_clean
        
        return jsonify({
            'response': combined_response,
            'grokipedia_used': grokipedia_info is not None
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

