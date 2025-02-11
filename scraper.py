import os
import openai
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# WordPress API Endpoint
WORDPRESS_API = "https://yourwebsite.com/wp-json/chatbot/v1/pages"


def fetch_page_content():
    """Fetch extracted page content from WordPress."""
    response = requests.get(WORDPRESS_API)
    if response.status_code == 200:
        return response.json()
    return None


def generate_chat_response(user_input, context):
    """Generate response using OpenAI GPT model."""
    messages = [{"role": "system", "content": "You are a helpful chatbot that answers based on website content."}]
    
    # Add page content to context
    for page in context:
        messages.append({"role": "system", "content": f"Page: {page['page_name']}\nContent: {page['content']}"})
    
    messages.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        api_key=OPENAI_API_KEY
    )

    return response["choices"][0]["message"]["content"]


@app.route("/chatbot", methods=["POST"])
def chatbot():
    """Chatbot API Endpoint."""
    data = request.json
    user_input = data.get("message", "")

    # Fetch page content
    context = fetch_page_content()
    if not context:
        return jsonify({"error": "Failed to fetch content"}), 500

    # Generate AI response
    bot_response = generate_chat_response(user_input, context)

    return jsonify({"response": bot_response})


if __name__ == "__main__":
    app.run(debug=True)
