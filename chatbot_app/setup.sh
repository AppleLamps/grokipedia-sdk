#!/bin/bash

echo "========================================"
echo "Grokipedia Chatbot Setup"
echo "========================================"
echo ""

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "========================================"
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env"
echo "2. Add your OpenRouter API key to .env"
echo "3. Run: python app.py"
echo "========================================"

