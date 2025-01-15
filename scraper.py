import os
import openai
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask app setup
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Predefined responses for specific keywords
KEYWORD_RESPONSES = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! How can I help you?",
    # Additional keywords...
}

def fetch_chatbox_settings():
    try:
        api_url = "https://wallingford.devstage24x7.com/wp-json/chatbox/v1/settings"
        logging.debug(f"Fetching chatbox settings from {api_url}")
        response = requests.get(api_url)
        response.raise_for_status()
        logging.debug(f"Settings fetched successfully: {response.json()}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching chatbox settings: {e}")
        return {"error": f"Failed to fetch chatbox settings: {str(e)}"}

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    logging.debug(f"Received user input: {user_input}")

    if not user_input:
        logging.warning("No message provided in request.")
        return jsonify({"error": "Message is required"}), 400

    # Fetch and log settings
    settings = fetch_chatbox_settings()
    if "error" in settings:
        logging.error(f"Error in settings: {settings['error']}")
        return jsonify({"error": settings["error"]}), 500

    # Update responses and log changes
    logging.debug(f"Updating responses with settings: {settings}")
    update_keyword_responses(settings)

    # Check predefined keywords
    for keyword, response in KEYWORD_RESPONSES.items():
        if keyword.lower() in user_input.lower():
            logging.info(f"Matched keyword: {keyword} | Responding with: {response}")
            return jsonify({"response": response})

    # Fetch selected pages and log details
    selected_pages = get_selected_pages()
    if "error" in selected_pages:
        logging.error(f"Error fetching selected pages: {selected_pages['error']}")
        return jsonify({"error": selected_pages["error"]}), 500

    # Fetch content and log errors
    content_from_pages = {}
    for page_name, page_url in selected_pages.items():
        logging.debug(f"Fetching content from {page_name}: {page_url}")
        json_content = fetch_website_content(page_url)
        content = json.loads(json_content)

        if "error" in content:
            logging.error(f"Error in content from {page_name}: {content['error']}")
            return jsonify({"error": content["error"]}), 500

        content_from_pages[page_name] = content

    combined_content = json.dumps(content_from_pages)
    logging.debug(f"Combined content for prompt: {combined_content}")

    # Generate and log the prompt
    prompt = generate_prompt(user_input, combined_content)
    logging.debug(f"Generated prompt for GPT: {prompt}")

    # Get and log GPT response
    response = ask_chatgpt(prompt)
    logging.info(f"GPT response: {response}")
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
