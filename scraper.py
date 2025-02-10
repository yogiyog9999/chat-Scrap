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
# Predefined responses for specific keywords
KEYWORD_RESPONSES = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! How can I help you?",
    "hey": "Hey! What can I do for you?",
    "thank you": "You're welcome! Let me know if there's anything else I can help with.",
    "bye": "Goodbye! Have a great day!"
}

# Function to fetch chatbox settings from API
def fetch_chatbox_settings():
    api_url = "https://wallingford.devstage24x7.com/wp-json/chatbox/v1/settings"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching chatbox settings: {str(e)}"}

# Function to fetch stored page content from the API
def fetch_stored_page_content():
    api_url = "https://wallingford.devstage24x7.com/wp-json/chatbot/v1/pages?jkjk"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching stored pages: {str(e)}"}

# Function to generate a refined prompt using JSON content
def generate_prompt(user_input, json_content):
    if "error" in json_content or not json_content:
        return f"User query: {user_input}\n\nIt seems I couldn't find the specific information you're looking for. Please visit our contact page for more details."
    
    return (
        f"Here is some content from our website (structured in JSON format):\n{json.dumps(json_content, indent=2)}\n\n"
        f"User query: {user_input}\n\n"
        "Please respond as a friendly, knowledgeable assistant for Wallingford."
    )

# Function to interact with ChatGPT
def ask_chatgpt(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a friendly and concise assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"Error communicating with ChatGPT: {str(e)}"

# Flask route for chatbot
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    # Fetch dynamic settings
    settings = fetch_chatbox_settings()
    if "error" in settings:
        return jsonify({"error": settings["error"]}), 500

    # Check if user input matches predefined responses
    for keyword, response in KEYWORD_RESPONSES.items():
        if keyword.lower() in user_input.lower():
            return jsonify({"response": response})

    # Fetch stored page content
    stored_pages = fetch_stored_page_content()
    if "error" in stored_pages:
        return jsonify({"error": stored_pages["error"]}), 500

    # Generate prompt and get response from ChatGPT
    prompt = generate_prompt(user_input, stored_pages)
    response = ask_chatgpt(prompt)
    return jsonify({"response": response})
     
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
        refined_response = refine_response(user_response)
        return jsonify({"response": refined_response})

    return jsonify({"error": "Invalid feedback value. Please use 'thumbs_up' or 'thumbs_down'."}), 400

# Function to refine the response
def refine_response(original_response):
    try:
        prompt = f"Refine the following response to make it more clear and helpful: {original_response}"
        return ask_chatgpt(prompt)
    except Exception as e:
        return f"Error refining response: {str(e)}"

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
