import os
import openai
from flask import Flask, request, jsonify, session
from langdetect import detect
from textblob import TextBlob
from googletrans import Translator
from dotenv import load_dotenv
import logging
import requests
from bs4 import BeautifulSoup
import json
from flask_cors import CORS

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.INFO, filename="chatbot.log", format="%(asctime)s - %(message)s")

# Default language for responses
DEFAULT_LANGUAGE = "en"

# Chat Memory
SESSION_MEMORY_LIMIT = 5  # Store the last 5 interactions

# Translator setup
translator = Translator()

# Predefined responses for specific keywords
KEYWORD_RESPONSES = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! How can I help you?",
    "address": "Our office address is 123 Wallingford St, Wallingford, USA.",
    "contact": "You can contact us via email at support@wallingford.com or call us at +123456789.",
    "email": "You can reach us at support@wallingford.com.",
    "phone": "Our contact number is +123456789.",
    "call": "Please feel free to give us a call at +123456789."
}

# Helper function: Translate text
def translate_text(text, target_lang):
    return translator.translate(text, dest=target_lang).text

# Helper function: Analyze sentiment
def analyze_sentiment(user_input):
    sentiment = TextBlob(user_input).sentiment.polarity
    if sentiment > 0.1:
        return "positive"
    elif sentiment < -0.1:
        return "negative"
    else:
        return "neutral"

# Function to fetch chatbox settings from API
def fetch_chatbox_settings():
    try:
        api_url = "https://wallingford.devstage24x7.com/wp-json/chatbox/v1/settings"
        response = requests.get(api_url)

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to fetch chatbox settings: {response.status_code}"}
    except Exception as e:
        return {"error": f"Error fetching chatbox settings: {str(e)}"}

# Update the predefined responses with dynamic values
def update_keyword_responses(settings):
    global KEYWORD_RESPONSES
    if "chatbox_address" in settings:
        KEYWORD_RESPONSES["address"] = f"Our office address is {settings['chatbox_address']}."
    if "chatbox_contact" in settings:
        KEYWORD_RESPONSES["contact"] = f"You can contact us via {settings['chatbox_contact']}."
    if "chatbox_email" in settings:
        KEYWORD_RESPONSES["email"] = f"You can reach us at {settings['chatbox_email']}."
    if "chatbox_hours" in settings:
        KEYWORD_RESPONSES["call"] = f"Our operational hours are {settings['chatbox_hours']}."

# Function to fetch specific content from a URL
def fetch_website_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract headers and paragraphs
        content = {
            "h1": [header.get_text(strip=True) for header in soup.find_all('h1')],
            "h2": [header.get_text(strip=True) for header in soup.find_all('h2')],
            "p": [para.get_text(strip=True) for para in soup.find_all('p')]
        }
        return json.dumps(content)
    except requests.RequestException as e:
        return json.dumps({"error": f"Error fetching content: {str(e)}"})

# Function to generate a refined prompt using JSON content
def generate_prompt(user_input, json_content):
    return (
        f"Here is some content from our website (structured in JSON format):\n{json_content}\n\n"
        f"User query: {user_input}\n\n"
        "Please respond as a knowledgeable support assistant based on the above content."
    )

# Function to interact with ChatGPT
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error communicating with ChatGPT: {str(e)}"

# Flask route for chatbot
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    user_language = detect(user_input)

    # Translate input to English for processing
    if user_language != DEFAULT_LANGUAGE:
        user_input_translated = translate_text(user_input, DEFAULT_LANGUAGE)
    else:
        user_input_translated = user_input

    # Sentiment Analysis
    sentiment = analyze_sentiment(user_input_translated)

    # Fetch dynamic settings and update keyword responses
    settings = fetch_chatbox_settings()
    if "error" in settings:
        return jsonify({"error": settings["error"]}), 500
    update_keyword_responses(settings)

    # Check if the user input matches any predefined keywords
    for keyword, response in KEYWORD_RESPONSES.items():
        if keyword.lower() in user_input.lower():
            return jsonify({"response": response, "sentiment": sentiment})

    # Create a refined prompt and get GPT response
    prompt = generate_prompt(user_input_translated, json.dumps(settings))
    bot_response = ask_chatgpt(prompt)

    # Translate response back to user's language
    if user_language != DEFAULT_LANGUAGE:
        bot_response = translate_text(bot_response, user_language)

    # Logging response
    logging.info(f"Bot response: {bot_response}")

    return jsonify({"response": bot_response, "sentiment": sentiment})

# Flask route for feedback
@app.route('/feedback', methods=['POST'])
def feedback():
    user_feedback = request.json.get("feedback")
    user_response = request.json.get("response")

    if not user_feedback or not user_response:
        return jsonify({"error": "Feedback and response are required"}), 400

    if user_feedback == "thumbs_up":
        return jsonify({"response": "Thank you for your feedback! Glad you liked it!"})

    if user_feedback == "thumbs_down":
        refined_response = ask_chatgpt(f"Refine this response to be more helpful: {user_response}")
        return jsonify({"response": "Thank you for your feedback. Here's a refined response:", "refined_response": refined_response})

    return jsonify({"error": "Invalid feedback value. Please use 'thumbs_up' or 'thumbs_down'."}), 400

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
